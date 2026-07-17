"""
engine.py — Motor de decision de AgroLink AI.

Contiene la logica de "IA" del prototipo: no son modelos entrenados
(no hay datos historicos propios todavia, como se explica en el
informe de propuesta), sino un sistema de scoring por reglas
ponderadas -- el mismo enfoque recomendado para la fase de MVP antes
de tener volumen de datos real.
"""

from datetime import date, timedelta
from data import (
    COMPRADORES, TRANSPORTISTAS, CERTIFICADORAS, FINANCIAMIENTO,
    obtener_riesgo_puerto, documentos_requeridos,
)


def buscar_compradores(tipo_cafe: str, cantidad_kg: float, top_n: int = 3) -> list:
    """Cruza la publicacion del productor con la base de compradores.

    Score = compatibilidad de tipo de cafe + ajuste por precio +
    reputacion + cercania relativa. Devuelve los N mejores, no el
    listado completo -- ese es justo el punto: matching, no directorio.
    """
    resultados = []
    for comprador in COMPRADORES:
        if tipo_cafe not in comprador["tipo_cafe"]:
            continue
        if not (comprador["volumen_min_kg"] <= cantidad_kg <= comprador["volumen_max_kg"]):
            # Penaliza pero no descarta del todo si esta cerca del rango
            if cantidad_kg < comprador["volumen_min_kg"] * 0.7 or cantidad_kg > comprador["volumen_max_kg"] * 1.3:
                continue

        precio_score = min(1.0, comprador["precio_usd_kg"] / 8.5)
        reputacion_score = comprador["reputacion"] / 5.0
        cercania_score = comprador["distancia_relativa"]
        pago_score = max(0.3, 1 - (comprador["pago_dias"] / 45))

        compatibilidad = (
            0.35 * precio_score +
            0.30 * reputacion_score +
            0.20 * cercania_score +
            0.15 * pago_score
        )
        resultados.append({**comprador, "compatibilidad_pct": round(compatibilidad * 100, 1)})

    resultados.sort(key=lambda c: c["compatibilidad_pct"], reverse=True)
    return resultados[:top_n]


def recomendar_transporte(dias_disponibles: int = 5) -> list:
    """Recomienda transporte por conveniencia total, no solo por precio."""
    resultados = []
    for t in TRANSPORTISTAS:
        cumple_plazo = t["dias_entrega"] <= dias_disponibles
        costo_score = 1 - (t["costo_usd"] / 1000)
        confiabilidad_score = 1 - (t["retrasos_historicos_pct"] / 100)
        reputacion_score = t["reputacion"] / 5.0

        conveniencia = (
            0.30 * costo_score +
            0.40 * confiabilidad_score +
            0.30 * reputacion_score
        )
        resultados.append({
            **t,
            "cumple_plazo": cumple_plazo,
            "conveniencia_pct": round(conveniencia * 100, 1),
        })
    resultados.sort(key=lambda t: t["conveniencia_pct"], reverse=True)
    return resultados


def estimar_financiamiento(cantidad_kg: float, precio_usd_kg: float) -> dict:
    """Estima capital de trabajo necesario y muestra mejores opciones."""
    valor_operacion = cantidad_kg * precio_usd_kg
    capital_estimado = valor_operacion * 0.35  # supuesto: 35% como capital de trabajo previo al pago del comprador
    opciones = sorted(FINANCIAMIENTO, key=lambda f: f["tasa_anual_pct"])
    return {
        "valor_operacion_usd": round(valor_operacion, 2),
        "capital_estimado_usd": round(capital_estimado, 2),
        "opciones": opciones,
    }


def checklist_documental(pais_destino: str, docs_marcados: set) -> list:
    requeridos = documentos_requeridos(pais_destino)
    return [{"documento": d, "listo": d in docs_marcados} for d in requeridos]


def generar_plan_exportacion(cantidad_kg: float, tipo_cafe: str, pais_destino: str,
                              puerto: str, fecha_embarque: date, docs_marcados: set) -> dict:
    """El 'Agente IA de Exportacion': arma el plan completo a partir de
    los datos de la operacion, tal como se describe en la propuesta
    (modulo copiloto, no solo marketplace)."""
    compradores = buscar_compradores(tipo_cafe, cantidad_kg, top_n=3)
    mejor_comprador = compradores[0] if compradores else None
    precio_ref = mejor_comprador["precio_usd_kg"] if mejor_comprador else 7.0

    dias_disponibles = max(1, (fecha_embarque - date.today()).days)
    transportes = recomendar_transporte(dias_disponibles)
    mejor_transporte = transportes[0] if transportes else None

    riesgo = obtener_riesgo_puerto(puerto, fecha_embarque)
    checklist = checklist_documental(pais_destino, docs_marcados)
    faltantes = [c["documento"] for c in checklist if not c["listo"]]

    financiamiento = estimar_financiamiento(cantidad_kg, precio_ref)

    alertas = []
    if riesgo["nivel"] in ("Alto", "Medio"):
        alertas.append(f"Riesgo {riesgo['nivel'].lower()} en puerto {puerto}: {riesgo['recomendacion']}")
    if faltantes:
        alertas.append(f"Documentos pendientes: {', '.join(faltantes)}.")
    if not compradores:
        alertas.append("No se encontraron compradores compatibles con estos criterios en la base actual.")

    return {
        "compradores": compradores,
        "mejor_comprador": mejor_comprador,
        "transportes": transportes,
        "mejor_transporte": mejor_transporte,
        "riesgo": riesgo,
        "checklist": checklist,
        "documentos_faltantes": faltantes,
        "financiamiento": financiamiento,
        "alertas": alertas,
    }
