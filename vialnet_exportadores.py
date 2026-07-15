"""
VialNet — Módulo de Visibilidad de Rutas Críticas para Cadenas Exportadoras
============================================================================
Prototipo funcional para Disruptón 2026 (Eje 2: Infraestructura, operación
y visibilidad de la cadena).

QUÉ ES ESTO Y QUÉ NO ES
------------------------
- SÍ es una interfaz funcional real, ejecutable, que demuestra cómo una
  empresa acopiadora/exportadora vería el estado de las rutas críticas
  de sus proveedores.
- SÍ usa una fórmula de riesgo transparente y explicable (reglas simples,
  documentadas abajo), no un modelo de IA entrenado.
- NO contiene datos reales de ninguna empresa exportadora todavía: los
  8 tramos y sus valores son datos de DEMOSTRACIÓN, con la misma
  estructura que el piloto real de VialNet en Ocongate (8 tramos, ~119 km).
- Antes de presentarlo como validado ante el jurado, hay que:
    1) reemplazar los datos de demo por los reales del piloto (o una
       conexión a la base PostgreSQL/Supabase ya existente), y
    2) validar la fórmula de riesgo con al menos una empresa
       acopiadora/exportadora real (bases, sección 8: no fabricar
       validaciones ni resultados).

Cómo ejecutarlo:
    pip install streamlit pandas plotly --break-system-packages
    streamlit run vialnet_exportadores.py
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import date

# ---------------------------------------------------------------------------
# Configuración de página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="VialNet · Visibilidad para Exportadores",
    page_icon="🧭",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Datos de demostración
# ---------------------------------------------------------------------------
# Estructura idéntica a la del piloto real de VialNet (8 tramos, distrito de
# Ocongate). Los valores de estado_via, dias_sin_mantenimiento y volumen son
# DATOS DE DEMO — reemplazar por la data real del piloto antes de usar esto
# como evidencia de validación.

TRAMOS_DEMO = pd.DataFrame([
    {"tramo": "T1 - Ocongate - Tinki",         "comunidad": "Tinki",         "km": 18.4, "estado_via": "Regular", "dias_sin_mantenimiento": 42, "temporada_lluvias": True,  "volumen_relativo": 0.9},
    {"tramo": "T2 - Tinki - Pacchanta",        "comunidad": "Pacchanta",     "km": 9.7,  "estado_via": "Malo",    "dias_sin_mantenimiento": 96, "temporada_lluvias": True,  "volumen_relativo": 0.7},
    {"tramo": "T3 - Ocongate - Upisa",         "comunidad": "Upisa",         "km": 14.2, "estado_via": "Bueno",   "dias_sin_mantenimiento": 12, "temporada_lluvias": False, "volumen_relativo": 0.6},
    {"tramo": "T4 - Upisa - Pampacancha",      "comunidad": "Pampacancha",   "km": 11.5, "estado_via": "Regular", "dias_sin_mantenimiento": 55, "temporada_lluvias": True,  "volumen_relativo": 0.8},
    {"tramo": "T5 - Ocongate - Ccatcca",       "comunidad": "Ccatcca",       "km": 21.0, "estado_via": "Bueno",   "dias_sin_mantenimiento": 20, "temporada_lluvias": False, "volumen_relativo": 1.0},
    {"tramo": "T6 - Ccatcca - Accocunca",      "comunidad": "Accocunca",     "km": 13.8, "estado_via": "Malo",    "dias_sin_mantenimiento": 110,"temporada_lluvias": True,  "volumen_relativo": 0.5},
    {"tramo": "T7 - Ocongate - Chillihuani",   "comunidad": "Chillihuani",   "km": 16.9, "estado_via": "Regular", "dias_sin_mantenimiento": 38, "temporada_lluvias": False, "volumen_relativo": 0.7},
    {"tramo": "T8 - Chillihuani - Lauramarca", "comunidad": "Lauramarca",    "km": 13.5, "estado_via": "Bueno",   "dias_sin_mantenimiento": 8,  "temporada_lluvias": False, "volumen_relativo": 0.9},
])

# ---------------------------------------------------------------------------
# Fórmula de riesgo — transparente y documentada (NO es un modelo de IA)
# ---------------------------------------------------------------------------
# Riesgo (0-100) = combinación ponderada de tres factores observables:
#   40% estado físico de la vía (Bueno=0, Regular=50, Malo=100)
#   35% días sin mantenimiento, normalizado a un máximo de 120 días
#   25% temporada de lluvias (activa=100, inactiva=0)
#
# Estos pesos son un punto de partida razonable para el prototipo y deben
# ajustarse con la empresa exportadora piloto una vez se valide con datos
# reales (bases, sección 8: transparencia y verificabilidad del uso de IA
# y de la evidencia).

ESTADO_PENALTY = {"Bueno": 0, "Regular": 50, "Malo": 100}
PESO_ESTADO = 0.40
PESO_DIAS = 0.35
PESO_TEMPORADA = 0.25
DIAS_MAX = 120


def calcular_riesgo(row: pd.Series) -> float:
    p_estado = ESTADO_PENALTY[row["estado_via"]]
    p_dias = min(row["dias_sin_mantenimiento"] / DIAS_MAX, 1.0) * 100
    p_temporada = 100 if row["temporada_lluvias"] else 0
    riesgo = (
        PESO_ESTADO * p_estado
        + PESO_DIAS * p_dias
        + PESO_TEMPORADA * p_temporada
    )
    return round(riesgo, 1)


def nivel_riesgo(score: float) -> str:
    if score >= 66:
        return "Alto"
    if score >= 33:
        return "Medio"
    return "Bajo"


def recomendacion(row: pd.Series) -> str:
    if row["nivel_riesgo"] == "Alto":
        return "Priorizar mantenimiento antes del próximo recojo; coordinar transporte alternativo o adelantar fecha de acopio."
    if row["nivel_riesgo"] == "Medio":
        return "Monitorear semanalmente; confirmar con la comunidad el estado antes de programar el recojo."
    return "Sin acción inmediata; mantener monitoreo de rutina."


df = TRAMOS_DEMO.copy()
df["riesgo_score"] = df.apply(calcular_riesgo, axis=1)
df["nivel_riesgo"] = df["riesgo_score"].apply(nivel_riesgo)
df["recomendacion"] = df.apply(recomendacion, axis=1)

# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------
st.title("🧭 VialNet — Visibilidad de rutas críticas para exportadores")
st.caption(
    "Prototipo funcional · Disruptón 2026 · Eje 2: Infraestructura, operación "
    "y visibilidad de la cadena"
)

st.warning(
    "⚠️ **Datos de demostración.** Esta vista usa la misma estructura del "
    "piloto real de VialNet (8 tramos, ~119 km, distrito de Ocongate), pero "
    "los valores de estado, mantenimiento y riesgo son ilustrativos. "
    "Pendiente: conectar con la base de datos real y validar la fórmula "
    "de riesgo con una empresa acopiadora/exportadora.",
    icon="⚠️",
)

# ---------------------------------------------------------------------------
# KPIs principales
# ---------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Tramos monitoreados", len(df))
col2.metric("Km totales", f"{df['km'].sum():.1f} km")
col3.metric("Tramos en riesgo alto", int((df["nivel_riesgo"] == "Alto").sum()))
col4.metric("Riesgo promedio", f"{df['riesgo_score'].mean():.0f} / 100")

st.divider()

# ---------------------------------------------------------------------------
# Panel principal: mapa de riesgo + tabla
# ---------------------------------------------------------------------------
left, right = st.columns([3, 2])

with left:
    st.subheader("Nivel de riesgo por tramo")
    color_map = {"Alto": "#D64545", "Medio": "#E8A33D", "Bajo": "#3F9142"}
    fig = px.bar(
        df.sort_values("riesgo_score", ascending=True),
        x="riesgo_score",
        y="tramo",
        color="nivel_riesgo",
        color_discrete_map=color_map,
        orientation="h",
        labels={"riesgo_score": "Riesgo (0-100)", "tramo": ""},
        text="riesgo_score",
    )
    fig.update_layout(showlegend=True, height=420, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Alertas activas")
    alertas = df[df["nivel_riesgo"] != "Bajo"].sort_values("riesgo_score", ascending=False)
    if alertas.empty:
        st.success("Sin alertas activas en este momento.")
    else:
        for _, r in alertas.iterrows():
            icon = "🔴" if r["nivel_riesgo"] == "Alto" else "🟠"
            with st.container(border=True):
                st.markdown(f"{icon} **{r['tramo']}**  ·  riesgo {r['riesgo_score']}/100")
                st.caption(r["recomendacion"])

st.divider()

# ---------------------------------------------------------------------------
# Detalle por tramo
# ---------------------------------------------------------------------------
st.subheader("Detalle de tramo")
tramo_sel = st.selectbox("Selecciona un tramo", df["tramo"])
row = df[df["tramo"] == tramo_sel].iloc[0]

d1, d2, d3, d4 = st.columns(4)
d1.metric("Estado de la vía", row["estado_via"])
d2.metric("Días sin mantenimiento", int(row["dias_sin_mantenimiento"]))
d3.metric("Temporada de lluvias", "Sí" if row["temporada_lluvias"] else "No")
d4.metric("Nivel de riesgo", row["nivel_riesgo"])

st.info(f"**Recomendación:** {row['recomendacion']}")

with st.expander("¿Cómo se calculó este riesgo? (metodología transparente)"):
    st.markdown(
        f"""
El riesgo se calcula con una fórmula simple y auditable, **no con un modelo
de IA entrenado**, para que cualquier persona pueda verificar el resultado:

- **{PESO_ESTADO*100:.0f}%** — Estado físico de la vía
  (Bueno = 0, Regular = 50, Malo = 100)
- **{PESO_DIAS*100:.0f}%** — Días sin mantenimiento, normalizado sobre un
  máximo de {DIAS_MAX} días
- **{PESO_TEMPORADA*100:.0f}%** — Temporada de lluvias activa (100) o no (0)

Riesgo de **{row['tramo']}** = {PESO_ESTADO*100:.0f}% × {ESTADO_PENALTY[row['estado_via']]}
\u2003+\u2003 {PESO_DIAS*100:.0f}% × {min(row['dias_sin_mantenimiento']/DIAS_MAX,1)*100:.0f}
\u2003+\u2003 {PESO_TEMPORADA*100:.0f}% × {100 if row['temporada_lluvias'] else 0}
\u2003= **{row['riesgo_score']}/100**

Estos pesos son un punto de partida razonable para el prototipo. Antes de
presentarlos como validados, deben ajustarse en conversación con una
empresa acopiadora/exportadora real.
        """
    )

st.divider()

# ---------------------------------------------------------------------------
# Tabla completa
# ---------------------------------------------------------------------------
st.subheader("Todos los tramos")
st.dataframe(
    df[["tramo", "comunidad", "km", "estado_via", "dias_sin_mantenimiento",
        "temporada_lluvias", "riesgo_score", "nivel_riesgo"]],
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "VialNet · Disruptón 2026 · Prototipo de demostración — datos ilustrativos, "
    "pendientes de validación con una empresa exportadora real."
)
