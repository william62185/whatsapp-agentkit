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


def _obtener_cliente() -> AsyncAnthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY no está configurada en las variables de entorno")
    return AsyncAnthropic(api_key=api_key)


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
        client = _obtener_cliente()
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


_PALABRAS_UPDATE = [
    # agregar
    "agrega", "agregar", "agréga", "añade", "añadir", "anade", "anadir",
    "adiciona", "adicionar", "incluye", "incluir", "suma", "sumar",
    "tambien", "también", "ademas", "además", "mas ", "más ",
    # quitar
    "quita", "quitar", "elimina", "eliminar", "borra", "borrar",
    "saca", "sacar", "remueve", "remover", "descarta", "descartar",
    # modificar
    "cambia", "cambiar", "modifica", "modificar", "actualiza", "actualizar",
    "corrige", "corregir", "en vez", "en lugar", "reemplaza", "reemplazar",
    # cantidad
    "aumenta", "aumentar", "reduce", "reducir", "menos ", "sube ", "baja ",
    "falta", "faltan",
]


def _ultimo_pedido(historial: list[dict]) -> str | None:
    """Extrae el último pedido generado del historial de conversación."""
    for msg in reversed(historial):
        if msg["role"] == "assistant" and "Pedido de Insumos" in msg["content"]:
            return msg["content"]
    return None


def _es_solicitud_update(mensaje: str) -> bool:
    """Detecta si el mensaje es una solicitud de modificación de pedido."""
    texto = mensaje.lower()
    return any(p in texto for p in _PALABRAS_UPDATE)


async def actualizar_pedido(mensaje: str, pedido_anterior: str) -> str:
    """
    Modifica el pedido anterior según la instrucción del usuario.
    Devuelve el pedido completo actualizado con el mismo formato.
    """
    hoy = date.today().strftime("%d/%m/%Y")
    prompt = f"""Tienes este pedido de insumos:

{pedido_anterior}

El usuario pide: "{mensaje}"

Aplica el cambio y devuelve el pedido COMPLETO con EXACTAMENTE el mismo formato.
Reglas:
- Mantén TODOS los items que no se mencionan
- Si dice "agrega" o "también" → añade el item nuevo
- Si dice "quita" o "elimina" → elimina ese item
- Si dice "cambia X por Y" o "en vez de X" → modifica el item
- Renumera los items si es necesario
- Mantén la misma fecha ({hoy})
"""
    try:
        client = _obtener_cliente()
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"Error Claude API (actualizar pedido): {e}")
        config = _cargar_prompts()
        return config.get("error_message", "Tuve un problema tecnico. Intenta de nuevo en un momento.")


async def generar_respuesta(mensaje: str, historial: list[dict]) -> str:
    """Genera respuesta para mensajes de texto normales."""
    config = _cargar_prompts()

    if not mensaje or len(mensaje.strip()) < 2:
        return config.get("fallback_message", "No entendi tu mensaje. Puedes repetirlo?")

    system_prompt = config.get("system_prompt", "Eres JuiceBot, asistente amigable del area de jugos.")

    mensajes = [{"role": m["role"], "content": m["content"]} for m in historial]
    mensajes.append({"role": "user", "content": mensaje})

    try:
        client = _obtener_cliente()
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
