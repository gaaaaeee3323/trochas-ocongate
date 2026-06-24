# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  PLATAFORMA WEB — GESTIÓN DE TROCHAS CARROZABLES                            ║
║  Sistema de Registro, Inspección Técnica y Gestión de Mantenimiento Vial    ║
║  Municipalidad Distrital de Ocongate — Quispicanchi, Cusco, Perú            ║
║                                                                               ║
║  Autor  : Frank Puma Mamani | Código: 202220055                             ║
║  Curso  : Proyecto Preprofesional — Teoría 7, UTEC 2026-I                    ║
║  Docente: Mg. Fernandez Choquepuma, Miguel Ángel                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

INSTALACIÓN:
    pip install streamlit plotly pandas pillow openpyxl fpdf2

EJECUCIÓN LOCAL:
    streamlit run plataforma_trochas.py

ESTRUCTURA (5 módulos según especificación):
    1. 🏠 INICIO                    — Presentación, KPIs rápidos, gráficos resumen
    2. 🛣️ REGISTRO DE TRAMOS         — Alta de tramos + evidencia fotográfica + adjuntos
    3. 📂 CONSULTA DE TRAMOS         — Buscar / filtrar / editar / eliminar / descargar
    4. 📋 FICHA TÉCNICA DE DAÑOS     — Ficha tipo Provías + clasificación automática + ICT
    5. 📊 REPORTES                  — Reportes automáticos + gráficos Plotly + export Excel/PDF

Persistencia: SQLite local (trochas_ocongate.db) — se crea automáticamente.
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from io import BytesIO
import base64
import os

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN GENERAL
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Gestión de Trochas Carrozables — Ocongate",
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trochas_ocongate.db")

# ──────────────────────────────────────────────────────────────────────────────
# BASE DE DATOS
# ──────────────────────────────────────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS tramos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            nombre TEXT,
            comunidad TEXT,
            distrito TEXT,
            provincia TEXT,
            departamento TEXT,
            longitud_km REAL,
            ancho_m REAL,
            tipo_superficie TEXT,
            estado_actual TEXT,
            responsable TEXT,
            telefono_responsable TEXT,
            fecha_registro TEXT,
            foto_inicio BLOB,
            foto_intermedia BLOB,
            foto_final BLOB,
            foto_danos BLOB,
            adjunto_pdf BLOB,
            adjunto_pdf_nombre TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS danos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tramo_id INTEGER,
            progresiva_inicial REAL,
            progresiva_final REAL,
            longitud_afectada REAL,
            tipo_dano TEXT,
            tipo_falla TEXT,
            nivel_gravedad TEXT,
            clase_densidad TEXT,
            estado_tramo TEXT,
            transitabilidad TEXT,
            necesidad_intervencion TEXT,
            tiempo_estimado_dias REAL,
            fecha_inspeccion TEXT,
            observaciones TEXT,
            ict REAL,
            pct_deterioro REAL,
            prioridad TEXT,
            foto_dano BLOB,
            FOREIGN KEY (tramo_id) REFERENCES tramos(id)
        )
    """)
    conn.commit()
    conn.close()


init_db()

# ──────────────────────────────────────────────────────────────────────────────
# DICCIONARIOS / REGLAS DE CLASIFICACIÓN AUTOMÁTICA
# ──────────────────────────────────────────────────────────────────────────────
TIPOS_SUPERFICIE = ["Asfaltado (AS)", "Afirmado (AF)", "Sin Afirmar (SA)", "Trocha (T)"]
ESTADOS_TRAMO = ["Bueno", "Regular", "Malo", "Muy Malo"]

TIPOS_DANO = [
    "Deformación", "Erosión", "Baches o Huecos", "Encalaminado", "Lodazal",
    "Cruce de Agua", "Hundimiento", "Pérdida de Plataforma", "Deslizamiento",
    "Falla de Drenaje",
]

# Clasificación de falla: Superficial vs Estructural (criterio MTC MCV-2014)
FALLA_SUPERFICIAL = {"Deformación", "Erosión", "Encalaminado", "Lodazal", "Cruce de Agua"}
FALLA_ESTRUCTURAL = {"Baches o Huecos", "Hundimiento", "Pérdida de Plataforma",
                      "Deslizamiento", "Falla de Drenaje"}

# Severidad base por tipo de daño (peso 0-3) usado en el cálculo del ICT
PESO_DANO = {
    "Deformación": 1, "Erosión": 1, "Encalaminado": 1, "Lodazal": 2,
    "Cruce de Agua": 1, "Baches o Huecos": 2, "Hundimiento": 3,
    "Pérdida de Plataforma": 3, "Deslizamiento": 3, "Falla de Drenaje": 2,
}

NIVELES_GRAVEDAD = ["Sin Deterioro", "Leve", "Moderada", "Severa"]
CLASES_DENSIDAD = ["No aplica", "Baja", "Media", "Alta"]


def clasificar_falla(tipo_dano: str) -> str:
    if tipo_dano in FALLA_ESTRUCTURAL:
        return "Estructural"
    return "Superficial"


def calcular_gravedad(longitud_afectada: float, longitud_tramo: float, peso_dano: int) -> str:
    """Gravedad en función de % de longitud afectada y severidad propia del daño."""
    if longitud_tramo <= 0:
        pct = 0
    else:
        pct = (longitud_afectada / longitud_tramo) * 100
    score = pct * 0.5 + peso_dano * 10
    if score < 10:
        return "Sin Deterioro"
    elif score < 25:
        return "Leve"
    elif score < 50:
        return "Moderada"
    else:
        return "Severa"


def calcular_estado(gravedad: str) -> str:
    return {
        "Sin Deterioro": "Bueno",
        "Leve": "Regular",
        "Moderada": "Malo",
        "Severa": "Muy Malo",
    }.get(gravedad, "Regular")


def calcular_transitabilidad(estado: str) -> str:
    return {
        "Bueno": "Libre",
        "Regular": "Libre",
        "Malo": "Restringida",
        "Muy Malo": "Interrumpida",
    }.get(estado, "Libre")


def calcular_prioridad(estado: str, transitabilidad: str) -> str:
    if transitabilidad == "Interrumpida":
        return "Urgente"
    if estado == "Malo":
        return "Alta"
    if estado == "Regular":
        return "Media"
    return "Baja"


def calcular_tiempo_reparacion(tipo_dano: str, longitud_afectada: float) -> float:
    """Días estimados de reparación según tipo de daño y longitud afectada (km)."""
    rendimiento_km_dia = {  # rendimiento referencial MCV-2014 (km/día por cuadrilla)
        "Deformación": 0.8, "Erosión": 0.6, "Baches o Huecos": 1.0,
        "Encalaminado": 1.2, "Lodazal": 0.4, "Cruce de Agua": 0.3,
        "Hundimiento": 0.25, "Pérdida de Plataforma": 0.2,
        "Deslizamiento": 0.15, "Falla de Drenaje": 0.35,
    }.get(tipo_dano, 0.5)
    dias = max(1.0, longitud_afectada / rendimiento_km_dia)
    return round(dias, 1)


def calcular_ict(gravedad: str, densidad: str, falla: str) -> float:
    """Índice de Condición de Trocha (0-100, 100 = óptimo)."""
    base = {"Sin Deterioro": 100, "Leve": 80, "Moderada": 55, "Severa": 25}.get(gravedad, 80)
    ajuste_densidad = {"No aplica": 0, "Baja": -2, "Media": -8, "Alta": -15}.get(densidad, 0)
    ajuste_falla = -10 if falla == "Estructural" else -3
    ict = base + ajuste_densidad + ajuste_falla
    return max(0.0, min(100.0, round(ict, 1)))


def calcular_necesidad_intervencion(prioridad: str) -> str:
    return {
        "Urgente": "Intervención inmediata (correctivo de emergencia)",
        "Alta": "Intervención correctiva en el corto plazo (≤ 30 días)",
        "Media": "Mantenimiento periódico programado",
        "Baja": "Mantenimiento rutinario / monitoreo",
    }.get(prioridad, "Monitoreo")


# ──────────────────────────────────────────────────────────────────────────────
# UTILIDADES DE DATOS
# ──────────────────────────────────────────────────────────────────────────────
def img_to_blob(uploaded_file):
    if uploaded_file is None:
        return None
    return uploaded_file.getvalue()


def blob_to_img(blob):
    if blob is None:
        return None
    return BytesIO(blob)


def df_tramos() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT id, codigo, nombre, comunidad, distrito, provincia, departamento,
               longitud_km, ancho_m, tipo_superficie, estado_actual, responsable,
               telefono_responsable, fecha_registro
        FROM tramos ORDER BY id DESC
    """, conn)
    conn.close()
    return df


def df_danos() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT d.*, t.codigo AS codigo_tramo, t.nombre AS nombre_tramo,
               t.longitud_km AS longitud_tramo_km
        FROM danos d
        LEFT JOIN tramos t ON d.tramo_id = t.id
        ORDER BY d.id DESC
    """, conn)
    conn.close()
    return df


def insertar_tramo(data: dict):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO tramos (codigo, nombre, comunidad, distrito, provincia, departamento,
            longitud_km, ancho_m, tipo_superficie, estado_actual, responsable,
            telefono_responsable, fecha_registro, foto_inicio, foto_intermedia,
            foto_final, foto_danos, adjunto_pdf, adjunto_pdf_nombre)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data["codigo"], data["nombre"], data["comunidad"], data["distrito"],
        data["provincia"], data["departamento"], data["longitud_km"], data["ancho_m"],
        data["tipo_superficie"], data["estado_actual"], data["responsable"],
        data["telefono_responsable"], data["fecha_registro"], data["foto_inicio"],
        data["foto_intermedia"], data["foto_final"], data["foto_danos"],
        data["adjunto_pdf"], data["adjunto_pdf_nombre"],
    ))
    conn.commit()
    conn.close()


def actualizar_tramo(tramo_id: int, data: dict):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        UPDATE tramos SET codigo=?, nombre=?, comunidad=?, distrito=?, provincia=?,
            departamento=?, longitud_km=?, ancho_m=?, tipo_superficie=?, estado_actual=?,
            responsable=?, telefono_responsable=?
        WHERE id=?
    """, (
        data["codigo"], data["nombre"], data["comunidad"], data["distrito"],
        data["provincia"], data["departamento"], data["longitud_km"], data["ancho_m"],
        data["tipo_superficie"], data["estado_actual"], data["responsable"],
        data["telefono_responsable"], tramo_id,
    ))
    conn.commit()
    conn.close()


def eliminar_tramo(tramo_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM danos WHERE tramo_id=?", (tramo_id,))
    c.execute("DELETE FROM tramos WHERE id=?", (tramo_id,))
    conn.commit()
    conn.close()


def insertar_dano(data: dict):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO danos (tramo_id, progresiva_inicial, progresiva_final, longitud_afectada,
            tipo_dano, tipo_falla, nivel_gravedad, clase_densidad, estado_tramo,
            transitabilidad, necesidad_intervencion, tiempo_estimado_dias, fecha_inspeccion,
            observaciones, ict, pct_deterioro, prioridad, foto_dano)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data["tramo_id"], data["progresiva_inicial"], data["progresiva_final"],
        data["longitud_afectada"], data["tipo_dano"], data["tipo_falla"],
        data["nivel_gravedad"], data["clase_densidad"], data["estado_tramo"],
        data["transitabilidad"], data["necesidad_intervencion"], data["tiempo_estimado_dias"],
        data["fecha_inspeccion"], data["observaciones"], data["ict"], data["pct_deterioro"],
        data["prioridad"], data["foto_dano"],
    ))
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────────────────────────────────────
# EXPORTACIÓN
# ──────────────────────────────────────────────────────────────────────────────
def exportar_excel(dfs: dict) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in dfs.items():
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return output.getvalue()


def exportar_pdf_resumen(titulo: str, df_resumen: pd.DataFrame, texto_intro: str = "") -> bytes:
    try:
        from fpdf import FPDF
    except ImportError:
        return None
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.multi_cell(0, 8, titulo)
    pdf.set_font("Helvetica", "", 9)
    if texto_intro:
        pdf.multi_cell(0, 5, texto_intro)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 8)
    cols = list(df_resumen.columns)
    col_w = max(20, int(190 / max(1, len(cols))))
    for col in cols:
        pdf.cell(col_w, 6, str(col)[:18], border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 7)
    for _, row in df_resumen.iterrows():
        for col in cols:
            pdf.cell(col_w, 6, str(row[col])[:18], border=1)
        pdf.ln()
    return bytes(pdf.output(dest="S"))


def download_button_bytes(data: bytes, filename: str, label: str, mime: str, key: str):
    if data is None:
        st.warning("Para exportar a PDF instala la librería `fpdf2` (pip install fpdf2).")
        return
    st.download_button(label, data=data, file_name=filename, mime=mime, key=key)


# ──────────────────────────────────────────────────────────────────────────────
# ESTILOS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%);
        padding: 1.4rem 1.8rem; border-radius: 10px; color: white; margin-bottom: 1.2rem;
    }
    .kpi-card {
        background: #ffffff; border: 1px solid #e0e0e0; border-left: 5px solid #2e7d32;
        border-radius: 8px; padding: 0.9rem 1.1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .kpi-value { font-size: 1.8rem; font-weight: 700; color: #1b5e20; }
    .kpi-label { font-size: 0.82rem; color: #555; }
    .badge-bueno { background:#c8e6c9; color:#1b5e20; padding:2px 10px; border-radius:12px; font-weight:600;}
    .badge-regular { background:#fff9c4; color:#7a6500; padding:2px 10px; border-radius:12px; font-weight:600;}
    .badge-malo { background:#ffe0b2; color:#a04b00; padding:2px 10px; border-radius:12px; font-weight:600;}
    .badge-muymalo { background:#ffcdd2; color:#a30000; padding:2px 10px; border-radius:12px; font-weight:600;}
</style>
""", unsafe_allow_html=True)


def badge_estado(estado: str) -> str:
    clase = {"Bueno": "badge-bueno", "Regular": "badge-regular",
             "Malo": "badge-malo", "Muy Malo": "badge-muymalo"}.get(estado, "badge-regular")
    return f'<span class="{clase}">{estado}</span>'


# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR — MENÚ PRINCIPAL (5 módulos)
# ──────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown("## 🛣️ Trochas Ocongate")
st.sidebar.caption("Municipalidad Distrital de Ocongate\nSubgerencia de Gestión de Riesgos y Mantenimiento")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Menú principal",
    ["🏠 INICIO", "🛣️ REGISTRO DE TRAMOS", "📂 CONSULTA DE TRAMOS",
     "📋 FICHA TÉCNICA DE DAÑOS", "📊 REPORTES"],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.caption(f"Sesión: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.sidebar.caption("Proyecto Preprofesional — UTEC 2026-I")


# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO 1 — INICIO
# ══════════════════════════════════════════════════════════════════════════════
if menu == "🏠 INICIO":
    st.markdown("""
    <div class="main-header">
        <h2 style="margin:0;">Sistema de Gestión Preventiva de Trochas Carrozables</h2>
        <p style="margin:0.3rem 0 0 0; opacity:0.9;">
        Municipalidad Distrital de Ocongate · Provincia de Quispicanchi · Región Cusco
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    Esta plataforma apoya a la **Subgerencia de Gestión de Riesgos y Mantenimiento** en el
    registro, inspección técnica y seguimiento del estado de la red vial no pavimentada
    (trochas carrozables) del distrito, siguiendo los criterios del **Manual de Conservación
    Vial MCV-2014 (MTC)** y los formatos técnicos de **Provías Descentralizado**.
    """)

    tramos = df_tramos()
    danos = df_danos()

    total_tramos = len(tramos)
    km_inventariados = round(tramos["longitud_km"].sum(), 2) if not tramos.empty else 0.0

    if not tramos.empty:
        conteo_estado = tramos["estado_actual"].value_counts()
        n_bueno = int(conteo_estado.get("Bueno", 0))
        n_regular = int(conteo_estado.get("Regular", 0))
        n_malo = int(conteo_estado.get("Malo", 0)) + int(conteo_estado.get("Muy Malo", 0))
    else:
        n_bueno = n_regular = n_malo = 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{total_tramos}</div>'
                     f'<div class="kpi-label">Tramos registrados</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{km_inventariados}</div>'
                     f'<div class="kpi-label">Km inventariados</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{n_bueno}</div>'
                     f'<div class="kpi-label">Tramos en buen estado</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{n_malo}</div>'
                     f'<div class="kpi-label">Tramos en mal / muy mal estado</div></div>', unsafe_allow_html=True)

    st.markdown("###")
    colA, colB = st.columns(2)

    with colA:
        st.markdown("##### Distribución de tramos por estado")
        if not tramos.empty:
            fig = px.pie(
                tramos, names="estado_actual", hole=0.45,
                color="estado_actual",
                color_discrete_map={"Bueno": "#43a047", "Regular": "#fdd835",
                                     "Malo": "#fb8c00", "Muy Malo": "#e53935"},
            )
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aún no hay tramos registrados. Ve a **🛣️ Registro de Tramos**.")

    with colB:
        st.markdown("##### Kilómetros por comunidad / sector")
        if not tramos.empty:
            agg = tramos.groupby("comunidad")["longitud_km"].sum().reset_index()
            fig2 = px.bar(agg, x="comunidad", y="longitud_km", color="longitud_km",
                          color_continuous_scale="Greens", text_auto=".1f")
            fig2.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320,
                               yaxis_title="km", xaxis_title="")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sin datos aún.")

    st.markdown("###")
    st.markdown("##### Indicadores rápidos de inspección")
    if not danos.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Daños registrados", len(danos))
        c2.metric("ICT promedio de la red", f"{danos['ict'].mean():.1f} / 100")
        c3.metric("Tramos con prioridad Urgente/Alta",
                  int(danos["prioridad"].isin(["Urgente", "Alta"]).sum()))
    else:
        st.info("Aún no se han registrado fichas de daños. Ve a **📋 Ficha Técnica de Daños**.")


# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO 2 — REGISTRO DE TRAMOS
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "🛣️ REGISTRO DE TRAMOS":
    st.markdown("## 🛣️ Registro de Tramos")
    st.caption("Registra los datos generales, evidencia fotográfica y archivos adjuntos de un tramo vial.")

    with st.form("form_registro_tramo", clear_on_submit=True):
        st.markdown("#### Datos Generales")
        c1, c2, c3 = st.columns(3)
        codigo = c1.text_input("Código de tramo *", placeholder="Ej: M-01")
        nombre = c2.text_input("Nombre del tramo *", placeholder="Ej: Ocongate - Pacchanta")
        comunidad = c3.text_input("Comunidad / Sector *", placeholder="Ej: Pacchanta Baja")

        c4, c5, c6 = st.columns(3)
        distrito = c4.text_input("Distrito *", value="Ocongate")
        provincia = c5.text_input("Provincia *", value="Quispicanchi")
        departamento = c6.text_input("Departamento *", value="Cusco")

        c7, c8, c9 = st.columns(3)
        longitud_km = c7.number_input("Longitud (km) *", min_value=0.0, step=0.1, format="%.2f")
        ancho_m = c8.number_input("Ancho de plataforma (m) *", min_value=0.0, step=0.1, format="%.2f")
        tipo_superficie = c9.selectbox("Tipo de superficie *", TIPOS_SUPERFICIE)

        c10, c11, c12 = st.columns(3)
        estado_actual = c10.selectbox("Estado actual *", ESTADOS_TRAMO)
        responsable = c11.text_input("Responsable de registro *")
        telefono_responsable = c12.text_input("Número telefónico del responsable", placeholder="9XXXXXXXX")

        fecha_registro = st.date_input("Fecha de registro *", value=date.today())

        st.markdown("#### Evidencia Fotográfica")
        f1, f2, f3, f4 = st.columns(4)
        foto_inicio = f1.file_uploader("Foto inicio del tramo", type=["jpg", "jpeg", "png"], key="fi")
        foto_intermedia = f2.file_uploader("Foto intermedia", type=["jpg", "jpeg", "png"], key="fm")
        foto_final = f3.file_uploader("Foto final del tramo", type=["jpg", "jpeg", "png"], key="ff")
        foto_danos = f4.file_uploader("Fotografías de daños", type=["jpg", "jpeg", "png"], key="fd")

        st.markdown("#### Archivos Adjuntos")
        adjunto_pdf = st.file_uploader("Adjuntar PDF (expediente, ficha, plano, etc.)", type=["pdf"])

        enviado = st.form_submit_button("💾 Guardar tramo en la base de datos", use_container_width=True)

    if enviado:
        if not codigo or not nombre or not comunidad or not responsable:
            st.error("Completa los campos obligatorios marcados con *.")
        else:
            try:
                data = {
                    "codigo": codigo, "nombre": nombre, "comunidad": comunidad,
                    "distrito": distrito, "provincia": provincia, "departamento": departamento,
                    "longitud_km": longitud_km, "ancho_m": ancho_m,
                    "tipo_superficie": tipo_superficie, "estado_actual": estado_actual,
                    "responsable": responsable, "telefono_responsable": telefono_responsable,
                    "fecha_registro": fecha_registro.strftime("%Y-%m-%d"),
                    "foto_inicio": img_to_blob(foto_inicio),
                    "foto_intermedia": img_to_blob(foto_intermedia),
                    "foto_final": img_to_blob(foto_final),
                    "foto_danos": img_to_blob(foto_danos),
                    "adjunto_pdf": adjunto_pdf.getvalue() if adjunto_pdf else None,
                    "adjunto_pdf_nombre": adjunto_pdf.name if adjunto_pdf else None,
                }
                insertar_tramo(data)
                st.success(f"✅ Tramo **{codigo} — {nombre}** guardado correctamente en la base de datos.")
            except sqlite3.IntegrityError:
                st.error(f"⚠️ Ya existe un tramo con el código **{codigo}**. Usa un código distinto.")

    st.markdown("---")
    st.caption(f"Tramos registrados actualmente: **{len(df_tramos())}**")


# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO 3 — CONSULTA DE TRAMOS
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "📂 CONSULTA DE TRAMOS":
    st.markdown("## 📂 Consulta de Tramos")
    tramos = df_tramos()

    if tramos.empty:
        st.info("No hay tramos registrados todavía.")
    else:
        st.markdown("#### Filtros")
        f1, f2, f3, f4 = st.columns(4)
        busq_codigo = f1.text_input("Buscar por código")
        busq_nombre = f2.text_input("Buscar por nombre")
        filtro_comunidad = f3.selectbox("Filtrar por comunidad", ["Todas"] + sorted(tramos["comunidad"].dropna().unique().tolist()))
        filtro_estado = f4.selectbox("Filtrar por estado", ["Todos"] + ESTADOS_TRAMO)

        min_km, max_km = float(tramos["longitud_km"].min()), float(tramos["longitud_km"].max())
        if min_km == max_km:
            max_km += 1
        rango_long = st.slider("Filtrar por longitud (km)", min_value=float(min_km), max_value=float(max_km),
                                value=(float(min_km), float(max_km)))

        df_f = tramos.copy()
        if busq_codigo:
            df_f = df_f[df_f["codigo"].str.contains(busq_codigo, case=False, na=False)]
        if busq_nombre:
            df_f = df_f[df_f["nombre"].str.contains(busq_nombre, case=False, na=False)]
        if filtro_comunidad != "Todas":
            df_f = df_f[df_f["comunidad"] == filtro_comunidad]
        if filtro_estado != "Todos":
            df_f = df_f[df_f["estado_actual"] == filtro_estado]
        df_f = df_f[(df_f["longitud_km"] >= rango_long[0]) & (df_f["longitud_km"] <= rango_long[1])]

        st.markdown(f"#### Resultados ({len(df_f)} tramo(s))")
        st.dataframe(
            df_f[["codigo", "nombre", "comunidad", "distrito", "longitud_km", "ancho_m",
                  "tipo_superficie", "estado_actual", "responsable", "fecha_registro"]],
            use_container_width=True, hide_index=True,
        )

        st.markdown("---")
        st.markdown("#### Detalle / Edición / Eliminación de un tramo")
        opciones = {f"{row.codigo} — {row.nombre}": row.id for row in df_f.itertuples()}
        if opciones:
            seleccion = st.selectbox("Selecciona un tramo", list(opciones.keys()))
            tramo_id = opciones[seleccion]

            conn = get_conn()
            row = conn.execute("SELECT * FROM tramos WHERE id=?", (tramo_id,)).fetchone()
            cols = [d[0] for d in conn.execute("SELECT * FROM tramos LIMIT 1").description]
            conn.close()
            tramo_dict = dict(zip(cols, row))

            tabs = st.tabs(["📄 Ficha", "📷 Fotografías", "✏️ Editar", "🗑️ Eliminar", "⬇️ Descargar"])

            with tabs[0]:
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Código:** {tramo_dict['codigo']}")
                    st.write(f"**Nombre:** {tramo_dict['nombre']}")
                    st.write(f"**Comunidad:** {tramo_dict['comunidad']}")
                    st.write(f"**Distrito / Provincia / Dpto:** {tramo_dict['distrito']} / {tramo_dict['provincia']} / {tramo_dict['departamento']}")
                    st.write(f"**Longitud:** {tramo_dict['longitud_km']} km")
                with c2:
                    st.write(f"**Ancho de plataforma:** {tramo_dict['ancho_m']} m")
                    st.write(f"**Tipo de superficie:** {tramo_dict['tipo_superficie']}")
                    st.markdown(f"**Estado actual:** {badge_estado(tramo_dict['estado_actual'])}", unsafe_allow_html=True)
                    st.write(f"**Responsable:** {tramo_dict['responsable']} ({tramo_dict['telefono_responsable'] or 's/n'})")
                    st.write(f"**Fecha de registro:** {tramo_dict['fecha_registro']}")
                if tramo_dict["adjunto_pdf"]:
                    st.download_button("⬇️ Descargar PDF adjunto", data=tramo_dict["adjunto_pdf"],
                                        file_name=tramo_dict["adjunto_pdf_nombre"] or "adjunto.pdf",
                                        mime="application/pdf", key=f"pdf_{tramo_id}")

            with tabs[1]:
                fc1, fc2, fc3, fc4 = st.columns(4)
                for col, label, container in [
                    ("foto_inicio", "Inicio", fc1), ("foto_intermedia", "Intermedia", fc2),
                    ("foto_final", "Final", fc3), ("foto_danos", "Daños", fc4),
                ]:
                    with container:
                        st.caption(label)
                        if tramo_dict[col]:
                            st.image(blob_to_img(tramo_dict[col]), use_container_width=True)
                        else:
                            st.caption("Sin foto")

            with tabs[2]:
                with st.form(f"editar_{tramo_id}"):
                    e1, e2, e3 = st.columns(3)
                    n_codigo = e1.text_input("Código", value=tramo_dict["codigo"])
                    n_nombre = e2.text_input("Nombre", value=tramo_dict["nombre"])
                    n_comunidad = e3.text_input("Comunidad", value=tramo_dict["comunidad"])
                    e4, e5, e6 = st.columns(3)
                    n_distrito = e4.text_input("Distrito", value=tramo_dict["distrito"])
                    n_provincia = e5.text_input("Provincia", value=tramo_dict["provincia"])
                    n_departamento = e6.text_input("Departamento", value=tramo_dict["departamento"])
                    e7, e8, e9 = st.columns(3)
                    n_long = e7.number_input("Longitud (km)", value=float(tramo_dict["longitud_km"]), step=0.1)
                    n_ancho = e8.number_input("Ancho (m)", value=float(tramo_dict["ancho_m"]), step=0.1)
                    n_sup = e9.selectbox("Tipo de superficie", TIPOS_SUPERFICIE,
                                          index=TIPOS_SUPERFICIE.index(tramo_dict["tipo_superficie"]) if tramo_dict["tipo_superficie"] in TIPOS_SUPERFICIE else 0)
                    e10, e11 = st.columns(2)
                    n_estado = e10.selectbox("Estado actual", ESTADOS_TRAMO,
                                              index=ESTADOS_TRAMO.index(tramo_dict["estado_actual"]) if tramo_dict["estado_actual"] in ESTADOS_TRAMO else 0)
                    n_resp = e11.text_input("Responsable", value=tramo_dict["responsable"])
                    n_tel = st.text_input("Teléfono", value=tramo_dict["telefono_responsable"] or "")
                    guardar = st.form_submit_button("💾 Guardar cambios")
                if guardar:
                    actualizar_tramo(tramo_id, {
                        "codigo": n_codigo, "nombre": n_nombre, "comunidad": n_comunidad,
                        "distrito": n_distrito, "provincia": n_provincia, "departamento": n_departamento,
                        "longitud_km": n_long, "ancho_m": n_ancho, "tipo_superficie": n_sup,
                        "estado_actual": n_estado, "responsable": n_resp, "telefono_responsable": n_tel,
                    })
                    st.success("✅ Tramo actualizado. Recarga la página o vuelve a filtrar para ver los cambios.")

            with tabs[3]:
                st.warning("Esta acción eliminará el tramo y todas sus fichas de daño asociadas.")
                if st.button("🗑️ Confirmar eliminación", key=f"del_{tramo_id}"):
                    eliminar_tramo(tramo_id)
                    st.success("Tramo eliminado. Vuelve a cargar la consulta.")

            with tabs[4]:
                ficha_df = pd.DataFrame([tramo_dict]).drop(
                    columns=["foto_inicio", "foto_intermedia", "foto_final", "foto_danos", "adjunto_pdf"])
                st.download_button(
                    "⬇️ Descargar ficha individual (Excel)",
                    data=exportar_excel({"Ficha_Tramo": ficha_df}),
                    file_name=f"Ficha_{tramo_dict['codigo']}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"xlsx_{tramo_id}",
                )


# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO 4 — FICHA TÉCNICA DE DAÑOS
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "📋 FICHA TÉCNICA DE DAÑOS":
    st.markdown("## 📋 Ficha Técnica de Daños en Camino Vecinal")
    st.caption("Formato basado en las fichas 1-B / 1-D de Provías Descentralizado (Itinerario y Daños).")

    tramos = df_tramos()
    if tramos.empty:
        st.info("Primero registra al menos un tramo en **🛣️ Registro de Tramos**.")
    else:
        opciones = {f"{row.codigo} — {row.nombre} ({row.longitud_km} km)": (row.id, row.longitud_km)
                    for row in tramos.itertuples()}
        seleccion = st.selectbox("Tramo a inspeccionar", list(opciones.keys()))
        tramo_id, longitud_tramo = opciones[seleccion]

        with st.form("form_ficha_dano", clear_on_submit=True):
            st.markdown("#### Progresiva y ubicación del daño")
            c1, c2, c3 = st.columns(3)
            prog_inicial = c1.number_input("Progresiva inicial (km)", min_value=0.0, step=0.05, format="%.3f")
            prog_final = c2.number_input("Progresiva final (km)", min_value=0.0, step=0.05, format="%.3f")
            longitud_afectada = c3.number_input("Longitud afectada (km)", min_value=0.0, step=0.01, format="%.3f")

            st.markdown("#### Características del daño")
            c4, c5, c6 = st.columns(3)
            tipo_dano = c4.selectbox("Tipo de daño", TIPOS_DANO)
            clase_densidad = c5.selectbox("Clase de densidad", CLASES_DENSIDAD,
                                           help="Solo aplica obligatoriamente si el tipo de daño es 'Baches o Huecos'.")
            fecha_inspeccion = c6.date_input("Fecha de inspección", value=date.today())

            observaciones = st.text_area("Observaciones técnicas", placeholder="Describe lo observado en campo...")
            foto_dano = st.file_uploader("Fotografía del daño", type=["jpg", "jpeg", "png"])

            calcular = st.form_submit_button("⚙️ Calcular clasificación automática y guardar", use_container_width=True)

        if calcular:
            falla = clasificar_falla(tipo_dano)
            peso = PESO_DANO.get(tipo_dano, 1)
            gravedad = calcular_gravedad(longitud_afectada, longitud_tramo, peso)
            estado_tramo_calc = calcular_estado(gravedad)
            transitabilidad = calcular_transitabilidad(estado_tramo_calc)
            prioridad = calcular_prioridad(estado_tramo_calc, transitabilidad)
            tiempo_rep = calcular_tiempo_reparacion(tipo_dano, max(longitud_afectada, 0.05))
            ict = calcular_ict(gravedad, clase_densidad, falla)
            pct_deterioro = round(100 - ict, 1)
            necesidad = calcular_necesidad_intervencion(prioridad)

            data = {
                "tramo_id": tramo_id, "progresiva_inicial": prog_inicial, "progresiva_final": prog_final,
                "longitud_afectada": longitud_afectada, "tipo_dano": tipo_dano, "tipo_falla": falla,
                "nivel_gravedad": gravedad, "clase_densidad": clase_densidad, "estado_tramo": estado_tramo_calc,
                "transitabilidad": transitabilidad, "necesidad_intervencion": necesidad,
                "tiempo_estimado_dias": tiempo_rep, "fecha_inspeccion": fecha_inspeccion.strftime("%Y-%m-%d"),
                "observaciones": observaciones, "ict": ict, "pct_deterioro": pct_deterioro,
                "prioridad": prioridad, "foto_dano": img_to_blob(foto_dano),
            }
            insertar_dano(data)

            st.success("✅ Ficha de daño registrada. Resultado de la clasificación automática:")
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Tipo de falla", falla)
            r2.metric("Nivel de gravedad", gravedad)
            r3.markdown(f"**Estado del tramo**<br>{badge_estado(estado_tramo_calc)}", unsafe_allow_html=True)
            r4.metric("Transitabilidad", transitabilidad)

            r5, r6, r7, r8 = st.columns(4)
            r5.metric("Prioridad de intervención", prioridad)
            r6.metric("Tiempo estimado de reparación", f"{tiempo_rep} días")
            r7.metric("ICT (Índice de Condición)", f"{ict} / 100")
            r8.metric("% de deterioro", f"{pct_deterioro}%")
            st.info(f"**Necesidad de intervención:** {necesidad}")

        st.markdown("---")
        st.markdown("#### Histórico de fichas de daños registradas")
        danos = df_danos()
        if danos.empty:
            st.caption("Aún no hay fichas registradas.")
        else:
            cols_show = ["codigo_tramo", "nombre_tramo", "progresiva_inicial", "progresiva_final",
                         "longitud_afectada", "tipo_dano", "tipo_falla", "nivel_gravedad",
                         "estado_tramo", "transitabilidad", "prioridad", "ict", "pct_deterioro",
                         "tiempo_estimado_dias", "fecha_inspeccion"]
            st.dataframe(danos[cols_show].rename(columns={
                "codigo_tramo": "Código", "nombre_tramo": "Tramo", "progresiva_inicial": "Prog. Inicial",
                "progresiva_final": "Prog. Final", "longitud_afectada": "Long. Afectada (km)",
                "tipo_dano": "Tipo de Daño", "tipo_falla": "Falla", "nivel_gravedad": "Gravedad",
                "estado_tramo": "Estado", "transitabilidad": "Transitabilidad", "prioridad": "Prioridad",
                "ict": "ICT", "pct_deterioro": "% Deterioro", "tiempo_estimado_dias": "Días Rep.",
                "fecha_inspeccion": "Fecha",
            }), use_container_width=True, hide_index=True)

            st.markdown("##### 🏆 Ranking de tramos críticos (menor ICT)")
            ranking = danos.groupby(["codigo_tramo", "nombre_tramo"])["ict"].mean().reset_index()
            ranking = ranking.sort_values("ict").rename(columns={"ict": "ICT promedio"})
            ranking.index = range(1, len(ranking) + 1)
            st.dataframe(ranking, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO 5 — REPORTES
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "📊 REPORTES":
    st.markdown("## 📊 Reportes")
    tramos = df_tramos()
    danos = df_danos()

    if tramos.empty:
        st.info("No hay datos suficientes para generar reportes todavía.")
    else:
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📦 Inventario y Estado", "⚠️ Daños", "💰 Costos e Intervenciones", "⬇️ Exportar"])

        # ---- TAB 1: Inventario y estado de la red ----
        with tab1:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("##### Estado de la red vial (N° de tramos)")
                fig = px.bar(tramos["estado_actual"].value_counts().reset_index(),
                             x="estado_actual", y="count",
                             color="estado_actual",
                             color_discrete_map={"Bueno": "#43a047", "Regular": "#fdd835",
                                                  "Malo": "#fb8c00", "Muy Malo": "#e53935"},
                             text_auto=True)
                fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="N° tramos", height=340)
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.markdown("##### Kilómetros afectados por estado")
                km_estado = tramos.groupby("estado_actual")["longitud_km"].sum().reset_index()
                fig2 = px.pie(km_estado, names="estado_actual", values="longitud_km", hole=0.4,
                              color="estado_actual",
                              color_discrete_map={"Bueno": "#43a047", "Regular": "#fdd835",
                                                   "Malo": "#fb8c00", "Muy Malo": "#e53935"})
                fig2.update_layout(height=340)
                st.plotly_chart(fig2, use_container_width=True)

            st.markdown("##### Inventario completo de tramos")
            st.dataframe(tramos, use_container_width=True, hide_index=True)

        # ---- TAB 2: Daños ----
        with tab2:
            if danos.empty:
                st.info("No hay fichas de daños registradas aún.")
            else:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("##### Daños por tipo")
                    fig3 = px.bar(danos["tipo_dano"].value_counts().reset_index(),
                                  x="tipo_dano", y="count", color="count",
                                  color_continuous_scale="Reds", text_auto=True)
                    fig3.update_layout(xaxis_title="", yaxis_title="N° de casos", height=360)
                    st.plotly_chart(fig3, use_container_width=True)
                with c2:
                    st.markdown("##### Daños por nivel de gravedad")
                    fig4 = px.pie(danos, names="nivel_gravedad", hole=0.4,
                                  color="nivel_gravedad",
                                  color_discrete_map={"Sin Deterioro": "#43a047", "Leve": "#9ccc65",
                                                       "Moderada": "#fb8c00", "Severa": "#e53935"})
                    fig4.update_layout(height=360)
                    st.plotly_chart(fig4, use_container_width=True)

                st.markdown("##### Histograma de % de deterioro (ICT invertido)")
                fig5 = px.histogram(danos, x="pct_deterioro", nbins=10, color_discrete_sequence=["#c62828"])
                fig5.update_layout(xaxis_title="% de deterioro", yaxis_title="Frecuencia", height=320)
                st.plotly_chart(fig5, use_container_width=True)

                st.markdown("##### Kilómetros afectados por tipo de daño")
                km_dano = danos.groupby("tipo_dano")["longitud_afectada"].sum().reset_index()
                fig6 = px.bar(km_dano.sort_values("longitud_afectada", ascending=False),
                              x="tipo_dano", y="longitud_afectada", color="longitud_afectada",
                              color_continuous_scale="Oranges", text_auto=".2f")
                fig6.update_layout(xaxis_title="", yaxis_title="km afectados", height=340)
                st.plotly_chart(fig6, use_container_width=True)

                st.markdown("##### Tramos críticos (Prioridad Urgente / Alta)")
                criticos = danos[danos["prioridad"].isin(["Urgente", "Alta"])][
                    ["codigo_tramo", "nombre_tramo", "tipo_dano", "estado_tramo",
                     "transitabilidad", "prioridad", "ict", "tiempo_estimado_dias"]]
                st.dataframe(criticos, use_container_width=True, hide_index=True)

        # ---- TAB 3: Costos / necesidades de mantenimiento ----
        with tab3:
            if danos.empty:
                st.info("No hay fichas de daños registradas aún.")
            else:
                COSTO_REFERENCIAL_KM = {  # S/. por km — referencial MCV-2014 / benchmarks de campo
                    "Deformación": 9500, "Erosión": 11000, "Baches o Huecos": 14500,
                    "Encalaminado": 8000, "Lodazal": 17500, "Cruce de Agua": 22000,
                    "Hundimiento": 26000, "Pérdida de Plataforma": 31000,
                    "Deslizamiento": 35000, "Falla de Drenaje": 19500,
                }
                danos["costo_estimado"] = danos.apply(
                    lambda r: round(r["longitud_afectada"] * COSTO_REFERENCIAL_KM.get(r["tipo_dano"], 12000), 0),
                    axis=1,
                )
                c1, c2, c3 = st.columns(3)
                c1.metric("Costo estimado total de intervención", f"S/. {danos['costo_estimado'].sum():,.0f}")
                c2.metric("Km totales afectados", f"{danos['longitud_afectada'].sum():.2f} km")
                c3.metric("Días totales estimados de reparación", f"{danos['tiempo_estimado_dias'].sum():.0f} días")

                st.markdown("##### Costo estimado por tipo de daño")
                costo_tipo = danos.groupby("tipo_dano")["costo_estimado"].sum().reset_index()
                fig7 = px.bar(costo_tipo.sort_values("costo_estimado", ascending=False),
                              x="tipo_dano", y="costo_estimado", color="costo_estimado",
                              color_continuous_scale="Blues", text_auto=".2s")
                fig7.update_layout(xaxis_title="", yaxis_title="S/.", height=340)
                st.plotly_chart(fig7, use_container_width=True)

                st.markdown("##### Necesidades de mantenimiento por tramo")
                necesidades = danos.groupby(["codigo_tramo", "nombre_tramo", "necesidad_intervencion"]).size().reset_index(name="N° fichas")
                st.dataframe(necesidades, use_container_width=True, hide_index=True)

        # ---- TAB 4: Exportar ----
        with tab4:
            st.markdown("#### Exportar reportes")
            dfs_excel = {"Inventario_Tramos": tramos}
            if not danos.empty:
                dfs_excel["Fichas_Danos"] = danos.drop(columns=["foto_dano"], errors="ignore")
                dfs_excel["Ranking_Criticos"] = (
                    danos.groupby(["codigo_tramo", "nombre_tramo"])["ict"].mean()
                    .reset_index().sort_values("ict").rename(columns={"ict": "ICT_promedio"})
                )

            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    "⬇️ Descargar reporte completo (Excel)",
                    data=exportar_excel(dfs_excel),
                    file_name=f"Reporte_Trochas_Ocongate_{date.today().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            with c2:
                pdf_bytes = exportar_pdf_resumen(
                    "Reporte de Inventario — Trochas Carrozables, Ocongate",
                    tramos[["codigo", "nombre", "comunidad", "longitud_km", "estado_actual"]],
                    texto_intro=f"Total de tramos: {len(tramos)} | Km inventariados: {tramos['longitud_km'].sum():.2f} km",
                )
                download_button_bytes(
                    pdf_bytes,
                    f"Reporte_Trochas_Ocongate_{date.today().strftime('%Y%m%d')}.pdf",
                    "⬇️ Descargar reporte resumen (PDF)",
                    "application/pdf",
                    "pdf_main",
                )


st.markdown("---")
st.caption("Plataforma desarrollada como demostración técnica — Proyecto Preprofesional UTEC 2026-I · "
           "Frank Puma Mamani (202220055) · Municipalidad Distrital de Ocongate.")
