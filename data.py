"""
data.py — Datos simulados para el prototipo AgroLink AI.

Estos datos son de ejemplo (mock), pensados para que la demo sea
representativa y creíble, no una base de datos real de producción.
"""

import random
from datetime import date, timedelta

# ---------------------------------------------------------------------
# Compradores internacionales (mock)
# ---------------------------------------------------------------------
COMPRADORES = [
    {"id": "C001", "nombre": "Hamburg Coffee Importers", "pais": "Alemania",
     "tipo_cafe": ["Especial", "Organico"], "volumen_min_kg": 500, "volumen_max_kg": 20000,
     "precio_usd_kg": 7.80, "reputacion": 4.8, "pago_dias": 15, "distancia_relativa": 0.7},
    {"id": "C002", "nombre": "Nordic Roasters AB", "pais": "Suecia",
     "tipo_cafe": ["Especial"], "volumen_min_kg": 300, "volumen_max_kg": 5000,
     "precio_usd_kg": 8.20, "reputacion": 4.6, "pago_dias": 20, "distancia_relativa": 0.65},
    {"id": "C003", "nombre": "Rocky Mountain Coffee Co.", "pais": "Estados Unidos",
     "tipo_cafe": ["Convencional", "Especial"], "volumen_min_kg": 1000, "volumen_max_kg": 40000,
     "precio_usd_kg": 7.10, "reputacion": 4.3, "pago_dias": 30, "distancia_relativa": 0.9},
    {"id": "C004", "nombre": "Antwerp Green Beans NV", "pais": "Belgica",
     "tipo_cafe": ["Convencional", "Organico"], "volumen_min_kg": 2000, "volumen_max_kg": 50000,
     "precio_usd_kg": 7.40, "reputacion": 4.5, "pago_dias": 25, "distancia_relativa": 0.7},
    {"id": "C005", "nombre": "Toronto Bean Traders", "pais": "Canada",
     "tipo_cafe": ["Especial", "Organico"], "volumen_min_kg": 500, "volumen_max_kg": 15000,
     "precio_usd_kg": 7.60, "reputacion": 4.4, "pago_dias": 20, "distancia_relativa": 0.85},
    {"id": "C006", "nombre": "Bogota Trading Partners", "pais": "Colombia",
     "tipo_cafe": ["Convencional"], "volumen_min_kg": 1000, "volumen_max_kg": 10000,
     "precio_usd_kg": 6.90, "reputacion": 4.0, "pago_dias": 10, "distancia_relativa": 0.95},
]

# ---------------------------------------------------------------------
# Transportistas (mock)
# ---------------------------------------------------------------------
TRANSPORTISTAS = [
    {"id": "T001", "nombre": "Transportes Andinos SAC", "costo_usd": 850,
     "dias_entrega": 2, "retrasos_historicos_pct": 4, "reputacion": 4.7},
    {"id": "T002", "nombre": "Rutas del Norte EIRL", "costo_usd": 780,
     "dias_entrega": 3, "retrasos_historicos_pct": 12, "reputacion": 4.1},
    {"id": "T003", "nombre": "Carga Segura Peru", "costo_usd": 920,
     "dias_entrega": 2, "retrasos_historicos_pct": 2, "reputacion": 4.9},
    {"id": "T004", "nombre": "Express Cajamarca", "costo_usd": 700,
     "dias_entrega": 4, "retrasos_historicos_pct": 18, "reputacion": 3.8},
]

# ---------------------------------------------------------------------
# Certificadoras (mock)
# ---------------------------------------------------------------------
CERTIFICADORAS = [
    {"id": "CERT01", "nombre": "OrganicCert Peru", "certificados": ["Organico", "Fitosanitario"], "dias_emision": 5},
    {"id": "CERT02", "nombre": "FairTrade Andes", "certificados": ["Comercio Justo", "Origen"], "dias_emision": 3},
    {"id": "CERT03", "nombre": "SENASA Regional", "certificados": ["Fitosanitario"], "dias_emision": 2},
]

# ---------------------------------------------------------------------
# Entidades financieras (mock)
# ---------------------------------------------------------------------
FINANCIAMIENTO = [
    {"entidad": "Agrobanco", "tasa_anual_pct": 14.5, "plazo_max_dias": 120},
    {"entidad": "Caja Arequipa", "tasa_anual_pct": 16.0, "plazo_max_dias": 90},
    {"entidad": "BCP Agro", "tasa_anual_pct": 13.2, "plazo_max_dias": 150},
]

# ---------------------------------------------------------------------
# Riesgo portuario / logístico (mock, basado en patrones documentados:
# Paita/Callao en rutas de bajo trafico naviero -> mayor variabilidad)
# ---------------------------------------------------------------------
PUERTOS = {
    "Callao": {"congestion_base": 0.55, "trafico_naviero": "medio"},
    "Paita": {"congestion_base": 0.68, "trafico_naviero": "bajo"},
}


def obtener_riesgo_puerto(puerto: str, fecha_embarque: date) -> dict:
    """Simula un score de riesgo logistico para un puerto y fecha dados.

    No es un modelo entrenado real: combina una congestion base (que
    refleja el patron documentado de baja prioridad naviera en rutas
    del Pacifico) con una variacion aleatoria acotada, para que la demo
    muestre variabilidad realista sin depender de una API externa.
    """
    info = PUERTOS.get(puerto, {"congestion_base": 0.5, "trafico_naviero": "medio"})
    random.seed(f"{puerto}-{fecha_embarque.isoformat()}")
    variacion = random.uniform(-0.15, 0.20)
    score = max(0.0, min(1.0, info["congestion_base"] + variacion))

    if score >= 0.65:
        nivel, color = "Alto", "#a33636"
        recomendacion = "Adelantar la salida del almacen 2-3 dias o evaluar el puerto alterno."
    elif score >= 0.40:
        nivel, color = "Medio", "#8a6d1f"
        recomendacion = "Confirmar cupo naviero con anticipacion; monitorear cambios."
    else:
        nivel, color = "Bajo", "#2e6b4f"
        recomendacion = "Condiciones normales; mantener el calendario planificado."

    return {
        "puerto": puerto,
        "score": round(score, 2),
        "nivel": nivel,
        "color": color,
        "trafico_naviero": info["trafico_naviero"],
        "recomendacion": recomendacion,
    }


DOCUMENTOS_BASE = ["Factura comercial", "Packing list"]
DOCUMENTOS_POR_DESTINO = {
    "Union Europea": ["Certificado fitosanitario", "Certificado de origen", "Declaracion de diligencia debida (EUDR)"],
    "Estados Unidos": ["Certificado fitosanitario", "Certificado de origen"],
    "default": ["Certificado fitosanitario", "Certificado de origen"],
}

PAISES_UE = {"Alemania", "Suecia", "Belgica", "Francia", "Italia", "Espana", "Paises Bajos"}


def documentos_requeridos(pais_destino: str) -> list:
    grupo = "Union Europea" if pais_destino in PAISES_UE else DOCUMENTOS_POR_DESTINO.get(pais_destino, "default")
    extra = DOCUMENTOS_POR_DESTINO["Union Europea"] if pais_destino in PAISES_UE else DOCUMENTOS_POR_DESTINO["default"]
    return DOCUMENTOS_BASE + extra
