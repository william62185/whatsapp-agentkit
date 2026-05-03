# agent/providers/base.py — Clase base para proveedores de WhatsApp
# Generado por AgentKit

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from fastapi import Request


@dataclass
class MensajeEntrante:
    """Mensaje normalizado — mismo formato sin importar el proveedor."""
    telefono: str       # Numero del remitente
    texto: str          # Contenido del mensaje (vacio si es audio)
    mensaje_id: str     # ID unico del mensaje
    es_propio: bool     # True si lo envio el agente (se ignora)
    es_audio: bool = False      # True si es una nota de voz
    audio_url: str = ""         # URL para descargar el audio
    audio_mime: str = "audio/ogg"  # Tipo MIME del audio


class ProveedorWhatsApp(ABC):
    """Interfaz que cada proveedor de WhatsApp debe implementar."""

    @abstractmethod
    async def parsear_webhook(self, request: Request) -> list[MensajeEntrante]:
        """Extrae y normaliza mensajes del payload del webhook."""
        ...

    @abstractmethod
    async def enviar_mensaje(self, telefono: str, mensaje: str) -> bool:
        """Envia un mensaje de texto. Retorna True si fue exitoso."""
        ...

    async def validar_webhook(self, request: Request) -> dict | int | None:
        """Verificacion GET del webhook (solo Meta la requiere). Retorna respuesta o None."""
        return None
