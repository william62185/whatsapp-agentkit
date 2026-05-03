# agent/tools.py — Herramientas del agente
# Generado por AgentKit

"""
Herramientas de soporte para JuiceBot.
Por ahora incluye utilidades para el area de jugos de Fresh to Go Foods.
"""

import os
import yaml
import logging
from datetime import datetime, date

logger = logging.getLogger("agentkit")

# Unidades de medida validas en el area de jugos
UNIDADES_VALIDAS = ["kg", "lb", "libras", "unidades", "cajas", "bolsas", "litros", "galones", "oz"]

# Insumos comunes del area de jugos (referencia para el agente)
INSUMOS_COMUNES = [
    # Frutas
    "green apple", "red apple", "pomegranate", "pineapple", "orange", "lemon",
    "lime", "mango", "watermelon", "strawberry", "blueberry", "grape",
    "passion fruit", "maracuya", "papaya", "guava", "guayaba",
    # Vegetales
    "fennel", "medium carrots", "celery", "beets", "ginger", "cucumber",
    "spinach", "kale", "turmeric", "curcuma",
    # Otros
    "sugar", "honey", "water", "coconut water", "bottles", "labels",
]


def cargar_info_negocio() -> dict:
    """Carga la informacion del negocio desde business.yaml."""
    try:
        with open("config/business.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("config/business.yaml no encontrado")
        return {}


def obtener_fecha_hoy() -> str:
    """Retorna la fecha actual formateada."""
    return date.today().strftime("%d/%m/%Y")


def esta_en_horario() -> bool:
    """Verifica si el momento actual esta dentro del horario de atencion."""
    ahora = datetime.now()
    # Lunes a Viernes (0=lunes, 4=viernes)
    if ahora.weekday() > 4:
        return False
    hora = ahora.hour + ahora.minute / 60
    return 10.0 <= hora <= 18.5  # 10am a 6:30pm
