# agent/transcriber.py — Transcripcion de audio con Groq Whisper
# Generado por AgentKit

"""
Descarga el audio desde Whapi y lo transcribe usando Groq Whisper.
Groq ofrece Whisper gratis con alta precision en espanol e ingles.
"""

import os
import io
import logging
import httpx
from groq import AsyncGroq

logger = logging.getLogger("agentkit")


def _obtener_cliente_groq() -> AsyncGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY no está configurada en las variables de entorno")
    return AsyncGroq(api_key=api_key)


def _extension_desde_mime(mime_type: str) -> str:
    """Determina la extension del archivo segun el tipo MIME."""
    mime = mime_type.lower()
    if "mp4" in mime or "m4a" in mime:
        return "m4a"
    if "mpeg" in mime or "mp3" in mime:
        return "mp3"
    if "wav" in mime:
        return "wav"
    if "webm" in mime:
        return "webm"
    return "ogg"  # formato por defecto de WhatsApp


async def descargar_audio(url: str, token: str) -> bytes:
    """Descarga el archivo de audio desde la URL de Whapi."""
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        return r.content


async def transcribir_audio(audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
    """
    Transcribe audio usando Groq Whisper large-v3.
    Soporta espanol, ingles y otros idiomas automaticamente.
    """
    extension = _extension_desde_mime(mime_type)
    nombre_archivo = f"audio.{extension}"

    try:
        cliente_groq = _obtener_cliente_groq()
        transcripcion = await cliente_groq.audio.transcriptions.create(
            file=(nombre_archivo, io.BytesIO(audio_bytes)),
            model="whisper-large-v3",
            response_format="text",
        )
        logger.info(f"Transcripcion exitosa: {str(transcripcion)[:100]}...")
        return str(transcripcion).strip()

    except Exception as e:
        logger.error(f"Error en transcripcion Groq: {e}")
        raise
