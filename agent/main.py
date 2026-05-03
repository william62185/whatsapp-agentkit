# agent/main.py — Servidor FastAPI + Webhook de WhatsApp
# Generado por AgentKit

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

from agent.brain import generar_respuesta, generar_pedido_desde_transcripcion
from agent.memory import inicializar_db, guardar_mensaje, obtener_historial
from agent.transcriber import descargar_audio, transcribir_audio
from agent.providers import obtener_proveedor

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
log_level = logging.DEBUG if ENVIRONMENT == "development" else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger("agentkit")

proveedor = obtener_proveedor()
PORT = int(os.getenv("PORT", 8000))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await inicializar_db()
    logger.info("Base de datos inicializada")
    logger.info(f"Servidor JuiceBot corriendo en puerto {PORT}")
    logger.info(f"Proveedor de WhatsApp: {proveedor.__class__.__name__}")
    logger.info(f"ANTHROPIC_API_KEY: {'OK' if os.getenv('ANTHROPIC_API_KEY') else 'FALTA'}")
    logger.info(f"WHAPI_TOKEN: {'OK' if os.getenv('WHAPI_TOKEN') else 'FALTA'}")
    logger.info(f"GROQ_API_KEY: {'OK' if os.getenv('GROQ_API_KEY') else 'FALTA'}")
    yield


app = FastAPI(
    title="JuiceBot — Fresh to Go Foods",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def health_check():
    return {"status": "ok", "service": "juicebot", "negocio": "Fresh to Go Foods"}


@app.get("/webhook")
async def webhook_verificacion(request: Request):
    resultado = await proveedor.validar_webhook(request)
    if resultado is not None:
        return PlainTextResponse(str(resultado))
    return {"status": "ok"}


@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    Recibe mensajes de WhatsApp.
    - Si es audio: transcribe con Groq Whisper y genera el pedido formateado con Claude.
    - Si es texto: responde como asistente conversacional.
    """
    try:
        mensajes = await proveedor.parsear_webhook(request)

        for msg in mensajes:
            # Ignorar mensajes propios
            if msg.es_propio:
                continue

            # Procesar nota de voz
            if msg.es_audio:
                if not msg.audio_url:
                    logger.warning(f"Audio sin URL de {msg.telefono}")
                    continue

                logger.info(f"Audio recibido de {msg.telefono}")
                await proveedor.enviar_mensaje(msg.telefono, "🎤 Procesando tu nota de voz...")

                try:
                    # Descargar y transcribir
                    token = os.getenv("WHAPI_TOKEN", "")
                    audio_bytes = await descargar_audio(msg.audio_url, token)
                    transcripcion = await transcribir_audio(audio_bytes, msg.audio_mime)
                    logger.info(f"Transcripcion: {transcripcion[:100]}")

                    # Generar pedido formateado
                    pedido = await generar_pedido_desde_transcripcion(transcripcion)

                    # Guardar en historial
                    await guardar_mensaje(msg.telefono, "user", f"[AUDIO] {transcripcion}")
                    await guardar_mensaje(msg.telefono, "assistant", pedido)

                    # Enviar pedido al usuario
                    await proveedor.enviar_mensaje(msg.telefono, pedido)
                    logger.info(f"Pedido enviado a {msg.telefono}")

                except Exception as e:
                    logger.error(f"Error procesando audio: {e}")
                    await proveedor.enviar_mensaje(
                        msg.telefono,
                        "❌ No pude procesar el audio. ¿Puedes intentarlo de nuevo?"
                    )

            # Procesar mensaje de texto
            elif msg.texto:
                logger.info(f"Mensaje de {msg.telefono}: {msg.texto}")
                historial = await obtener_historial(msg.telefono)
                respuesta = await generar_respuesta(msg.texto, historial)
                await guardar_mensaje(msg.telefono, "user", msg.texto)
                await guardar_mensaje(msg.telefono, "assistant", respuesta)
                await proveedor.enviar_mensaje(msg.telefono, respuesta)
                logger.info(f"Respuesta a {msg.telefono}: {respuesta}")

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error en webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
