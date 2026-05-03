# agent/providers/whapi.py — Adaptador para Whapi.cloud
# Generado por AgentKit

import os
import logging
import httpx
from fastapi import Request
from agent.providers.base import ProveedorWhatsApp, MensajeEntrante

logger = logging.getLogger("agentkit")


class ProveedorWhapi(ProveedorWhatsApp):
    """Proveedor de WhatsApp usando Whapi.cloud."""

    def __init__(self):
        self.token = os.getenv("WHAPI_TOKEN")
        self.url_envio = "https://gate.whapi.cloud/messages/text"

    async def parsear_webhook(self, request: Request) -> list[MensajeEntrante]:
        """Parsea el payload de Whapi.cloud, incluyendo mensajes de audio."""
        body = await request.json()
        logger.info(f"Whapi payload keys: {list(body.keys())}")
        logger.info(f"Whapi payload: {str(body)[:500]}")
        mensajes = []

        for msg in body.get("messages", []):
            tipo = msg.get("type", "text")
            telefono = msg.get("chat_id", "")
            mensaje_id = msg.get("id", "")
            es_propio = msg.get("from_me", False)

            # Nota de voz: Whapi puede enviar tipo 'voice', 'audio' o 'ptt'
            if tipo in ("audio", "ptt", "voice"):
                datos_audio = msg.get(tipo, {})
                audio_id = datos_audio.get("id", "")
                # Whapi puede incluir 'link' directo o solo el 'id' del media
                audio_url = datos_audio.get("link") or (
                    f"https://gate.whapi.cloud/whatsapp/media/{audio_id}" if audio_id else ""
                )
                mensajes.append(MensajeEntrante(
                    telefono=telefono,
                    texto="",
                    mensaje_id=mensaje_id,
                    es_propio=es_propio,
                    es_audio=True,
                    audio_url=audio_url,
                    audio_mime=datos_audio.get("mime_type", "audio/ogg"),
                ))

            elif tipo == "text":
                mensajes.append(MensajeEntrante(
                    telefono=telefono,
                    texto=msg.get("text", {}).get("body", ""),
                    mensaje_id=mensaje_id,
                    es_propio=es_propio,
                ))

        return mensajes

    async def enviar_mensaje(self, telefono: str, mensaje: str) -> bool:
        """Envia mensaje via Whapi.cloud."""
        if not self.token:
            logger.warning("WHAPI_TOKEN no configurado — mensaje no enviado")
            return False
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient() as client:
            r = await client.post(
                self.url_envio,
                json={"to": telefono, "body": mensaje},
                headers=headers,
            )
            if r.status_code != 200:
                logger.error(f"Error Whapi: {r.status_code} — {r.text}")
            return r.status_code == 200
