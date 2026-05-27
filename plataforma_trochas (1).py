"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  PLATAFORMA WEB — GESTIÓN DE TROCHAS CARROZABLES                           ║
║  Sistema de Registro, Visualización y Gestión Técnica de Tramos Viales     ║
║  Municipalidad Distrital de Ocongate — Quispicanchi, Cusco, Perú           ║
║                                                                              ║
║  Autor  : Frank Puma Mamani | Código: 202220055                             ║
║  Curso  : Proyecto Preprofesional — Teoría 7, UTEC 2026                    ║
║  Docente: Mg. Fernandez Choquepuma, Miguel Ángel                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

INSTALACIÓN:
    pip install streamlit plotly pandas pillow

EJECUCIÓN:
    streamlit run plataforma_trochas.py

MÓDULOS DE LA PLATAFORMA:
    1. Dashboard  — Resumen ejecutivo y métricas globales
    2. Registro   — Registrar nuevo tramo vial
    3. Consulta   — Ver y filtrar todos los tramos registrados
    4. Detalle    — Ficha técnica completa de un tramo
    5. Mantenimiento — Historial y planificación de intervenciones
    6. Reportes   — Análisis estadístico y gráficas exportables
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime
import json
import random
import math

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN GLOBAL
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Plataforma Trochas — Ocongate",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paleta institucional ──────────────────────────────────────────────────────
PAL = {
    "navy":    "#1B3A6B",
    "blue":    "#2563A8",
    "sky":     "#D6E4F0",
    "gold":    "#E8A020",
    "green":   "#1A7A4A",
    "lgreen":  "#E9F7EF",
    "red":     "#C0392B",
    "lred":    "#FDECEA",
    "orange":  "#D35400",
    "lorange": "#FEF5E7",
    "gray":    "#F4F6FA",
    "white":   "#FFFFFF",
    "text":    "#1A1A2E",
    "muted":   "#5A6478",
    "line":    "#CBD5E1",
}

# ══════════════════════════════════════════════════════════════════════════════
# CSS GLOBAL
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {{
    --navy:   {PAL['navy']};
    --blue:   {PAL['blue']};
    --sky:    {PAL['sky']};
    --gold:   {PAL['gold']};
    --green:  {PAL['green']};
    --lgreen: {PAL['lgreen']};
    --red:    {PAL['red']};
    --lred:   {PAL['lred']};
    --orange: {PAL['orange']};
    --lorange:{PAL['lorange']};
    --gray:   {PAL['gray']};
    --text:   {PAL['text']};
    --muted:  {PAL['muted']};
    --line:   {PAL['line']};
}}

html, body, [class*="css"] {{
    font-family: 'Sora', sans-serif !important;
}}

/* Ocultar elementos Streamlit */
#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: var(--navy) !important;
    min-width: 240px;
}}
[data-testid="stSidebar"] * {{
    color: rgba(255,255,255,0.85) !important;
    font-family: 'Sora', sans-serif !important;
}}
[data-testid="stSidebarNav"] {{
    padding-top: 0 !important;
}}

/* Main area */
.main .block-container {{
    padding: 1.5rem 2rem;
    max-width: 1280px;
}}

/* Metric cards */
.kpi-card {{
    background: #fff;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    border-left: 4px solid var(--navy);
    box-shadow: 0 2px 10px rgba(27,58,107,0.07);
    height: 100%;
}}
.kpi-card.green  {{ border-left-color: var(--green); }}
.kpi-card.red    {{ border-left-color: var(--red); }}
.kpi-card.orange {{ border-left-color: var(--orange); }}
.kpi-card.gold   {{ border-left-color: var(--gold); }}
.kpi-label {{
    font-size: 0.7rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 0.3rem;
}}
.kpi-value {{
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--navy);
    line-height: 1;
    margin-bottom: 0.3rem;
}}
.kpi-sub {{
    font-size: 0.78rem;
    color: var(--muted);
}}

/* Page header */
.page-header {{
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1.2rem 1.8rem;
    background: linear-gradient(135deg, var(--navy) 0%, var(--blue) 100%);
    border-radius: 12px;
    margin-bottom: 1.5rem;
    color: white;
}}
.page-header-icon {{
    font-size: 2rem;
    opacity: 0.9;
}}
.page-header-title {{
    font-size: 1.3rem;
    font-weight: 700;
    color: white;
    margin: 0;
}}
.page-header-sub {{
    font-size: 0.82rem;
    color: rgba(214,228,240,0.85);
    margin: 0;
}}

/* Sección titles */
.section-title {{
    font-size: 1rem;
    font-weight: 600;
    color: var(--navy);
    padding-bottom: 0.4rem;
    border-bottom: 2px solid var(--gold);
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}

/* Badge de estado */
.badge {{
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 100px;
    font-size: 0.72rem;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
}}
.badge-bueno    {{ background: var(--lgreen); color: var(--green); }}
.badge-regular  {{ background: var(--lorange); color: var(--orange); }}
.badge-malo     {{ background: var(--lred); color: var(--red); }}
.badge-critico  {{ background: var(--red); color: #fff; }}

/* Ficha técnica */
.ficha-row {{
    display: flex;
    border-bottom: 1px solid var(--line);
    padding: 0.55rem 0;
    align-items: flex-start;
}}
.ficha-row:last-child {{ border-bottom: none; }}
.ficha-key {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: var(--muted);
    min-width: 180px;
    padding-top: 0.05rem;
    flex-shrink: 0;
}}
.ficha-val {{
    font-size: 0.85rem;
    color: var(--text);
    font-weight: 500;
    flex: 1;
}}

/* Tarjeta de tramo */
.tramo-card {{
    background: #fff;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    border: 1px solid var(--line);
    margin-bottom: 0.8rem;
    transition: box-shadow 0.2s;
    cursor: pointer;
}}
.tramo-card:hover {{
    box-shadow: 0 4px 16px rgba(27,58,107,0.1);
    border-color: var(--blue);
}}
.tramo-card-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
}}
.tramo-name {{
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--navy);
}}
.tramo-meta {{
    font-size: 0.78rem;
    color: var(--muted);
    margin-top: 0.15rem;
}}
.tramo-stats {{
    display: flex;
    gap: 1.2rem;
    margin-top: 0.6rem;
    flex-wrap: wrap;
}}
.tramo-stat {{
    display: flex;
    flex-direction: column;
}}
.tramo-stat-label {{
    font-size: 0.65rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.07em;
    font-family: 'JetBrains Mono', monospace;
}}
.tramo-stat-value {{
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--text);
    font-family: 'JetBrains Mono', monospace;
}}

/* Barra de deterioro */
.deterioro-bar {{
    height: 8px;
    border-radius: 100px;
    background: var(--line);
    overflow: hidden;
    margin-top: 0.5rem;
}}
.deterioro-fill {{
    height: 100%;
    border-radius: 100px;
}}

/* Historial de mantenimiento */
.mant-item {{
    display: flex;
    gap: 1rem;
    padding: 0.8rem 0;
    border-bottom: 1px solid var(--line);
}}
.mant-fecha {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: var(--muted);
    min-width: 90px;
    padding-top: 0.1rem;
}}
.mant-tipo {{
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--navy);
}}
.mant-desc {{
    font-size: 0.8rem;
    color: var(--muted);
    margin-top: 0.15rem;
}}

/* Sidebar logo */
.sidebar-logo {{
    padding: 1.2rem 1rem 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.12);
    margin-bottom: 0.5rem;
}}
.sidebar-logo-title {{
    font-size: 0.95rem;
    font-weight: 700;
    color: white;
    margin-bottom: 0.15rem;
}}
.sidebar-logo-sub {{
    font-size: 0.7rem;
    color: rgba(214,228,240,0.65);
    line-height: 1.4;
}}

/* Alerta */
.alerta-box {{
    background: var(--lred);
    border-left: 4px solid var(--red);
    border-radius: 0 8px 8px 0;
    padding: 0.8rem 1rem;
    margin-bottom: 0.6rem;
    font-size: 0.82rem;
    color: #5B0000;
}}
.alerta-box.warn {{
    background: var(--lorange);
    border-left-color: var(--orange);
    color: #4A1C00;
}}
.alerta-box.ok {{
    background: var(--lgreen);
    border-left-color: var(--green);
    color: #0B3020;
}}

/* Form labels */
.stSelectbox label, .stTextInput label, .stNumberInput label,
.stTextArea label, .stDateInput label, .stSlider label {{
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: var(--navy) !important;
}}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# BASE DE DATOS EN MEMORIA (session_state)
# ══════════════════════════════════════════════════════════════════════════════
def init_data():
    """Inicializa los datos demo si no existen en session_state."""
    if "tramos" not in st.session_state:
        st.session_state.tramos = [
            {
                "id": "TR-001",
                "nombre": "Trocha Pacchanta Alta — UPIS",
                "comunidad": "Pacchanta Alta",
                "distrito": "Ocongate",
                "provincia": "Quispicanchi",
                "longitud_km": 21.1,
                "ancho_m": 4.5,
                "altitud_msnm": 4250,
                "superficie": "Afirmado",
                "nivel_deterioro": "Malo",
                "iec": 32,  # Índice de Estado del Camino 0-100
                "accesibilidad": "Estacional (cerrado dic–mar)",
                "cantera_cercana": "Sí — Cantera Pacchanta (2.3 km)",
                "fuente_lastre": "Río Ausangate (material aluvial)",
                "drenaje": "Deficiente — cunetas colmatadas",
                "señalizacion": "Ausente",
                "puentes": 2,
                "badenes": 5,
                "tipo_intervencion_recomendada": "Periódico urgente",
                "costo_estimado_rutinario": 184000,
                "costo_estimado_periodico": 336000,
                "fecha_ultima_intervencion": "2023-06-15",
                "foto_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/Ausangate_trek_dirt_road.jpg/640px-Ausangate_trek_dirt_road.jpg",
                "observaciones": "Tramo con mayor deterioro del distrito. Baches profundos >20 cm. Erosión severa en km 8–12. Requiere intervención periódica antes de temporada de lluvias.",
                "latitud": -13.6458,
                "longitud": -71.1234,
                "historial": [
                    {"fecha": "2023-06-15", "tipo": "Correctivo", "costo": 519635, "ejecutor": "Contratista Andes Viales SAC", "descripcion": "Mantenimiento periódico mecanizado con aporte de material. Reconformación general."},
                    {"fecha": "2021-03-20", "tipo": "Correctivo", "costo": 320000, "ejecutor": "Subgerencia de Mantenimiento", "descripcion": "Bacheo de emergencia post-temporada de lluvias. Limpieza de derrumbes."},
                ],
            },
            {
                "id": "TR-002",
                "nombre": "Trocha Mahuayani — Ocongate",
                "comunidad": "Mahuayani",
                "distrito": "Ocongate",
                "provincia": "Quispicanchi",
                "longitud_km": 15.0,
                "ancho_m": 3.8,
                "altitud_msnm": 3900,
                "superficie": "Tierra compactada",
                "nivel_deterioro": "Regular",
                "iec": 55,
                "accesibilidad": "Todo el año (con precaución en lluvias)",
                "cantera_cercana": "No — material debe traerse de Ocongate (18 km)",
                "fuente_lastre": "No disponible en radio de 5 km",
                "drenaje": "Regular — cunetas con vegetación",
                "señalizacion": "Parcial (2 hitos)",
                "puentes": 1,
                "badenes": 3,
                "tipo_intervencion_recomendada": "Rutinario preventivo",
                "costo_estimado_rutinario": 169575,
                "costo_estimado_periodico": 399000,
                "fecha_ultima_intervencion": "2023-09-10",
                "foto_url": "",
                "observaciones": "Tramo en condición regular. Cunetas requieren limpieza. Superficie presenta ondulaciones menores. Prioridad media.",
                "latitud": -13.6200,
                "longitud": -71.0980,
                "historial": [
                    {"fecha": "2023-09-10", "tipo": "Correctivo", "costo": 140125, "ejecutor": "Subgerencia de Mantenimiento", "descripcion": "Mantenimiento periódico no mecanizado. Limpieza de cunetas y bacheo menor."},
                ],
            },
            {
                "id": "TR-003",
                "nombre": "Trocha Palcca Central — Palcca Alta",
                "comunidad": "Palcca",
                "distrito": "Ocongate",
                "provincia": "Quispicanchi",
                "longitud_km": 30.0,
                "ancho_m": 4.0,
                "altitud_msnm": 4100,
                "superficie": "Afirmado",
                "nivel_deterioro": "Malo",
                "iec": 28,
                "accesibilidad": "Restringido (requiere 4x4)",
                "cantera_cercana": "Sí — Cantera Palcca (1.8 km)",
                "fuente_lastre": "Quebrada Palcca (material disponible)",
                "drenaje": "Muy deficiente — sin cunetas en 40% del tramo",
                "señalizacion": "Ausente",
                "puentes": 4,
                "badenes": 8,
                "tipo_intervencion_recomendada": "Periódico urgente",
                "costo_estimado_rutinario": 405000,
                "costo_estimado_periodico": 630000,
                "fecha_ultima_intervencion": "2023-11-20",
                "foto_url": "",
                "observaciones": "Tramo más largo y costoso. 4 puentes requieren revisión estructural. Sin drenaje adecuado en 12 km. Mayor sobrecosto acumulado del distrito: S/. 443 118.",
                "latitud": -13.5900,
                "longitud": -71.1100,
                "historial": [
                    {"fecha": "2023-11-20", "tipo": "Correctivo", "costo": 848118, "ejecutor": "Contratista Vialec SRL", "descripcion": "Mantenimiento periódico mayor. Reposición de afirmado en 18 km. Reconformación de plataforma."},
                    {"fecha": "2020-08-05", "tipo": "Correctivo", "costo": 520000, "ejecutor": "Subgerencia de Mantenimiento", "descripcion": "Rehabilitación parcial post-huayco. Reparación de badenes y limpieza de cauce."},
                ],
            },
            {
                "id": "TR-004",
                "nombre": "Trocha Pacchanta Baja — Cruce UPIS",
                "comunidad": "Pacchanta Baja",
                "distrito": "Ocongate",
                "provincia": "Quispicanchi",
                "longitud_km": 18.5,
                "ancho_m": 4.2,
                "altitud_msnm": 3800,
                "superficie": "Afirmado",
                "nivel_deterioro": "Regular",
                "iec": 48,
                "accesibilidad": "Todo el año",
                "cantera_cercana": "Sí — Cantera Chocco (3.5 km)",
                "fuente_lastre": "Río Urubamba tributario (5 km)",
                "drenaje": "Regular — cunetas parcialmente funcionales",
                "señalizacion": "Parcial (5 hitos, 2 señales de curva)",
                "puentes": 2,
                "badenes": 6,
                "tipo_intervencion_recomendada": "Rutinario preventivo",
                "costo_estimado_rutinario": 238625,
                "costo_estimado_periodico": 483000,
                "fecha_ultima_intervencion": "2023-08-30",
                "foto_url": "",
                "observaciones": "Tramo en uso frecuente por transportistas y productores. Condición regular con tendencia al deterioro. Requiere rutinario antes de lluvias.",
                "latitud": -13.6600,
                "longitud": -71.0800,
                "historial": [
                    {"fecha": "2023-08-30", "tipo": "Correctivo", "costo": 640734, "ejecutor": "Contratista Vías Andinas EIRL", "descripcion": "Mantenimiento de infraestructura vial. Puente Chocco – Cruce UPIS. Reposición de badenes."},
                ],
            },
            {
                "id": "TR-005",
                "nombre": "Trocha Ausangate — Comunidad",
                "comunidad": "Ausangate",
                "distrito": "Ocongate",
                "provincia": "Quispicanchi",
                "longitud_km": 12.0,
                "ancho_m": 3.5,
                "altitud_msnm": 4600,
                "superficie": "Tierra natural",
                "nivel_deterioro": "Bueno",
                "iec": 72,
                "accesibilidad": "Estacional (solo épocas secas)",
                "cantera_cercana": "No — zona protegida Ausangate",
                "fuente_lastre": "Sin fuentes cercanas disponibles",
                "drenaje": "Bueno — pendiente natural favorece drenaje",
                "señalizacion": "Parcial (señales de altitud)",
                "puentes": 0,
                "badenes": 2,
                "tipo_intervencion_recomendada": "Rutinario preventivo",
                "costo_estimado_rutinario": 94929,
                "costo_estimado_periodico": 220000,
                "fecha_ultima_intervencion": "2024-02-14",
                "foto_url": "",
                "observaciones": "Tramo a mayor altitud. Zona turística (cerro Ausangate). Condición buena. Priorizar mantenimiento rutinario para conservar.",
                "latitud": -13.7800,
                "longitud": -71.2200,
                "historial": [
                    {"fecha": "2024-02-14", "tipo": "Correctivo", "costo": 94929, "ejecutor": "Subgerencia de Mantenimiento", "descripcion": "Mantenimiento rutinario: reconformación de cunetas, limpieza y bacheo menor."},
                ],
            },
        ]

    if "mantenimientos_programados" not in st.session_state:
        st.session_state.mantenimientos_programados = [
            {"tramo_id": "TR-001", "tipo": "Periódico", "fecha_prog": "2025-04-15", "estado": "Pendiente", "responsable": "Subgerencia", "costo_est": 336000},
            {"tramo_id": "TR-003", "tipo": "Periódico", "fecha_prog": "2025-05-01", "estado": "Pendiente", "responsable": "Contratista", "costo_est": 630000},
            {"tramo_id": "TR-002", "tipo": "Rutinario", "fecha_prog": "2025-04-20", "estado": "En ejecución", "responsable": "Subgerencia", "costo_est": 169575},
            {"tramo_id": "TR-004", "tipo": "Rutinario", "fecha_prog": "2025-05-10", "estado": "Pendiente", "responsable": "Subgerencia", "costo_est": 238625},
            {"tramo_id": "TR-005", "tipo": "Rutinario", "fecha_prog": "2025-06-01", "estado": "Programado", "responsable": "Subgerencia", "costo_est": 94929},
        ]

    if "pagina" not in st.session_state:
        st.session_state.pagina = "Dashboard"

    if "tramo_seleccionado" not in st.session_state:
        st.session_state.tramo_seleccionado = None


init_data()

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def color_deterioro(nivel):
    return {"Bueno": PAL["green"], "Regular": PAL["orange"],
            "Malo": PAL["red"], "Crítico": "#7D0000"}.get(nivel, PAL["muted"])

def badge_deterioro(nivel):
    cls = {"Bueno": "badge-bueno", "Regular": "badge-regular",
           "Malo": "badge-malo", "Crítico": "badge-critico"}.get(nivel, "")
    return f'<span class="badge {cls}">{nivel}</span>'

def barra_iec(iec, w=200):
    color = PAL["green"] if iec >= 70 else PAL["orange"] if iec >= 40 else PAL["red"]
    return f"""
    <div style="display:flex; align-items:center; gap:8px;">
        <div style="width:{w}px; height:8px; border-radius:100px;
                    background:{PAL['line']}; overflow:hidden; flex-shrink:0;">
            <div style="width:{iec}%; height:100%; border-radius:100px;
                        background:{color};"></div>
        </div>
        <span style="font-family:'JetBrains Mono',monospace; font-size:0.78rem;
                     color:{color}; font-weight:600;">{iec}%</span>
    </div>"""

def get_tramo(tid):
    for t in st.session_state.tramos:
        if t["id"] == tid:
            return t
    return None


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div style="font-size:1.8rem; margin-bottom:0.5rem;">🏔️</div>
        <div class="sidebar-logo-title">Plataforma Trochas</div>
        <div class="sidebar-logo-sub">
            Municipalidad Distrital de Ocongate<br>
            Quispicanchi, Cusco, Perú
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Navegación**")
    paginas = {
        "📊  Dashboard":         "Dashboard",
        "➕  Registrar Tramo":   "Registro",
        "🗂️  Consultar Tramos":  "Consulta",
        "📋  Ficha Técnica":     "Detalle",
        "🔧  Mantenimiento":     "Mantenimiento",
        "📈  Reportes":          "Reportes",
    }

    for label, pid in paginas.items():
        active = st.session_state.pagina == pid
        if st.button(
            label,
            key=f"nav_{pid}",
            use_container_width=True,
            type="primary" if active else "secondary",
        ):
            st.session_state.pagina = pid
            st.rerun()

    st.markdown("---")
    st.markdown(f"""
    <div style="font-size:0.7rem; color:rgba(214,228,240,0.5); line-height:1.6;">
        <strong style="color:rgba(255,255,255,0.6);">Proyecto Preprofesional</strong><br>
        Frank Puma Mamani · 202220055<br>
        UTEC 2026-I
    </div>
    """, unsafe_allow_html=True)

    # Mini-resumen en sidebar
    n_tramos = len(st.session_state.tramos)
    n_malos  = sum(1 for t in st.session_state.tramos if t["nivel_deterioro"] in ("Malo","Crítico"))
    km_total = sum(t["longitud_km"] for t in st.session_state.tramos)
    st.markdown("---")
    st.markdown(f"""
    <div style="font-size:0.72rem; color:rgba(214,228,240,0.65);">
        <div style="margin-bottom:4px;">Tramos registrados: <b style="color:white;">{n_tramos}</b></div>
        <div style="margin-bottom:4px;">Km totales: <b style="color:white;">{km_total:.1f} km</b></div>
        <div>Tramos en mal estado: <b style="color:#FF7F7F;">{n_malos}</b></div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.pagina == "Dashboard":

    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">📊</div>
        <div>
            <div class="page-header-title">Dashboard — Resumen Ejecutivo</div>
            <div class="page-header-sub">
                Estado actual de la red vial de trochas carrozables · Ocongate, Quispicanchi
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPIs globales ────────────────────────────────────────────────────────
    tramos = st.session_state.tramos
    n = len(tramos)
    km_tot = sum(t["longitud_km"] for t in tramos)
    pct_prev = 0  # línea base
    costo_tot = sum(sum(h["costo"] for h in t["historial"]) for t in tramos)
    iec_prom = round(sum(t["iec"] for t in tramos) / n)

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">Tramos registrados</div>
            <div class="kpi-value">{n}</div>
            <div class="kpi-sub">{km_tot:.1f} km en total</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="kpi-card red">
            <div class="kpi-label">Estado promedio (IEC)</div>
            <div class="kpi-value">{iec_prom}%</div>
            <div class="kpi-sub">Índice de Estado del Camino</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        malos = sum(1 for t in tramos if t["nivel_deterioro"] in ("Malo","Crítico"))
        st.markdown(f"""<div class="kpi-card orange">
            <div class="kpi-label">Tramos en mal estado</div>
            <div class="kpi-value">{malos} / {n}</div>
            <div class="kpi-sub">Requieren intervención urgente</div>
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="kpi-card red">
            <div class="kpi-label">% Intervenciones preventivas</div>
            <div class="kpi-value">0%</div>
            <div class="kpi-sub">Línea base — 100% correctivo</div>
        </div>""", unsafe_allow_html=True)
    with k5:
        costo_km = round(costo_tot / km_tot) if km_tot else 0
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">Costo promedio / km</div>
            <div class="kpi-value">S/{costo_km:,}</div>
            <div class="kpi-sub">Meta: ≤ S/. 11 500/km</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Gráficas ─────────────────────────────────────────────────────────────
    col_g1, col_g2, col_g3 = st.columns([1, 1, 1])

    with col_g1:
        st.markdown('<div class="section-title">📉 Estado de la red vial</div>', unsafe_allow_html=True)
        counts = {"Bueno": 0, "Regular": 0, "Malo": 0, "Crítico": 0}
        for t in tramos:
            counts[t["nivel_deterioro"]] = counts.get(t["nivel_deterioro"], 0) + 1
        fig_pie = go.Figure(go.Pie(
            labels=list(counts.keys()),
            values=list(counts.values()),
            hole=0.55,
            marker=dict(colors=[PAL["green"], PAL["orange"], PAL["red"], "#7D0000"]),
            textinfo="percent+label",
            textfont=dict(family="Sora", size=11),
            hovertemplate="%{label}: <b>%{value} tramo(s)</b><extra></extra>",
        ))
        fig_pie.update_layout(
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=10, l=10, r=10), height=220,
            annotations=[dict(text=f"{n}<br>tramos", x=0.5, y=0.5,
                              font=dict(family="Sora", size=13, color=PAL["navy"]),
                              showarrow=False)],
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

    with col_g2:
        st.markdown('<div class="section-title">💰 Costo por tramo (S/.)</div>', unsafe_allow_html=True)
        nombres_cortos = [t["id"] for t in tramos]
        costos_rut = [t["costo_estimado_rutinario"] for t in tramos]
        costos_per = [t["costo_estimado_periodico"] for t in tramos]
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(name="Rutinario", x=nombres_cortos, y=costos_rut,
                               marker_color=PAL["green"], text=[f"S/{c//1000}K" for c in costos_rut],
                               textposition="outside", textfont=dict(size=9)))
        fig_b.add_trace(go.Bar(name="Periódico", x=nombres_cortos, y=costos_per,
                               marker_color=PAL["blue"], text=[f"S/{c//1000}K" for c in costos_per],
                               textposition="outside", textfont=dict(size=9)))
        fig_b.update_layout(
            barmode="group", bargap=0.3,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=10, l=10, r=10), height=220,
            legend=dict(orientation="h", y=-0.25, font=dict(size=9)),
            yaxis=dict(gridcolor="#E8EDF5", tickformat=",.0f"),
            xaxis=dict(tickfont=dict(size=10)),
        )
        st.plotly_chart(fig_b, use_container_width=True, config={"displayModeBar": False})

    with col_g3:
        st.markdown('<div class="section-title">🔢 IEC por tramo</div>', unsafe_allow_html=True)
        nombres = [t["nombre"].split("—")[0].strip()[:18] for t in tramos]
        iecs = [t["iec"] for t in tramos]
        colores = [color_deterioro(t["nivel_deterioro"]) for t in tramos]
        fig_h = go.Figure(go.Bar(
            x=iecs, y=nombres, orientation="h",
            marker_color=colores,
            text=[f"{i}%" for i in iecs],
            textposition="outside",
            textfont=dict(family="JetBrains Mono", size=10),
            hovertemplate="%{y}: <b>IEC %{x}%</b><extra></extra>",
        ))
        fig_h.add_vline(x=70, line_dash="dash", line_color=PAL["green"],
                        annotation_text="Umbral Bueno", annotation_font_size=9)
        fig_h.add_vline(x=40, line_dash="dash", line_color=PAL["orange"],
                        annotation_text="Umbral Regular", annotation_font_size=9)
        fig_h.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=10, l=10, r=60), height=220,
            xaxis=dict(range=[0, 110], gridcolor="#E8EDF5"),
            yaxis=dict(tickfont=dict(size=9)),
        )
        st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar": False})

    # ── Alertas ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">⚠️ Alertas de intervención</div>', unsafe_allow_html=True)
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        for t in tramos:
            if t["nivel_deterioro"] in ("Malo", "Crítico"):
                st.markdown(f"""
                <div class="alerta-box">
                    <strong>{t['id']} — {t['nombre']}</strong><br>
                    Estado: {t['nivel_deterioro']} (IEC {t['iec']}%) · {t['longitud_km']} km ·
                    Intervención recomendada: <strong>{t['tipo_intervencion_recomendada']}</strong>
                </div>""", unsafe_allow_html=True)
    with col_a2:
        for t in tramos:
            if t["nivel_deterioro"] == "Regular":
                st.markdown(f"""
                <div class="alerta-box warn">
                    <strong>{t['id']} — {t['nombre']}</strong><br>
                    Estado: Regular (IEC {t['iec']}%) · {t['longitud_km']} km ·
                    Monitorear — {t['tipo_intervencion_recomendada']}
                </div>""", unsafe_allow_html=True)
            elif t["nivel_deterioro"] == "Bueno":
                st.markdown(f"""
                <div class="alerta-box ok">
                    <strong>{t['id']} — {t['nombre']}</strong><br>
                    Estado: Bueno (IEC {t['iec']}%) · Mantener con rutinario preventivo
                </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — REGISTRAR TRAMO
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.pagina == "Registro":

    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">➕</div>
        <div>
            <div class="page-header-title">Registrar nuevo tramo vial</div>
            <div class="page-header-sub">Ingrese la información técnica completa del tramo</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("form_registro", clear_on_submit=True):
        st.markdown('<div class="section-title">📍 Ubicación e identificación</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            nombre = st.text_input("Nombre del tramo *", placeholder="Ej: Trocha Pacchanta — Mahuayani")
        with c2:
            comunidad = st.text_input("Comunidad / Sector *", placeholder="Ej: Pacchanta Alta")
        with c3:
            distrito = st.text_input("Distrito *", value="Ocongate")

        c4, c5, c6 = st.columns(3)
        with c4:
            provincia = st.text_input("Provincia", value="Quispicanchi")
        with c5:
            latitud = st.number_input("Latitud (GPS)", value=-13.65, format="%.4f")
        with c6:
            longitud_coord = st.number_input("Longitud (GPS)", value=-71.12, format="%.4f")

        st.markdown('<div class="section-title">📏 Características técnicas</div>', unsafe_allow_html=True)
        c7, c8, c9, c10 = st.columns(4)
        with c7:
            longitud_km = st.number_input("Longitud (km) *", min_value=0.1, value=5.0, step=0.1)
        with c8:
            ancho_m = st.number_input("Ancho de plataforma (m)", min_value=2.0, value=4.0, step=0.1)
        with c9:
            altitud = st.number_input("Altitud (m s.n.m.)", min_value=0, value=4000, step=50)
        with c10:
            puentes = st.number_input("N° de puentes", min_value=0, value=0, step=1)

        c11, c12, c13, c14 = st.columns(4)
        with c11:
            badenes = st.number_input("N° de badenes", min_value=0, value=0, step=1)
        with c12:
            superficie = st.selectbox("Tipo de superficie", ["Afirmado", "Tierra compactada", "Tierra natural", "Empedrado", "Otro"])
        with c13:
            drenaje = st.selectbox("Estado del drenaje", ["Bueno", "Regular", "Deficiente", "Muy deficiente", "Sin drenaje"])
        with c14:
            señalizacion = st.selectbox("Señalización", ["Completa", "Parcial", "Ausente"])

        st.markdown('<div class="section-title">🩺 Estado y deterioro</div>', unsafe_allow_html=True)
        c15, c16, c17 = st.columns(3)
        with c15:
            nivel_det = st.selectbox("Nivel de deterioro *", ["Bueno", "Regular", "Malo", "Crítico"])
        with c16:
            iec_val = st.slider("IEC — Índice de Estado del Camino (0–100)", 0, 100, 60)
        with c17:
            interv_rec = st.selectbox("Intervención recomendada", ["Rutinario preventivo", "Periódico preventivo", "Periódico urgente", "Correctivo de emergencia", "Sin intervención inmediata"])

        st.markdown('<div class="section-title">⛏️ Recursos y accesibilidad</div>', unsafe_allow_html=True)
        c18, c19, c20 = st.columns(3)
        with c18:
            cantera = st.text_input("Cantera o fuente de material cercana", placeholder="Ej: Cantera Pacchanta (2 km)")
        with c19:
            lastre = st.text_input("Fuente de lastre / material", placeholder="Ej: Río Ausangate")
        with c20:
            accesibilidad = st.selectbox("Accesibilidad", ["Todo el año", "Estacional (solo épocas secas)", "Restringido (requiere 4x4)", "Solo a pie o acémila"])

        st.markdown('<div class="section-title">💰 Costos estimados</div>', unsafe_allow_html=True)
        c21, c22 = st.columns(2)
        with c21:
            costo_rut = st.number_input("Costo estimado — Rutinario (S/.)", min_value=0, value=int(longitud_km * 11500), step=1000)
        with c22:
            costo_per = st.number_input("Costo estimado — Periódico (S/.)", min_value=0, value=int(longitud_km * 21000), step=1000)

        st.markdown('<div class="section-title">📝 Observaciones técnicas</div>', unsafe_allow_html=True)
        observaciones = st.text_area("Observaciones y notas del inspector", height=100,
            placeholder="Describir condiciones del terreno, problemas específicos, hallazgos de la inspección...")

        fecha_insp = st.date_input("Fecha de inspección", value=date.today())

        submitted = st.form_submit_button("💾  Guardar tramo", type="primary", use_container_width=True)

        if submitted:
            if not nombre or not comunidad:
                st.error("Por favor complete los campos obligatorios (*)")
            else:
                nuevo_id = f"TR-{len(st.session_state.tramos)+1:03d}"
                nuevo_tramo = {
                    "id": nuevo_id,
                    "nombre": nombre,
                    "comunidad": comunidad,
                    "distrito": distrito,
                    "provincia": provincia,
                    "longitud_km": longitud_km,
                    "ancho_m": ancho_m,
                    "altitud_msnm": altitud,
                    "superficie": superficie,
                    "nivel_deterioro": nivel_det,
                    "iec": iec_val,
                    "accesibilidad": accesibilidad,
                    "cantera_cercana": cantera,
                    "fuente_lastre": lastre,
                    "drenaje": drenaje,
                    "señalizacion": señalizacion,
                    "puentes": int(puentes),
                    "badenes": int(badenes),
                    "tipo_intervencion_recomendada": interv_rec,
                    "costo_estimado_rutinario": int(costo_rut),
                    "costo_estimado_periodico": int(costo_per),
                    "fecha_ultima_intervencion": str(fecha_insp),
                    "foto_url": "",
                    "observaciones": observaciones,
                    "latitud": latitud,
                    "longitud": longitud_coord,
                    "historial": [],
                }
                st.session_state.tramos.append(nuevo_tramo)
                st.success(f"✅ Tramo {nuevo_id} — '{nombre}' registrado correctamente.")
                st.session_state.pagina = "Consulta"
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — CONSULTAR TRAMOS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.pagina == "Consulta":

    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">🗂️</div>
        <div>
            <div class="page-header-title">Consulta de tramos viales</div>
            <div class="page-header-sub">Busque, filtre y seleccione un tramo para ver su ficha técnica completa</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Filtros
    fc1, fc2, fc3 = st.columns([2, 1, 1])
    with fc1:
        busqueda = st.text_input("🔍 Buscar por nombre o comunidad", placeholder="Ej: Pacchanta...")
    with fc2:
        filtro_estado = st.selectbox("Estado de la vía", ["Todos", "Bueno", "Regular", "Malo", "Crítico"])
    with fc3:
        filtro_sup = st.selectbox("Superficie", ["Todas", "Afirmado", "Tierra compactada", "Tierra natural", "Empedrado"])

    # Aplicar filtros
    tramos_filtrados = st.session_state.tramos
    if busqueda:
        tramos_filtrados = [t for t in tramos_filtrados
                            if busqueda.lower() in t["nombre"].lower()
                            or busqueda.lower() in t["comunidad"].lower()]
    if filtro_estado != "Todos":
        tramos_filtrados = [t for t in tramos_filtrados if t["nivel_deterioro"] == filtro_estado]
    if filtro_sup != "Todas":
        tramos_filtrados = [t for t in tramos_filtrados if t["superficie"] == filtro_sup]

    st.markdown(f"**{len(tramos_filtrados)} tramo(s) encontrado(s)**")
    st.markdown("---")

    if not tramos_filtrados:
        st.info("No se encontraron tramos con los filtros seleccionados.")
    else:
        for t in tramos_filtrados:
            color_borde = color_deterioro(t["nivel_deterioro"])
            st.markdown(f"""
            <div class="tramo-card" style="border-left:4px solid {color_borde};">
                <div class="tramo-card-header">
                    <div>
                        <div class="tramo-name">{t['id']}  ·  {t['nombre']}</div>
                        <div class="tramo-meta">
                            📍 {t['comunidad']}, {t['distrito']} · {t['altitud_msnm']} m s.n.m.
                        </div>
                    </div>
                    <div>{badge_deterioro(t['nivel_deterioro'])}</div>
                </div>
                <div>{barra_iec(t['iec'], w=260)}</div>
                <div class="tramo-stats">
                    <div class="tramo-stat">
                        <span class="tramo-stat-label">Longitud</span>
                        <span class="tramo-stat-value">{t['longitud_km']} km</span>
                    </div>
                    <div class="tramo-stat">
                        <span class="tramo-stat-label">Superficie</span>
                        <span class="tramo-stat-value">{t['superficie']}</span>
                    </div>
                    <div class="tramo-stat">
                        <span class="tramo-stat-label">Drenaje</span>
                        <span class="tramo-stat-value">{t['drenaje']}</span>
                    </div>
                    <div class="tramo-stat">
                        <span class="tramo-stat-label">Costo rutinario</span>
                        <span class="tramo-stat-value">S/. {t['costo_estimado_rutinario']:,}</span>
                    </div>
                    <div class="tramo-stat">
                        <span class="tramo-stat-label">Intervención</span>
                        <span class="tramo-stat-value">{t['tipo_intervencion_recomendada']}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"📋 Ver ficha completa — {t['id']}", key=f"ver_{t['id']}"):
                st.session_state.tramo_seleccionado = t["id"]
                st.session_state.pagina = "Detalle"
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 4 — FICHA TÉCNICA DETALLADA
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.pagina == "Detalle":

    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">📋</div>
        <div>
            <div class="page-header-title">Ficha técnica del tramo</div>
            <div class="page-header-sub">Información técnica completa para la planificación y mantenimiento</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Selector de tramo
    ids = [t["id"] for t in st.session_state.tramos]
    nombres_tramos = [f"{t['id']} — {t['nombre']}" for t in st.session_state.tramos]
    idx_sel = 0
    if st.session_state.tramo_seleccionado in ids:
        idx_sel = ids.index(st.session_state.tramo_seleccionado)

    sel = st.selectbox("Seleccionar tramo", nombres_tramos, index=idx_sel)
    tid = sel.split(" — ")[0]
    t = get_tramo(tid)
    if not t:
        st.error("Tramo no encontrado.")
        st.stop()
    st.session_state.tramo_seleccionado = tid

    # Encabezado del tramo
    col_enc1, col_enc2 = st.columns([2, 1])
    with col_enc1:
        st.markdown(f"""
        <div style="background:#fff; border-radius:12px; padding:1.2rem 1.5rem;
                    border:1px solid {PAL['line']}; border-left:5px solid {color_deterioro(t['nivel_deterioro'])};">
            <div style="font-size:1.2rem; font-weight:700; color:{PAL['navy']}; margin-bottom:0.3rem;">
                {t['id']}  ·  {t['nombre']}
            </div>
            <div style="font-size:0.82rem; color:{PAL['muted']}; margin-bottom:0.8rem;">
                📍 {t['comunidad']}, {t['distrito']}, {t['provincia']} ·
                🏔️ {t['altitud_msnm']:,} m s.n.m.
            </div>
            <div style="display:flex; gap:0.8rem; align-items:center; flex-wrap:wrap;">
                {badge_deterioro(t['nivel_deterioro'])}
                <span style="font-family:'JetBrains Mono',monospace; font-size:0.75rem;
                             color:{PAL['muted']};">IEC: {t['iec']}%</span>
                <span style="color:{PAL['line']};">|</span>
                <span style="font-size:0.78rem; color:{PAL['blue']};
                             font-weight:600;">{t['tipo_intervencion_recomendada']}</span>
            </div>
            <div style="margin-top:0.8rem;">{barra_iec(t['iec'], w=400)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_enc2:
        # Mini gauge IEC
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=t["iec"],
            domain={"x": [0, 1], "y": [0, 1]},
            number={"suffix": "%", "font": {"family": "Sora", "size": 28, "color": PAL["navy"]}},
            title={"text": "IEC", "font": {"family": "Sora", "size": 12, "color": PAL["muted"]}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": PAL["muted"]},
                "bar": {"color": color_deterioro(t["nivel_deterioro"])},
                "steps": [
                    {"range": [0,  40], "color": "#FDECEA"},
                    {"range": [40, 70], "color": "#FEF5E7"},
                    {"range": [70, 100], "color": "#E9F7EF"},
                ],
                "threshold": {"line": {"color": PAL["navy"], "width": 3}, "thickness": 0.7, "value": t["iec"]},
            },
        ))
        fig_gauge.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20, b=20, l=20, r=20), height=180,
        )
        st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<br>", unsafe_allow_html=True)

    # Columnas de ficha
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.markdown('<div class="section-title">📏 Datos técnicos</div>', unsafe_allow_html=True)
        ficha = {
            "Longitud del tramo":    f"{t['longitud_km']} km",
            "Ancho de plataforma":   f"{t['ancho_m']} m",
            "Altitud":               f"{t['altitud_msnm']:,} m s.n.m.",
            "Tipo de superficie":    t["superficie"],
            "Estado del drenaje":    t["drenaje"],
            "Señalización":          t["señalizacion"],
            "N° de puentes":         str(t["puentes"]),
            "N° de badenes":         str(t["badenes"]),
        }
        html_f = '<div style="background:#fff; border-radius:12px; padding:1rem 1.2rem; border:1px solid var(--line);">'
        for k, v in ficha.items():
            html_f += f'<div class="ficha-row"><span class="ficha-key">{k}</span><span class="ficha-val">{v}</span></div>'
        html_f += "</div>"
        st.markdown(html_f, unsafe_allow_html=True)

    with col_f2:
        st.markdown('<div class="section-title">⛏️ Recursos y logística</div>', unsafe_allow_html=True)
        ficha2 = {
            "Accesibilidad":          t["accesibilidad"],
            "Cantera / fuente mat.":  t["cantera_cercana"] or "No disponible",
            "Fuente de lastre":       t["fuente_lastre"] or "No disponible",
            "Última intervención":    t["fecha_ultima_intervencion"],
            "Costo est. rutinario":   f"S/. {t['costo_estimado_rutinario']:,}",
            "Costo est. periódico":   f"S/. {t['costo_estimado_periodico']:,}",
            "Costo/km rutinario":     f"S/. {t['costo_estimado_rutinario'] / t['longitud_km']:,.0f}",
            "Coordenadas GPS":        f"{t['latitud']:.4f}, {t['longitud']:.4f}",
        }
        html_f2 = '<div style="background:#fff; border-radius:12px; padding:1rem 1.2rem; border:1px solid var(--line);">'
        for k, v in ficha2.items():
            html_f2 += f'<div class="ficha-row"><span class="ficha-key">{k}</span><span class="ficha-val">{v}</span></div>'
        html_f2 += "</div>"
        st.markdown(html_f2, unsafe_allow_html=True)

    # Observaciones
    st.markdown('<div class="section-title" style="margin-top:1rem;">📝 Observaciones técnicas</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:{PAL['lorange']}; border-left:4px solid {PAL['orange']};
                border-radius:0 10px 10px 0; padding:1rem 1.2rem;
                font-size:0.88rem; color:{PAL['text']}; line-height:1.6;">
        {t['observaciones'] or 'Sin observaciones registradas.'}
    </div>
    """, unsafe_allow_html=True)

    # Historial
    st.markdown('<div class="section-title" style="margin-top:1rem;">🔧 Historial de mantenimiento</div>', unsafe_allow_html=True)
    if t["historial"]:
        html_h = '<div style="background:#fff; border-radius:12px; padding:1rem 1.2rem; border:1px solid var(--line);">'
        for h in sorted(t["historial"], key=lambda x: x["fecha"], reverse=True):
            c_tipo = PAL["red"] if h["tipo"] == "Correctivo" else PAL["green"]
            html_h += f"""
            <div class="mant-item">
                <div class="mant-fecha">{h['fecha']}</div>
                <div>
                    <div class="mant-tipo" style="color:{c_tipo};">
                        {h['tipo']} · S/. {h['costo']:,}
                    </div>
                    <div class="mant-desc">{h['ejecutor']}</div>
                    <div class="mant-desc" style="margin-top:0.2rem;">{h['descripcion']}</div>
                </div>
            </div>"""
        html_h += "</div>"
        st.markdown(html_h, unsafe_allow_html=True)
    else:
        st.info("No hay intervenciones registradas para este tramo.")


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 5 — MANTENIMIENTO
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.pagina == "Mantenimiento":

    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">🔧</div>
        <div>
            <div class="page-header-title">Planificación y registro de mantenimiento</div>
            <div class="page-header-sub">Cronograma preventivo y registro de intervenciones ejecutadas</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📅  Mantenimientos programados", "➕  Registrar intervención"])

    with tab1:
        st.markdown('<div class="section-title">Cronograma de mantenimiento — Plan Anual</div>', unsafe_allow_html=True)

        prog = st.session_state.mantenimientos_programados
        df_prog = pd.DataFrame(prog)
        df_prog["nombre_tramo"] = df_prog["tramo_id"].apply(
            lambda tid: next((t["nombre"] for t in st.session_state.tramos if t["id"] == tid), tid)
        )

        # Gantt de mantenimientos
        colores_tipo = {"Rutinario": PAL["green"], "Periódico": PAL["blue"]}
        fig_gantt = go.Figure()
        for i, row in df_prog.iterrows():
            color = colores_tipo.get(row["tipo"], PAL["muted"])
            fig_gantt.add_trace(go.Bar(
                x=[15],
                y=[f"{row['tramo_id']} — {row['nombre_tramo'][:20]}"],
                base=[0],
                orientation="h",
                marker=dict(color=color, opacity=0.85),
                name=row["tipo"],
                showlegend=i < 2,
                text=f"{row['tipo']} · {row['fecha_prog']}",
                textposition="inside",
                textfont=dict(family="Sora", size=9, color="white"),
                hovertemplate=(
                    f"<b>{row['tramo_id']}</b><br>"
                    f"Tipo: {row['tipo']}<br>"
                    f"Fecha: {row['fecha_prog']}<br>"
                    f"Estado: {row['estado']}<br>"
                    f"Costo est.: S/. {row['costo_est']:,}<extra></extra>"
                ),
            ))

        fig_gantt.update_layout(
            barmode="stack",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=10, l=10, r=10), height=240,
            legend=dict(orientation="h", y=-0.2, font=dict(size=10)),
            xaxis=dict(showticklabels=False, showgrid=False),
            yaxis=dict(tickfont=dict(size=9), autorange="reversed"),
        )
        st.plotly_chart(fig_gantt, use_container_width=True, config={"displayModeBar": False})

        # Tabla de programados
        col_estado = {"Pendiente": "🔴", "En ejecución": "🟡", "Programado": "🔵", "Completado": "🟢"}
        for row in prog:
            t_nom = next((t["nombre"] for t in st.session_state.tramos if t["id"] == row["tramo_id"]), row["tramo_id"])
            icono = col_estado.get(row["estado"], "⚪")
            st.markdown(f"""
            <div style="background:#fff; border-radius:10px; padding:0.8rem 1rem;
                        border:1px solid {PAL['line']}; margin-bottom:0.5rem;
                        display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
                <div>
                    <div style="font-weight:600; font-size:0.88rem; color:{PAL['navy']};">
                        {row['tramo_id']} — {t_nom[:35]}
                    </div>
                    <div style="font-size:0.76rem; color:{PAL['muted']};">
                        Tipo: <strong>{row['tipo']}</strong> · Fecha: {row['fecha_prog']} ·
                        Resp.: {row['responsable']} · Est.: S/. {row['costo_est']:,}
                    </div>
                </div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.75rem;">
                    {icono} {row['estado']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="section-title">Registrar nueva intervención ejecutada</div>', unsafe_allow_html=True)
        with st.form("form_mant"):
            c1, c2 = st.columns(2)
            with c1:
                ids_tramos = [f"{t['id']} — {t['nombre']}" for t in st.session_state.tramos]
                tramo_sel = st.selectbox("Tramo intervenido *", ids_tramos)
                tipo_mant = st.selectbox("Tipo de intervención *", ["Rutinario", "Periódico", "Correctivo", "Emergencia"])
                costo_real = st.number_input("Costo real ejecutado (S/.)", min_value=0, step=1000)
            with c2:
                fecha_mant = st.date_input("Fecha de ejecución", value=date.today())
                ejecutor = st.text_input("Ejecutor / Contratista", placeholder="Ej: Subgerencia de Mantenimiento")
                descripcion_mant = st.text_area("Descripción de los trabajos realizados", height=80)

            prog_btn = st.form_submit_button("💾  Guardar intervención", type="primary", use_container_width=True)
            if prog_btn:
                tid = tramo_sel.split(" — ")[0]
                tramo_obj = get_tramo(tid)
                if tramo_obj:
                    tramo_obj["historial"].append({
                        "fecha": str(fecha_mant),
                        "tipo": tipo_mant,
                        "costo": costo_real,
                        "ejecutor": ejecutor,
                        "descripcion": descripcion_mant,
                    })
                    tramo_obj["fecha_ultima_intervencion"] = str(fecha_mant)
                    st.success(f"✅ Intervención registrada correctamente en {tid}.")
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 6 — REPORTES
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.pagina == "Reportes":

    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">📈</div>
        <div>
            <div class="page-header-title">Reportes y análisis estadístico</div>
            <div class="page-header-sub">Análisis de costos, deterioro y planificación preventiva</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tramos = st.session_state.tramos

    # ── Fila 1: Comparativo de costos ──────────────────────────────────────
    st.markdown('<div class="section-title">📊 Comparativo de costos por tramo (S/.)</div>', unsafe_allow_html=True)

    df_costos = pd.DataFrame({
        "Tramo": [t["id"] for t in tramos],
        "Nombre": [t["nombre"].split("—")[0].strip()[:20] for t in tramos],
        "Rutinario": [t["costo_estimado_rutinario"] for t in tramos],
        "Periódico":  [t["costo_estimado_periodico"] for t in tramos],
        "Correctivo": [sum(h["costo"] for h in t["historial"]) for t in tramos],
    })

    fig_comp = go.Figure()
    for col, color, name in [
        ("Rutinario", PAL["green"], "Preventivo Rutinario (estimado)"),
        ("Periódico", PAL["blue"],  "Preventivo Periódico (estimado)"),
        ("Correctivo", PAL["red"],  "Correctivo Real (ejecutado)"),
    ]:
        fig_comp.add_trace(go.Bar(
            name=name, x=df_costos["Tramo"], y=df_costos[col],
            marker_color=color,
            text=[f"S/{v//1000}K" for v in df_costos[col]],
            textposition="outside", textfont=dict(size=9),
            hovertemplate="%{x}: <b>S/. %{y:,.0f}</b><extra>" + name + "</extra>",
        ))
    fig_comp.update_layout(
        barmode="group", bargap=0.25,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=10, l=10, r=10), height=300,
        legend=dict(orientation="h", y=-0.2, font=dict(size=10)),
        yaxis=dict(gridcolor="#E8EDF5", tickformat=",.0f", tickprefix="S/."),
        xaxis=dict(tickfont=dict(size=11)),
    )
    st.plotly_chart(fig_comp, use_container_width=True, config={"displayModeBar": False})

    # ── Fila 2: Curva deterioro + Radar ────────────────────────────────────
    col_r1, col_r2 = st.columns(2)

    with col_r1:
        st.markdown('<div class="section-title">📉 Curva de deterioro a 25 años</div>', unsafe_allow_html=True)
        años = list(range(0, 26))
        sin_m  = [max(0, round(100 - (años[i]**1.8) * 0.38)) for i in range(26)]
        con_r  = [max(78, 100 - i * 0.7) for i in range(26)]
        con_p  = [max(85, 100 - i * 0.4) for i in range(26)]

        fig_det = go.Figure()
        for y_vals, name, color, dash in [
            (sin_m, "Sin mantenimiento",    PAL["red"],    "dash"),
            (con_r, "Con mant. rutinario",  PAL["green"],  "solid"),
            (con_p, "Con mant. periódico",  PAL["blue"],   "dot"),
        ]:
            fig_det.add_trace(go.Scatter(
                x=años, y=y_vals, name=name, mode="lines",
                line=dict(color=color, width=2.5, dash=dash),
                fill="tozeroy" if name == "Sin mantenimiento" else None,
                fillcolor="rgba(192,57,43,0.06)",
                hovertemplate="Año %{x}: <b>%{y}%</b><extra>" + name + "</extra>",
            ))
        for y0, y1, label in [(70,100,"Bueno/Muy Bueno"),(40,70,"Regular"),(0,40,"Malo/Crítico")]:
            fig_det.add_hrect(y0=y0, y1=y1,
                              fillcolor="rgba(26,122,74,0.04)" if y0==70 else
                                        "rgba(211,84,0,0.04)" if y0==40 else
                                        "rgba(192,57,43,0.04)",
                              line_width=0,
                              annotation_text=label,
                              annotation_position="right",
                              annotation_font=dict(size=8, color=PAL["muted"]))
        fig_det.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=50, l=50, r=80), height=300,
            legend=dict(orientation="h", y=-0.22, font=dict(size=9)),
            xaxis=dict(title="Años", gridcolor="#E8EDF5"),
            yaxis=dict(title="IEC (%)", gridcolor="#E8EDF5", range=[0, 110]),
        )
        st.plotly_chart(fig_det, use_container_width=True, config={"displayModeBar": False})

    with col_r2:
        st.markdown('<div class="section-title">🕸️ Evaluación de alternativas (Radar)</div>', unsafe_allow_html=True)
        criterios  = ["Costo impl.", "Viabilidad org.", "T. impleme.", "Sostenibilidad", "Adapt. rural"]
        alt_a_vals = [5, 5, 5, 4, 5]
        alt_b_vals = [3, 4, 4, 4, 3]
        alt_c_vals = [2, 2, 2, 3, 2]
        crit_cierre = criterios + [criterios[0]]
        fig_rad = go.Figure()
        for nombre, vals, color in [
            ("Alt. A — Cronogramas Preventivos ★", alt_a_vals + [alt_a_vals[0]], PAL["green"]),
            ("Alt. B — Plataforma Digital",         alt_b_vals + [alt_b_vals[0]], PAL["blue"]),
            ("Alt. C — Tercerización LCS",           alt_c_vals + [alt_c_vals[0]], PAL["red"]),
        ]:
            fig_rad.add_trace(go.Scatterpolar(
                r=vals, theta=crit_cierre, name=nombre, mode="lines+markers",
                line=dict(color=color, width=2),
                marker=dict(size=5, color=color),
                fill="toself", fillcolor=color + "15",
                hovertemplate="%{theta}: <b>%{r}/5</b><extra>" + nombre + "</extra>",
            ))
        fig_rad.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 5], tickfont=dict(size=8)),
                angularaxis=dict(tickfont=dict(size=9)),
            ),
            showlegend=True,
            legend=dict(orientation="h", y=-0.15, font=dict(size=9)),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=70, l=50, r=50), height=300,
        )
        st.plotly_chart(fig_rad, use_container_width=True, config={"displayModeBar": False})

    # ── Tabla resumen de KPIs ──────────────────────────────────────────────
    st.markdown('<div class="section-title">🎯 Indicadores KPI — Línea base vs. Meta</div>', unsafe_allow_html=True)
    kpi_data = {
        "Código": ["KPI-01", "KPI-02", "KPI-03", "KPI-04", "KPI-05", "KPI-06"],
        "Indicador": [
            "% Intervenciones preventivas",
            "Costo promedio / km (S/.)",
            "% Tramos en estado ≥ Bueno",
            "Tramos con PMA activo (de 5)",
            "Plazo promedio / intervención (días)",
            "% Personal técnico capacitado",
        ],
        "Línea base (actual)": ["0%", "S/. 17,762", "~20%", "0 / 5", "75 días", "0%"],
        "Meta al 12° mes": ["≥70%", "≤ S/. 11,500", "≥80%", "5 / 5", "≤30 días", "100%"],
        "Frecuencia": ["Mensual", "Por intervención", "Mensual (fichas)", "Al 4° mes", "Por intervención", "Al 3° mes"],
    }
    df_kpi = pd.DataFrame(kpi_data)
    st.dataframe(df_kpi, use_container_width=True, hide_index=True)

    # ── Exportar datos ─────────────────────────────────────────────────────
    st.markdown('<div class="section-title" style="margin-top:1rem;">⬇️ Exportar datos</div>', unsafe_allow_html=True)
    df_export = pd.DataFrame([{
        "ID": t["id"], "Nombre": t["nombre"], "Comunidad": t["comunidad"],
        "Longitud (km)": t["longitud_km"], "Superficie": t["superficie"],
        "Nivel deterioro": t["nivel_deterioro"], "IEC (%)": t["iec"],
        "Costo rutinario (S/.)": t["costo_estimado_rutinario"],
        "Costo periódico (S/.)": t["costo_estimado_periodico"],
        "Intervención recomendada": t["tipo_intervencion_recomendada"],
        "Última intervención": t["fecha_ultima_intervencion"],
    } for t in st.session_state.tramos])

    csv = df_export.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥  Descargar datos de tramos (CSV)",
        data=csv,
        file_name="trochas_ocongate_export.csv",
        mime="text/csv",
        type="primary",
    )
