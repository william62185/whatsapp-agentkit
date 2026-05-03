# tests/test_local.py — Simulador de chat en terminal
# Generado por AgentKit

"""
Prueba JuiceBot sin necesitar WhatsApp.

Modos de prueba:
  - Escribe texto normal para probar el chat
  - Escribe '/audio Tu texto aqui' para simular una nota de voz
  - Escribe 'limpiar' para borrar el historial
  - Escribe 'salir' para terminar
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.brain import generar_respuesta, generar_pedido_desde_transcripcion
from agent.memory import inicializar_db, guardar_mensaje, obtener_historial, limpiar_historial

TELEFONO_TEST = "test-local-001"


async def main():
    await inicializar_db()

    print()
    print("=" * 60)
    print("   JuiceBot — Test Local | Fresh to Go Foods")
    print("=" * 60)
    print()
    print("  Comandos disponibles:")
    print("    Texto normal     → chat con JuiceBot")
    print("    /audio [texto]   → simula una nota de voz con ese texto")
    print("    limpiar          → borra el historial")
    print("    salir            → termina el test")
    print()
    print("  Ejemplo de audio:")
    print("    /audio necesito 50 kilos de green apple, 30 de mango y 20 cajas de pineapple")
    print()
    print("-" * 60)
    print()

    while True:
        try:
            entrada = input("Tu: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nTest finalizado.")
            break

        if not entrada:
            continue

        if entrada.lower() == "salir":
            print("\nTest finalizado.")
            break

        if entrada.lower() == "limpiar":
            await limpiar_historial(TELEFONO_TEST)
            print("[Historial borrado]\n")
            continue

        # Simular nota de voz
        if entrada.lower().startswith("/audio "):
            transcripcion = entrada[7:].strip()
            if not transcripcion:
                print("  Escribe el texto despues de /audio\n")
                continue

            print(f"\n  [Simulando audio] Transcripcion: {transcripcion}")
            print("\nJuiceBot: ", end="", flush=True)
            pedido = await generar_pedido_desde_transcripcion(transcripcion)
            print(pedido)
            await guardar_mensaje(TELEFONO_TEST, "user", f"[AUDIO] {transcripcion}")
            await guardar_mensaje(TELEFONO_TEST, "assistant", pedido)
            print()
            continue

        # Mensaje de texto normal
        historial = await obtener_historial(TELEFONO_TEST)
        print("\nJuiceBot: ", end="", flush=True)
        respuesta = await generar_respuesta(entrada, historial)
        print(respuesta)
        await guardar_mensaje(TELEFONO_TEST, "user", entrada)
        await guardar_mensaje(TELEFONO_TEST, "assistant", respuesta)
        print()


if __name__ == "__main__":
    asyncio.run(main())
