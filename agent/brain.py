# agent/brain.py — Cerebro del agente: conexion con Claude API
# Generado por AgentKit

import os
import yaml
import logging
from datetime import date
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("agentkit")

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def _cargar_prompts() -> dict:
    """Lee la configuracion de prompts.yaml."""
    try:
        with open("config/prompts.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.error("config/prompts.yaml no encontrado")
        return {}


async def generar_pedido_desde_transcripcion(transcripcion: str) -> str:
    """
    Recibe la transcripcion de un audio y genera el listado
    formateado de insumos listo para enviar por WhatsApp.
    """
    config = _cargar_prompts()
    hoy = date.today().strftime("%d/%m/%Y")

    # Construir el prompt con la transcripcion y la fecha actual
    audio_prompt_template = config.get("audio_prompt", "")
    prompt = audio_prompt_template.replace("{fecha}", hoy).replace("{transcripcion}", transcripcion).replace("{items}", "")

    # Si no hay template en el yaml, usar un prompt por defecto
    if not audio_prompt_template:
        prompt = f"""Eres JuiceBot del area de jugos de Fresh to Go Foods.
El siguiente texto es la transcripcion de una nota de voz con insumos necesarios.

Genera el pedido con EXACTAMENTE este formato:

📋 *Pedido de Insumos — Fresh to Go Foods*
📅 Fecha: {hoy}

1. [Insumo] — [cantidad] [unidad]
2. [Insumo] — [cantidad] [unidad]
...

---
_JuiceBot — Area de Jugos_ 🤖

Si no se menciona cantidad, usa "?". Unidades: kg, lb, unidades, cajas, bolsas, litros, galones.

TRANSCRIPCION:
{transcripcion}"""

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    except Exception as e:
        logger.error(f"Error Claude API (audio): {e}")
        config = _cargar_prompts()
        return config.get("error_message", "Tuve un problema generando el pedido. Intenta de nuevo.")


async def generar_respuesta(mensaje: str, historial: list[dict]) -> str:
    """Genera respuesta para mensajes de texto normales."""
    config = _cargar_prompts()

    if not mensaje or len(mensaje.strip()) < 2:
        return config.get("fallback_message", "No entendi tu mensaje. Puedes repetirlo?")

    system_prompt = config.get("system_prompt", "Eres JuiceBot, asistente amigable del area de jugos.")

    mensajes = [{"role": m["role"], "content": m["content"]} for m in historial]
    mensajes.append({"role": "user", "content": mensaje})

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=system_prompt,
            messages=mensajes
        )
        return response.content[0].text

    except Exception as e:
        logger.error(f"Error Claude API (texto): {e}")
        return config.get("error_message", "Tuve un problema tecnico. Intenta de nuevo.")
