# -*- coding: utf-8 -*-
"""
CHASKI TRACK - Plataforma de Gestión Operativa
Servicio de Transporte de Carga (Flete) de Tuna | Ayacucho -> Lima
Proyecto: Evaluación Financiera de Proyectos (GI4101) - UTEC

Autor: Grupo PC2 - Huanuco Mayta, Puma Mamani, Vargas Inga, Viracocha Cruz
Descripción:
    Simulador operativo del proyecto. NO calcula COK/WACC/VAN/TIR (eso ya
    está resuelto en el informe). Esta plataforma representa cómo
    funcionaría el negocio en la práctica: actores, roles, pedidos, viajes,
    rutas, flota, clientes, costos, ingresos, seguimiento en tiempo real
    y reportes, con persistencia en SQLite.

Ejecutar:
    streamlit run chaski_track_platform.py
"""

import sqlite3
import random
import string
from datetime import datetime, timedelta, date
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================
DB_PATH = Path(__file__).parent / "chaski_track.db"

st.set_page_config(
    page_title="Chaski Track | Gestión de Flete de Tuna",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY = "#1B5E20"
SECONDARY = "#2E7D32"
ACCENT = "#F9A825"
DANGER = "#C62828"
BG_CARD = "#F4F8F1"

CUSTOM_CSS = f"""
<style>
.main {{ background-color: #FAFAF7; }}
.block-container {{ padding-top: 1.4rem; }}
h1, h2, h3 {{ color: {PRIMARY}; }}
div[data-testid="stMetric"] {{
    background-color: {BG_CARD};
    border: 1px solid #DCE8D5;
    border-radius: 10px;
    padding: 14px 16px 6px 16px;
}}
.kpi-card {{
    background: white;
    border-radius: 12px;
    padding: 16px 18px;
    border: 1px solid #E3E8DD;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}}
.badge {{
    display:inline-block; padding:3px 10px; border-radius:20px;
    font-size:12px; font-weight:600; color:white;
}}
.badge-ok {{ background-color: {SECONDARY}; }}
.badge-warn {{ background-color: {ACCENT}; color:#3a2f00; }}
.badge-bad {{ background-color: {DANGER}; }}
.badge-info {{ background-color:#1565C0; }}
.section-title {{
    border-left: 5px solid {SECONDARY};
    padding-left: 10px; margin-top: 6px; margin-bottom: 4px;
}}
.small-note {{ color:#666; font-size:13px; }}
.stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
.stTabs [data-baseweb="tab"] {{
    background-color:#EFF3EA; border-radius:8px 8px 0 0; padding:8px 16px;
}}
.stTabs [aria-selected="true"] {{ background-color: {SECONDARY}; color:white; }}
footer {{visibility:hidden;}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================================
# BASE DE DATOS — CONEXIÓN Y ESQUEMA
# ============================================================

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS personal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    cargo TEXT NOT NULL,
    tipo TEXT NOT NULL,            -- Directa / Indirecta
    telefono TEXT,
    estado TEXT DEFAULT 'Activo'
);

CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL,            -- Productor / Comerciante (mayorista)
    zona TEXT,
    telefono TEXT,
    fecha_registro TEXT
);

CREATE TABLE IF NOT EXISTS flota (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    placa TEXT NOT NULL,
    tipo TEXT NOT NULL,            -- Principal / Respaldo
    capacidad_cajas INTEGER,
    estado TEXT DEFAULT 'Operativo',  -- Operativo / Mantenimiento / Inactivo
    km_recorridos REAL DEFAULT 0,
    ultimo_mantenimiento TEXT
);

CREATE TABLE IF NOT EXISTS viajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE,
    cliente_id INTEGER,
    chofer_id INTEGER,
    ayudante_id INTEGER,
    vehiculo_id INTEGER,
    origen TEXT DEFAULT 'Ayacucho',
    destino TEXT DEFAULT 'Mercado Mayorista N°2 - Lima',
    fecha_salida TEXT,
    fecha_entrega_estimada TEXT,
    fecha_entrega_real TEXT,
    cantidad_cajas INTEGER,
    tarifa_caja REAL DEFAULT 21.0,
    estado TEXT DEFAULT 'Programado', -- Programado/En tránsito/Entregado/Incidencia/Cancelado
    incidencia TEXT,
    merma_cajas INTEGER DEFAULT 0,
    avance_pct INTEGER DEFAULT 0,
    observaciones TEXT,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    FOREIGN KEY (chofer_id) REFERENCES personal(id),
    FOREIGN KEY (ayudante_id) REFERENCES personal(id),
    FOREIGN KEY (vehiculo_id) REFERENCES flota(id)
);

CREATE TABLE IF NOT EXISTS costos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    viaje_id INTEGER,
    categoria TEXT NOT NULL,   -- Combustible/Peaje/Mantenimiento/Materiales/Otros
    descripcion TEXT,
    monto REAL,
    fecha TEXT,
    FOREIGN KEY (viaje_id) REFERENCES viajes(id)
);

CREATE TABLE IF NOT EXISTS pagos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    viaje_id INTEGER,
    cliente_id INTEGER,
    monto REAL,
    estado TEXT DEFAULT 'Pendiente',  -- Pendiente/Pagado
    fecha_emision TEXT,
    fecha_pago TEXT,
    FOREIGN KEY (viaje_id) REFERENCES viajes(id),
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

CREATE TABLE IF NOT EXISTS seguimiento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    viaje_id INTEGER,
    evento TEXT,
    detalle TEXT,
    timestamp TEXT,
    FOREIGN KEY (viaje_id) REFERENCES viajes(id)
);
"""

def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


# ============================================================
# AUTO-SEED (datos iniciales basados en el informe)
# ============================================================

PERSONAL_SEED = [
    ("Juan Carlos Quispe", "Chofer de transporte", "Directa", "987 654 321"),
    ("Pedro Huamán", "Ayudante del chofer", "Directa", "988 451 022"),
    ("Rosa Ttito Mamani", "Estibador (carga/descarga)", "Directa", "984 332 110"),
    ("Marco Cárdenas Soto", "Coordinador logístico (Gerente)", "Indirecta", "999 112 233"),
    ("Lucía Fernández Paredes", "Asistente contable", "Indirecta", "955 220 884"),
    ("Diego Huanuco Mayta", "Responsable de marketing", "Indirecta", "966 778 102"),
]

CLIENTES_SEED = [
    ("Asoc. Productores Tuna Cangallo", "Productor", "Ayacucho - Cangallo", "066-441122"),
    ("Productor Independiente - Vischongo", "Productor", "Ayacucho - Vischongo", "966-552231"),
    ("Comercial Frutera Lima Norte", "Comerciante", "Mercado Mayorista N°2", "01-3349812"),
    ("Doña Tula Distribuidora", "Comerciante", "Mercado Mayorista N°2", "01-4471092"),
    ("Frutos del Sur SAC", "Comerciante", "Mercado Mayorista N°2", "01-2280456"),
    ("Productores Huamanga Agro", "Productor", "Ayacucho - Huamanga", "066-778455"),
]

FLOTA_SEED = [
    ("AYA-1024", "Principal", 300, "Operativo", 18450, "2026-04-12"),
    ("AYA-7790", "Respaldo", 270, "Operativo", 5210, "2026-05-02"),
]

ESTADOS_VIAJE = ["Programado", "En tránsito", "Entregado", "Incidencia"]
INCIDENCIAS_POSIBLES = [
    "Retraso por clima en la ruta",
    "Bloqueo temporal de vía",
    "Falla mecánica menor",
    "Demora en carga en almacén",
]


def codigo_viaje(n):
    return f"ACHS-{n:04d}"


def seed_if_empty():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM personal")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO personal (nombre, cargo, tipo, telefono) VALUES (?,?,?,?)",
            PERSONAL_SEED,
        )

    cur.execute("SELECT COUNT(*) FROM clientes")
    if cur.fetchone()[0] == 0:
        hoy = datetime.now()
        rows = [(n, t, z, tel, (hoy - timedelta(days=random.randint(10, 400))).strftime("%Y-%m-%d"))
                for (n, t, z, tel) in CLIENTES_SEED]
        cur.executemany(
            "INSERT INTO clientes (nombre, tipo, zona, telefono, fecha_registro) VALUES (?,?,?,?,?)",
            rows,
        )

    cur.execute("SELECT COUNT(*) FROM flota")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO flota (placa, tipo, capacidad_cajas, estado, km_recorridos, ultimo_mantenimiento) "
            "VALUES (?,?,?,?,?,?)",
            FLOTA_SEED,
        )
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM viajes")
    if cur.fetchone()[0] == 0:
        cur.execute("SELECT id FROM clientes")
        cliente_ids = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT id FROM personal WHERE cargo='Chofer de transporte'")
        chofer_ids = [r[0] for r in cur.fetchall()] or [1]
        cur.execute("SELECT id FROM personal WHERE cargo='Ayudante del chofer'")
        ayudante_ids = [r[0] for r in cur.fetchall()] or [2]
        cur.execute("SELECT id FROM flota")
        flota_ids = [r[0] for r in cur.fetchall()]

        hoy = datetime.now()
        n_viajes = 28
        for i in range(1, n_viajes + 1):
            dias_atras = random.randint(0, 45)
            f_salida = hoy - timedelta(days=dias_atras, hours=random.randint(0, 10))
            f_estimada = f_salida + timedelta(hours=20)
            cajas = random.choice([140, 150, 160, 180, 200, 220, 260, 300])
            tarifa = 21.0

            if dias_atras <= 1:
                estado = random.choice(["Programado", "En tránsito"])
                avance = 0 if estado == "Programado" else random.randint(15, 80)
                f_real = None
                incid = None
            elif dias_atras <= 3 and random.random() < 0.18:
                estado = "Incidencia"
                avance = random.randint(30, 70)
                f_real = None
                incid = random.choice(INCIDENCIAS_POSIBLES)
            else:
                estado = "Entregado"
                avance = 100
                f_real = f_estimada + timedelta(hours=random.choice([-2, -1, 0, 0, 1, 3]))
                incid = None

            merma = random.choice([0, 0, 0, 1, 2, 3]) if estado == "Entregado" else 0

            cur.execute(
                """INSERT INTO viajes
                (codigo, cliente_id, chofer_id, ayudante_id, vehiculo_id, origen, destino,
                 fecha_salida, fecha_entrega_estimada, fecha_entrega_real, cantidad_cajas,
                 tarifa_caja, estado, incidencia, merma_cajas, avance_pct, observaciones)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    codigo_viaje(i),
                    random.choice(cliente_ids),
                    random.choice(chofer_ids),
                    random.choice(ayudante_ids),
                    random.choice(flota_ids),
                    "Ayacucho",
                    "Mercado Mayorista de Frutas N°2 - Lima",
                    f_salida.strftime("%Y-%m-%d %H:%M"),
                    f_estimada.strftime("%Y-%m-%d %H:%M"),
                    f_real.strftime("%Y-%m-%d %H:%M") if f_real else None,
                    cajas,
                    tarifa,
                    estado,
                    incid,
                    merma,
                    avance,
                    "Viaje generado en carga inicial de demostración.",
                ),
            )
            viaje_id = cur.lastrowid

            # costos asociados
            costos_viaje = [
                ("Combustible", "Diésel para recorrido Ayacucho-Lima-Ayacucho", round(random.uniform(420, 520), 2)),
                ("Peajes", "Peajes ruta Los Libertadores / Panamericana", round(random.uniform(55, 70), 2)),
                ("Materiales", "Cajas de madera, rafia, plásticos protectores", round(cajas * 3.7, 2)),
            ]
            if random.random() < 0.15:
                costos_viaje.append(("Mantenimiento", "Revisión preventiva menor", round(random.uniform(80, 250), 2)))

            for cat, desc, monto in costos_viaje:
                cur.execute(
                    "INSERT INTO costos (viaje_id, categoria, descripcion, monto, fecha) VALUES (?,?,?,?,?)",
                    (viaje_id, cat, desc, monto, f_salida.strftime("%Y-%m-%d")),
                )

            # pago / ingreso
            monto_pago = round(cajas * tarifa, 2)
            pagado = estado == "Entregado" and random.random() < 0.75
            cur.execute(
                """INSERT INTO pagos (viaje_id, cliente_id, monto, estado, fecha_emision, fecha_pago)
                VALUES (?,?,?,?,?,?)""",
                (
                    viaje_id,
                    None,
                    monto_pago,
                    "Pagado" if pagado else "Pendiente",
                    f_salida.strftime("%Y-%m-%d"),
                    (f_salida + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d") if pagado else None,
                ),
            )

            # seguimiento
            eventos = [("Salida del camión", "Camión despachado desde almacén Ayacucho")]
            if estado in ("En tránsito", "Entregado", "Incidencia"):
                eventos.append(("En tránsito", "Camión en ruta hacia Lima"))
            if estado == "Incidencia":
                eventos.append(("Incidencia reportada", incid))
            if estado == "Entregado":
                eventos.append(("Entrega completada", "Mercadería entregada y verificada en destino"))
            for ev, det in eventos:
                cur.execute(
                    "INSERT INTO seguimiento (viaje_id, evento, detalle, timestamp) VALUES (?,?,?,?)",
                    (viaje_id, ev, det, f_salida.strftime("%Y-%m-%d %H:%M")),
                )

        conn.commit()
    conn.close()


init_db()
seed_if_empty()

# ============================================================
# UTILITARIOS DE ACCESO A DATOS
# ============================================================

def df_query(query, params=()):
    conn = get_conn()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def execute(query, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


def next_codigo():
    df = df_query("SELECT COUNT(*) AS n FROM viajes")
    return codigo_viaje(int(df['n'][0]) + 1)


def badge(text, kind="ok"):
    cls = {"ok": "badge-ok", "warn": "badge-warn", "bad": "badge-bad", "info": "badge-info"}[kind]
    return f"<span class='badge {cls}'>{text}</span>"


def estado_kind(estado):
    return {
        "Programado": "info",
        "En tránsito": "warn",
        "Entregado": "ok",
        "Incidencia": "bad",
        "Cancelado": "bad",
    }.get(estado, "info")


# ============================================================
# SIDEBAR — LOGIN SIMULADO POR ROL
# ============================================================

ROLES = {
    "Coordinador logístico (Gerente)": "gerente",
    "Asistente contable": "contable",
    "Responsable de marketing": "marketing",
    "Chofer de transporte": "chofer",
    "Cliente / Comerciante": "cliente",
}

with st.sidebar:
    st.markdown("## 🚚 CHASKI TRACK")
    st.caption("Sistema de Gestión del Servicio de Flete de Tuna")
    st.divider()
    rol_label = st.selectbox("Ingresar como:", list(ROLES.keys()), index=0)
    rol = ROLES[rol_label]
    st.success(f"Sesión activa: **{rol_label}**")
    st.divider()

    menu_opciones = {
        "gerente": ["🏠 Dashboard", "🧾 Pedidos y Viajes", "👥 Clientes", "👷 Personal",
                    "🚛 Flota y Mantenimiento", "💰 Costos e Ingresos", "📍 Seguimiento en Vivo", "📊 Reportes"],
        "contable": ["🏠 Dashboard", "💰 Costos e Ingresos", "📊 Reportes"],
        "marketing": ["🏠 Dashboard", "👥 Clientes", "📊 Reportes"],
        "chofer": ["🏠 Dashboard", "🧾 Pedidos y Viajes", "📍 Seguimiento en Vivo"],
        "cliente": ["🏠 Dashboard", "📍 Seguimiento en Vivo"],
    }
    seccion = st.radio("Navegación", menu_opciones[rol])

    st.divider()
    st.markdown("**Ruta del servicio**")
    st.caption("Ayacucho → Mercado Mayorista de Frutas N°2, La Victoria, Lima")
    st.markdown("**Tarifa vigente:** S/ 21.00 por caja")
    st.markdown("---")
    st.caption("Plataforma de simulación operativa — UTEC GI4101")
    if st.button("🔄 Reiniciar datos de demostración"):
        if DB_PATH.exists():
            DB_PATH.unlink()
        init_db()
        seed_if_empty()
        st.rerun()

st.title("🚚 Chaski Track — Plataforma de Gestión del Servicio de Flete")
st.caption("Transporte especializado de tuna · Ayacucho → Mercado Mayorista de Frutas N° 2, Lima")
st.markdown("---")

# ============================================================
# MÓDULO: DASHBOARD
# ============================================================

def modulo_dashboard():
    st.markdown("<h3 class='section-title'>Panel General de Operaciones</h3>", unsafe_allow_html=True)

    viajes = df_query("SELECT * FROM viajes")
    pagos = df_query("SELECT * FROM pagos")
    costos = df_query("SELECT * FROM costos")
    clientes = df_query("SELECT * FROM clientes")

    total_viajes = len(viajes)
    en_curso = len(viajes[viajes['estado'].isin(['Programado', 'En tránsito'])])
    incidencias = len(viajes[viajes['estado'] == 'Incidencia'])
    cajas_totales = int(viajes['cantidad_cajas'].sum()) if total_viajes else 0
    ingresos = pagos['monto'].sum() if len(pagos) else 0
    cobrado = pagos.loc[pagos['estado'] == 'Pagado', 'monto'].sum() if len(pagos) else 0
    pendiente = ingresos - cobrado
    gastos = costos['monto'].sum() if len(costos) else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Viajes registrados", total_viajes)
    c2.metric("En curso", en_curso)
    c3.metric("Cajas transportadas", f"{cajas_totales:,}")
    c4.metric("Ingresos facturados", f"S/ {ingresos:,.2f}")
    c5.metric("Incidencias activas", incidencias, delta=None)

    c6, c7, c8 = st.columns(3)
    c6.metric("Cobrado", f"S/ {cobrado:,.2f}")
    c7.metric("Por cobrar", f"S/ {pendiente:,.2f}")
    c8.metric("Costos operativos", f"S/ {gastos:,.2f}")

    st.markdown("---")
    col1, col2 = st.columns([1.3, 1])

    with col1:
        st.markdown("##### Estado actual de viajes")
        if total_viajes:
            conteo = viajes['estado'].value_counts().reset_index()
            conteo.columns = ['Estado', 'Cantidad']
            fig = px.bar(conteo, x='Estado', y='Cantidad', color='Estado',
                         color_discrete_map={
                             "Programado": "#1565C0", "En tránsito": ACCENT,
                             "Entregado": SECONDARY, "Incidencia": DANGER, "Cancelado": "#777"
                         }, text='Cantidad')
            fig.update_layout(showlegend=False, height=320, margin=dict(t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aún no hay viajes registrados.")

    with col2:
        st.markdown("##### Cajas por cliente (Top 6)")
        if total_viajes:
            merge = viajes.merge(clientes, left_on='cliente_id', right_on='id', suffixes=('', '_cli'))
            top = merge.groupby('nombre')['cantidad_cajas'].sum().sort_values(ascending=False).head(6)
            fig2 = px.pie(top, values=top.values, names=top.index, hole=0.45)
            fig2.update_layout(height=320, margin=dict(t=10, b=0))
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("##### Evolución diaria de viajes (últimos 30 días)")
    if total_viajes:
        v = viajes.copy()
        v['fecha'] = pd.to_datetime(v['fecha_salida']).dt.date
        serie = v.groupby('fecha').size().reset_index(name='viajes')
        fig3 = px.area(serie, x='fecha', y='viajes', color_discrete_sequence=[SECONDARY])
        fig3.update_layout(height=260, margin=dict(t=10, b=0))
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("##### 🔔 Alertas operativas")
    alertas = []
    if incidencias:
        alertas.append((f"{incidencias} viaje(s) con incidencia activa requieren atención.", "bad"))
    flota = df_query("SELECT * FROM flota WHERE estado != 'Operativo'")
    if len(flota):
        alertas.append((f"{len(flota)} vehículo(s) fuera de operación (mantenimiento/inactivo).", "warn"))
    if pendiente > 0:
        alertas.append((f"S/ {pendiente:,.2f} pendientes de cobro a clientes.", "warn"))
    if not alertas:
        alertas.append(("Sin alertas operativas. El servicio opera con normalidad.", "ok"))
    for texto, kind in alertas:
        st.markdown(badge(texto, kind), unsafe_allow_html=True)


# ============================================================
# MÓDULO: PEDIDOS Y VIAJES
# ============================================================

def modulo_pedidos():
    st.markdown("<h3 class='section-title'>Gestión de Pedidos y Viajes</h3>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📋 Listado de viajes", "➕ Registrar nuevo viaje"])

    with tab1:
        viajes = df_query("""
            SELECT v.id, v.codigo, c.nombre AS cliente, p1.nombre AS chofer, p2.nombre AS ayudante,
                   f.placa AS vehiculo, v.fecha_salida, v.fecha_entrega_estimada, v.fecha_entrega_real,
                   v.cantidad_cajas, v.tarifa_caja, v.estado, v.avance_pct, v.merma_cajas, v.incidencia
            FROM viajes v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            LEFT JOIN personal p1 ON v.chofer_id = p1.id
            LEFT JOIN personal p2 ON v.ayudante_id = p2.id
            LEFT JOIN flota f ON v.vehiculo_id = f.id
            ORDER BY v.fecha_salida DESC
        """)

        colf1, colf2, colf3 = st.columns(3)
        with colf1:
            f_estado = st.multiselect("Filtrar por estado", ESTADOS_VIAJE + ["Cancelado"])
        with colf2:
            f_cliente = st.multiselect("Filtrar por cliente", sorted(viajes['cliente'].dropna().unique()))
        with colf3:
            f_codigo = st.text_input("Buscar código de viaje")

        vf = viajes.copy()
        if f_estado:
            vf = vf[vf['estado'].isin(f_estado)]
        if f_cliente:
            vf = vf[vf['cliente'].isin(f_cliente)]
        if f_codigo:
            vf = vf[vf['codigo'].str.contains(f_codigo, case=False, na=False)]

        vf['ingreso (S/.)'] = vf['cantidad_cajas'] * vf['tarifa_caja']
        st.dataframe(
            vf[['codigo', 'cliente', 'chofer', 'vehiculo', 'fecha_salida', 'fecha_entrega_estimada',
                'cantidad_cajas', 'ingreso (S/.)', 'estado', 'avance_pct', 'merma_cajas']].rename(
                columns={'avance_pct': 'avance (%)'}
            ),
            use_container_width=True, height=380
        )

        st.markdown("##### Actualizar estado de un viaje")
        if len(vf):
            sel = st.selectbox("Selecciona el código de viaje", vf['codigo'].tolist())
            row = viajes[viajes['codigo'] == sel].iloc[0]
            c1, c2, c3 = st.columns(3)
            with c1:
                nuevo_estado = st.selectbox("Nuevo estado", ESTADOS_VIAJE + ["Cancelado"],
                                             index=ESTADOS_VIAJE.index(row['estado']) if row['estado'] in ESTADOS_VIAJE else 0)
            with c2:
                avance = st.slider("Avance del viaje (%)", 0, 100, int(row['avance_pct']))
            with c3:
                merma = st.number_input("Merma de cajas (unid.)", min_value=0, value=int(row['merma_cajas']))
            obs = st.text_area("Observación / incidencia (si aplica)", value=row['incidencia'] or "")

            if st.button("💾 Guardar actualización", type="primary"):
                viaje_id = int(viajes[viajes['codigo'] == sel]['id'].iloc[0])
                f_real = None
                if nuevo_estado == "Entregado":
                    f_real = datetime.now().strftime("%Y-%m-%d %H:%M")
                    avance = 100
                execute(
                    """UPDATE viajes SET estado=?, avance_pct=?, merma_cajas=?, incidencia=?,
                       fecha_entrega_real=COALESCE(?, fecha_entrega_real) WHERE id=?""",
                    (nuevo_estado, avance, merma, obs if obs else None, f_real, viaje_id),
                )
                execute(
                    "INSERT INTO seguimiento (viaje_id, evento, detalle, timestamp) VALUES (?,?,?,?)",
                    (viaje_id, f"Actualización: {nuevo_estado}",
                     obs if obs else f"Estado actualizado a {nuevo_estado} ({avance}%)",
                     datetime.now().strftime("%Y-%m-%d %H:%M")),
                )
                st.success(f"Viaje {sel} actualizado correctamente.")
                st.rerun()

    with tab2:
        st.markdown("##### Registrar un nuevo viaje / pedido de transporte")
        clientes = df_query("SELECT id, nombre FROM clientes ORDER BY nombre")
        choferes = df_query("SELECT id, nombre FROM personal WHERE cargo='Chofer de transporte'")
        ayudantes = df_query("SELECT id, nombre FROM personal WHERE cargo='Ayudante del chofer'")
        flota = df_query("SELECT id, placa, capacidad_cajas, estado FROM flota WHERE estado='Operativo'")

        with st.form("nuevo_viaje_form"):
            c1, c2 = st.columns(2)
            with c1:
                cliente_sel = st.selectbox("Cliente / comerciante", clientes['nombre'])
                chofer_sel = st.selectbox("Chofer asignado", choferes['nombre'] if len(choferes) else ["Sin chofer registrado"])
                vehiculo_sel = st.selectbox("Vehículo", flota['placa'] if len(flota) else ["Sin vehículo disponible"])
                cajas = st.number_input("Cantidad de cajas a transportar", min_value=1, max_value=320, value=150, step=10)
            with c2:
                ayudante_sel = st.selectbox("Ayudante de chofer", ayudantes['nombre'] if len(ayudantes) else ["Sin ayudante registrado"])
                tarifa = st.number_input("Tarifa por caja (S/.)", min_value=1.0, value=21.0, step=0.5)
                fecha_salida = st.date_input("Fecha de salida", value=date.today())
                hora_salida = st.time_input("Hora de salida", value=datetime.now().time())

            obs = st.text_area("Observaciones del pedido")
            submitted = st.form_submit_button("🚚 Registrar viaje", type="primary")

            if submitted:
                cliente_id = int(clientes[clientes['nombre'] == cliente_sel]['id'].iloc[0])
                chofer_id = int(choferes[choferes['nombre'] == chofer_sel]['id'].iloc[0]) if len(choferes) else None
                ayudante_id = int(ayudantes[ayudantes['nombre'] == ayudante_sel]['id'].iloc[0]) if len(ayudantes) else None
                vehiculo_id = int(flota[flota['placa'] == vehiculo_sel]['id'].iloc[0]) if len(flota) else None

                f_salida_dt = datetime.combine(fecha_salida, hora_salida)
                f_estimada_dt = f_salida_dt + timedelta(hours=20)
                codigo = next_codigo()

                viaje_id = execute(
                    """INSERT INTO viajes
                    (codigo, cliente_id, chofer_id, ayudante_id, vehiculo_id, origen, destino,
                     fecha_salida, fecha_entrega_estimada, cantidad_cajas, tarifa_caja, estado,
                     avance_pct, observaciones)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (codigo, cliente_id, chofer_id, ayudante_id, vehiculo_id, "Ayacucho",
                     "Mercado Mayorista de Frutas N°2 - Lima",
                     f_salida_dt.strftime("%Y-%m-%d %H:%M"), f_estimada_dt.strftime("%Y-%m-%d %H:%M"),
                     cajas, tarifa, "Programado", 0, obs),
                )

                monto = round(cajas * tarifa, 2)
                execute(
                    "INSERT INTO pagos (viaje_id, monto, estado, fecha_emision) VALUES (?,?,?,?)",
                    (viaje_id, monto, "Pendiente", f_salida_dt.strftime("%Y-%m-%d")),
                )
                # costos estimados automáticos
                costos_auto = [
                    ("Combustible", "Diésel estimado para el recorrido", round(random.uniform(420, 520), 2)),
                    ("Peajes", "Peajes ruta Los Libertadores / Panamericana", round(random.uniform(55, 70), 2)),
                    ("Materiales", "Cajas de madera, rafia, plásticos protectores", round(cajas * 3.7, 2)),
                ]
                for cat, desc, m in costos_auto:
                    execute(
                        "INSERT INTO costos (viaje_id, categoria, descripcion, monto, fecha) VALUES (?,?,?,?,?)",
                        (viaje_id, cat, desc, m, fecha_salida.strftime("%Y-%m-%d")),
                    )
                execute(
                    "INSERT INTO seguimiento (viaje_id, evento, detalle, timestamp) VALUES (?,?,?,?)",
                    (viaje_id, "Pedido registrado", f"Viaje {codigo} programado para {cliente_sel}",
                     datetime.now().strftime("%Y-%m-%d %H:%M")),
                )
                st.success(f"✅ Viaje **{codigo}** registrado correctamente. Ingreso estimado: S/ {monto:,.2f}")
                st.balloons()


# ============================================================
# MÓDULO: CLIENTES
# ============================================================

def modulo_clientes():
    st.markdown("<h3 class='section-title'>Gestión de Clientes</h3>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📇 Cartera de clientes", "➕ Registrar cliente"])

    with tab1:
        clientes = df_query("SELECT * FROM clientes ORDER BY nombre")
        viajes = df_query("SELECT cliente_id, cantidad_cajas, tarifa_caja, estado FROM viajes")

        resumen = viajes.groupby('cliente_id').agg(
            viajes=('cliente_id', 'count'),
            cajas=('cantidad_cajas', 'sum'),
        ).reset_index()
        resumen['ingreso (S/.)'] = (viajes.groupby('cliente_id')
                                     .apply(lambda d: (d['cantidad_cajas'] * d['tarifa_caja']).sum())
                                     .reset_index(drop=True)) if len(viajes) else 0

        tabla = clientes.merge(resumen, left_on='id', right_on='cliente_id', how='left').fillna(0)
        st.dataframe(
            tabla[['nombre', 'tipo', 'zona', 'telefono', 'fecha_registro', 'viajes', 'cajas', 'ingreso (S/.)']],
            use_container_width=True, height=380
        )

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### Clientes por tipo")
            fig = px.pie(clientes, names='tipo', hole=0.45)
            fig.update_layout(height=280)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("##### Top clientes por ingreso generado")
            top = tabla.sort_values('ingreso (S/.)', ascending=False).head(6)
            fig2 = px.bar(top, x='nombre', y='ingreso (S/.)', color_discrete_sequence=[SECONDARY])
            fig2.update_layout(height=280, xaxis_title="", margin=dict(t=10))
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        with st.form("nuevo_cliente_form"):
            nombre = st.text_input("Nombre / Razón social")
            tipo = st.selectbox("Tipo de cliente", ["Productor", "Comerciante"])
            zona = st.text_input("Zona / Ubicación")
            telefono = st.text_input("Teléfono de contacto")
            submitted = st.form_submit_button("Registrar cliente", type="primary")
            if submitted and nombre:
                execute(
                    "INSERT INTO clientes (nombre, tipo, zona, telefono, fecha_registro) VALUES (?,?,?,?,?)",
                    (nombre, tipo, zona, telefono, datetime.now().strftime("%Y-%m-%d")),
                )
                st.success(f"Cliente **{nombre}** registrado correctamente.")
                st.rerun()


# ============================================================
# MÓDULO: PERSONAL
# ============================================================

def modulo_personal():
    st.markdown("<h3 class='section-title'>Personal y Roles Operativos</h3>", unsafe_allow_html=True)

    st.markdown("""
    El equipo de Chaski Track está organizado bajo una estructura funcional que separa la **mano de
    obra directa** (operación) de la **mano de obra indirecta** (gestión y administración), conforme a
    lo definido en el estudio del proyecto.
    """)

    personal = df_query("SELECT * FROM personal ORDER BY tipo, cargo")

    descripciones = {
        "Coordinador logístico (Gerente)": "Gestión general del negocio, planificación de operaciones y control financiero.",
        "Asistente contable": "Registro de ingresos/egresos, reportes financieros y cumplimiento tributario.",
        "Responsable de marketing": "Captación de clientes, posicionamiento del servicio y relación con productores.",
        "Chofer de transporte": "Conducción del vehículo y cumplimiento de rutas y tiempos de entrega.",
        "Ayudante del chofer": "Apoyo en carga/descarga y supervisión del estado de la mercadería.",
        "Estibador (carga/descarga)": "Carga y descarga de cajas de tuna, evitando pérdidas o daños.",
    }

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 👷 Mano de Obra Directa")
        for _, r in personal[personal['tipo'] == 'Directa'].iterrows():
            st.markdown(f"**{r['nombre']}** — *{r['cargo']}*")
            st.caption(descripciones.get(r['cargo'], ""))
            st.markdown(badge(r['estado'], "ok" if r['estado'] == "Activo" else "warn"), unsafe_allow_html=True)
            st.markdown("---")
    with col2:
        st.markdown("#### 🗂️ Mano de Obra Indirecta")
        for _, r in personal[personal['tipo'] == 'Indirecta'].iterrows():
            st.markdown(f"**{r['nombre']}** — *{r['cargo']}*")
            st.caption(descripciones.get(r['cargo'], ""))
            st.markdown(badge(r['estado'], "ok" if r['estado'] == "Activo" else "warn"), unsafe_allow_html=True)
            st.markdown("---")

    st.markdown("##### Carga operativa por chofer (viajes asignados)")
    viajes = df_query("""
        SELECT p.nombre AS chofer, COUNT(*) AS viajes, SUM(v.cantidad_cajas) AS cajas
        FROM viajes v JOIN personal p ON v.chofer_id = p.id
        GROUP BY p.nombre
    """)
    if len(viajes):
        fig = px.bar(viajes, x='chofer', y='viajes', text='cajas', color_discrete_sequence=[ACCENT])
        fig.update_layout(height=300, xaxis_title="", yaxis_title="N° de viajes")
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("➕ Registrar nuevo colaborador"):
        with st.form("nuevo_personal_form"):
            nombre = st.text_input("Nombre completo")
            cargo = st.selectbox("Cargo", list(descripciones.keys()))
            tipo = st.selectbox("Tipo de mano de obra", ["Directa", "Indirecta"])
            telefono = st.text_input("Teléfono")
            ok = st.form_submit_button("Registrar")
            if ok and nombre:
                execute(
                    "INSERT INTO personal (nombre, cargo, tipo, telefono) VALUES (?,?,?,?)",
                    (nombre, cargo, tipo, telefono),
                )
                st.success(f"Colaborador **{nombre}** registrado.")
                st.rerun()


# ============================================================
# MÓDULO: FLOTA Y MANTENIMIENTO
# ============================================================

def modulo_flota():
    st.markdown("<h3 class='section-title'>Flota y Mantenimiento</h3>", unsafe_allow_html=True)

    flota = df_query("SELECT * FROM flota")
    c1, c2, c3 = st.columns(3)
    c1.metric("Unidades registradas", len(flota))
    c2.metric("Operativas", len(flota[flota['estado'] == 'Operativo']))
    c3.metric("En mantenimiento / inactivas", len(flota[flota['estado'] != 'Operativo']))

    for _, r in flota.iterrows():
        with st.container(border=True):
            cc1, cc2, cc3, cc4 = st.columns([1.2, 1, 1, 1])
            cc1.markdown(f"**🚛 {r['placa']}** · {r['tipo']}")
            cc2.markdown(f"Capacidad: **{r['capacidad_cajas']} cajas**")
            cc3.markdown(f"Km recorridos: **{r['km_recorridos']:,.0f} km**")
            kind = "ok" if r['estado'] == "Operativo" else ("warn" if r['estado'] == "Mantenimiento" else "bad")
            cc4.markdown(badge(r['estado'], kind), unsafe_allow_html=True)
            st.caption(f"Último mantenimiento: {r['ultimo_mantenimiento']}")

    st.markdown("##### Actualizar estado de unidad")
    if len(flota):
        sel = st.selectbox("Vehículo", flota['placa'])
        nuevo_estado = st.selectbox("Nuevo estado", ["Operativo", "Mantenimiento", "Inactivo"])
        fecha_mant = st.date_input("Fecha de mantenimiento (si aplica)", value=date.today())
        if st.button("Actualizar unidad"):
            vid = int(flota[flota['placa'] == sel]['id'].iloc[0])
            execute("UPDATE flota SET estado=?, ultimo_mantenimiento=? WHERE id=?",
                    (nuevo_estado, fecha_mant.strftime("%Y-%m-%d"), vid))
            st.success(f"Vehículo {sel} actualizado a estado: {nuevo_estado}")
            st.rerun()

    st.markdown("---")
    st.markdown("##### Camión de respaldo y contingencia")
    st.info("""
    Conforme al diseño del proyecto, ante una falla del vehículo principal o mantenimiento programado,
    se activa el **camión de respaldo** para no interrumpir el servicio, financiado dentro de los
    Costos Indirectos de Fabricación (alquiler de camión en caso fortuito / mantenimiento).
    """)


# ============================================================
# MÓDULO: COSTOS E INGRESOS
# ============================================================

def modulo_costos():
    st.markdown("<h3 class='section-title'>Costos e Ingresos Operativos</h3>", unsafe_allow_html=True)

    costos = df_query("SELECT c.*, v.codigo FROM costos c LEFT JOIN viajes v ON c.viaje_id = v.id")
    pagos = df_query("SELECT p.*, v.codigo FROM pagos p LEFT JOIN viajes v ON p.viaje_id = v.id")

    total_costos = costos['monto'].sum() if len(costos) else 0
    total_ingresos = pagos['monto'].sum() if len(pagos) else 0
    margen = total_ingresos - total_costos

    c1, c2, c3 = st.columns(3)
    c1.metric("Ingresos por viajes", f"S/ {total_ingresos:,.2f}")
    c2.metric("Costos operativos", f"S/ {total_costos:,.2f}")
    c3.metric("Margen operativo", f"S/ {margen:,.2f}", delta=f"{(margen/total_ingresos*100 if total_ingresos else 0):.1f}%")

    tab1, tab2, tab3 = st.tabs(["📤 Costos por categoría", "📥 Cuentas por cobrar", "➕ Registrar movimiento"])

    with tab1:
        if len(costos):
            resumen = costos.groupby('categoria')['monto'].sum().reset_index().sort_values('monto', ascending=False)
            cc1, cc2 = st.columns([1, 1.2])
            with cc1:
                fig = px.pie(resumen, names='categoria', values='monto', hole=0.4)
                fig.update_layout(height=320)
                st.plotly_chart(fig, use_container_width=True)
            with cc2:
                st.dataframe(resumen.rename(columns={'categoria': 'Categoría', 'monto': 'Monto (S/.)'}),
                             use_container_width=True, height=320)
            st.markdown("##### Detalle de costos")
            st.dataframe(
                costos[['codigo', 'categoria', 'descripcion', 'monto', 'fecha']].rename(
                    columns={'codigo': 'Viaje', 'categoria': 'Categoría', 'descripcion': 'Descripción',
                             'monto': 'Monto (S/.)', 'fecha': 'Fecha'}
                ).sort_values('Fecha', ascending=False),
                use_container_width=True, height=300
            )
        else:
            st.info("No hay costos registrados todavía.")

    with tab2:
        if len(pagos):
            pend = pagos[pagos['estado'] == 'Pendiente']
            pag = pagos[pagos['estado'] == 'Pagado']
            cc1, cc2 = st.columns(2)
            cc1.metric("Pendiente de cobro", f"S/ {pend['monto'].sum():,.2f}", f"{len(pend)} viaje(s)")
            cc2.metric("Cobrado", f"S/ {pag['monto'].sum():,.2f}", f"{len(pag)} viaje(s)")

            st.markdown("##### Marcar pago como cobrado")
            if len(pend):
                sel = st.selectbox("Seleccionar viaje pendiente", pend['codigo'])
                if st.button("✅ Registrar cobro"):
                    pid = int(pend[pend['codigo'] == sel]['id'].iloc[0])
                    execute("UPDATE pagos SET estado='Pagado', fecha_pago=? WHERE id=?",
                            (datetime.now().strftime("%Y-%m-%d"), pid))
                    st.success(f"Pago del viaje {sel} registrado como cobrado.")
                    st.rerun()

            st.dataframe(
                pagos[['codigo', 'monto', 'estado', 'fecha_emision', 'fecha_pago']].rename(
                    columns={'codigo': 'Viaje', 'monto': 'Monto (S/.)', 'estado': 'Estado',
                             'fecha_emision': 'Emisión', 'fecha_pago': 'Fecha de pago'}
                ).sort_values('Emisión', ascending=False),
                use_container_width=True, height=300
            )

    with tab3:
        viajes_lista = df_query("SELECT id, codigo FROM viajes ORDER BY fecha_salida DESC")
        with st.form("nuevo_costo_form"):
            viaje_sel = st.selectbox("Viaje asociado", viajes_lista['codigo'])
            categoria = st.selectbox("Categoría de costo", ["Combustible", "Peajes", "Mantenimiento", "Materiales", "Otros"])
            descripcion = st.text_input("Descripción")
            monto = st.number_input("Monto (S/.)", min_value=0.0, step=10.0)
            fecha = st.date_input("Fecha", value=date.today())
            ok = st.form_submit_button("Registrar costo")
            if ok and monto > 0:
                vid = int(viajes_lista[viajes_lista['codigo'] == viaje_sel]['id'].iloc[0])
                execute(
                    "INSERT INTO costos (viaje_id, categoria, descripcion, monto, fecha) VALUES (?,?,?,?,?)",
                    (vid, categoria, descripcion, monto, fecha.strftime("%Y-%m-%d")),
                )
                st.success("Costo registrado correctamente.")
                st.rerun()


# ============================================================
# MÓDULO: SEGUIMIENTO EN VIVO
# ============================================================

def modulo_seguimiento():
    st.markdown("<h3 class='section-title'>📍 Seguimiento de Envíos en Tiempo Real</h3>", unsafe_allow_html=True)
    st.caption("Simulación del sistema de monitoreo y seguimiento de mercancías del software Chaski Track.")

    viajes = df_query("""
        SELECT v.id, v.codigo, c.nombre AS cliente, p.nombre AS chofer, f.placa AS vehiculo,
               v.estado, v.avance_pct, v.fecha_salida, v.fecha_entrega_estimada,
               v.cantidad_cajas, v.incidencia
        FROM viajes v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        LEFT JOIN personal p ON v.chofer_id = p.id
        LEFT JOIN flota f ON v.vehiculo_id = f.id
        WHERE v.estado IN ('Programado','En tránsito','Incidencia')
        ORDER BY v.fecha_salida DESC
    """)

    if not len(viajes):
        st.success("✅ No hay viajes en tránsito en este momento. Todos los envíos han sido entregados.")
    else:
        for _, r in viajes.iterrows():
            with st.container(border=True):
                col1, col2, col3 = st.columns([1.4, 1, 1])
                with col1:
                    st.markdown(f"### {r['codigo']}")
                    st.markdown(f"**Cliente:** {r['cliente']}")
                    st.markdown(f"**Chofer:** {r['chofer']} · **Vehículo:** {r['vehiculo']}")
                    st.markdown("**Ruta:** Ayacucho ➜ Mercado Mayorista N°2, Lima")
                with col2:
                    st.markdown(f"**Salida:** {r['fecha_salida']}")
                    st.markdown(f"**Entrega estimada:** {r['fecha_entrega_estimada']}")
                    st.markdown(f"**Carga:** {r['cantidad_cajas']} cajas")
                with col3:
                    kind = estado_kind(r['estado'])
                    st.markdown(badge(r['estado'], kind), unsafe_allow_html=True)
                    if r['incidencia']:
                        st.warning(f"⚠️ {r['incidencia']}")

                st.progress(int(r['avance_pct']) / 100, text=f"Avance del viaje: {r['avance_pct']}%")

                hist = df_query("SELECT evento, detalle, timestamp FROM seguimiento WHERE viaje_id=? ORDER BY timestamp",
                                (int(r['id']),))
                with st.expander("📜 Historial de eventos del viaje"):
                    for _, h in hist.iterrows():
                        st.markdown(f"- **{h['timestamp']}** — *{h['evento']}*: {h['detalle']}")

    st.markdown("---")
    st.markdown("##### Buscar un envío por código")
    codigo_busqueda = st.text_input("Ingresa el código de viaje (ej. ACHS-0005)")
    if codigo_busqueda:
        res = df_query("""
            SELECT v.*, c.nombre AS cliente, p.nombre AS chofer, f.placa AS vehiculo
            FROM viajes v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            LEFT JOIN personal p ON v.chofer_id = p.id
            LEFT JOIN flota f ON v.vehiculo_id = f.id
            WHERE v.codigo LIKE ?
        """, (f"%{codigo_busqueda}%",))
        if len(res):
            r = res.iloc[0]
            st.success(f"Viaje {r['codigo']} — Estado: {r['estado']} — Avance: {r['avance_pct']}%")
            st.json({
                "Cliente": r['cliente'], "Chofer": r['chofer'], "Vehículo": r['vehiculo'],
                "Origen": r['origen'], "Destino": r['destino'],
                "Cajas": int(r['cantidad_cajas']), "Tarifa por caja": f"S/ {r['tarifa_caja']}",
                "Total estimado": f"S/ {r['cantidad_cajas']*r['tarifa_caja']:,.2f}",
            })
        else:
            st.error("No se encontró ningún viaje con ese código.")


# ============================================================
# MÓDULO: REPORTES
# ============================================================

def modulo_reportes():
    st.markdown("<h3 class='section-title'>📊 Reportes Operativos y Financieros</h3>", unsafe_allow_html=True)

    viajes = df_query("SELECT * FROM viajes")
    pagos = df_query("SELECT * FROM pagos")
    costos = df_query("SELECT * FROM costos")
    clientes = df_query("SELECT * FROM clientes")

    if not len(viajes):
        st.info("No hay datos suficientes para generar reportes.")
        return

    rango = st.date_input("Rango de fechas para el reporte",
                           value=(pd.to_datetime(viajes['fecha_salida']).min().date(),
                                  pd.to_datetime(viajes['fecha_salida']).max().date()))
    viajes['fecha'] = pd.to_datetime(viajes['fecha_salida']).dt.date
    if isinstance(rango, tuple) and len(rango) == 2:
        vf = viajes[(viajes['fecha'] >= rango[0]) & (viajes['fecha'] <= rango[1])]
    else:
        vf = viajes

    ids = vf['id'].tolist()
    cf = costos[costos['viaje_id'].isin(ids)]
    pf = pagos[pagos['viaje_id'].isin(ids)]

    total_cajas = int(vf['cantidad_cajas'].sum())
    total_ingresos = float((vf['cantidad_cajas'] * vf['tarifa_caja']).sum())
    total_costos = float(cf['monto'].sum())
    merma_total = int(vf['merma_cajas'].sum())
    margen = total_ingresos - total_costos

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Viajes en el periodo", len(vf))
    c2.metric("Cajas transportadas", f"{total_cajas:,}")
    c3.metric("Ingresos", f"S/ {total_ingresos:,.2f}")
    c4.metric("Costos", f"S/ {total_costos:,.2f}")
    c5.metric("Margen operativo", f"S/ {margen:,.2f}")

    st.markdown("##### Eficiencia operativa")
    entregados = vf[vf['estado'] == 'Entregado']
    on_time = 0
    if len(entregados):
        e = entregados.copy()
        e['estim'] = pd.to_datetime(e['fecha_entrega_estimada'])
        e['real'] = pd.to_datetime(e['fecha_entrega_real'])
        on_time = (e['real'] <= e['estim']).mean() * 100
    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("Entregas a tiempo", f"{on_time:.1f}%")
    cc2.metric("Merma total (cajas)", merma_total)
    cc3.metric("Incidencias", len(vf[vf['estado'] == 'Incidencia']))

    st.markdown("---")
    colA, colB = st.columns(2)
    with colA:
        st.markdown("##### Ingresos vs Costos por mes")
        vf2 = vf.copy()
        vf2['mes'] = pd.to_datetime(vf2['fecha_salida']).dt.to_period('M').astype(str)
        vf2['ingreso'] = vf2['cantidad_cajas'] * vf2['tarifa_caja']
        ing_mes = vf2.groupby('mes')['ingreso'].sum().reset_index()
        cf2 = cf.merge(vf2[['id', 'mes']], left_on='viaje_id', right_on='id', how='left')
        costo_mes = cf2.groupby('mes')['monto'].sum().reset_index()
        comp = ing_mes.merge(costo_mes, on='mes', how='outer').fillna(0)
        fig = go.Figure()
        fig.add_bar(x=comp['mes'], y=comp['ingreso'], name='Ingresos', marker_color=SECONDARY)
        fig.add_bar(x=comp['mes'], y=comp['monto'], name='Costos', marker_color=DANGER)
        fig.update_layout(barmode='group', height=320)
        st.plotly_chart(fig, use_container_width=True)

    with colB:
        st.markdown("##### Distribución de estados de viaje")
        conteo = vf['estado'].value_counts().reset_index()
        conteo.columns = ['Estado', 'Cantidad']
        fig2 = px.pie(conteo, names='Estado', values='Cantidad', hole=0.45)
        fig2.update_layout(height=320)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown("##### Exportar reporte")
    export_df = vf.merge(clientes, left_on='cliente_id', right_on='id', suffixes=('', '_cli'))
    export_df['ingreso (S/.)'] = export_df['cantidad_cajas'] * export_df['tarifa_caja']
    export_cols = ['codigo', 'nombre', 'fecha_salida', 'fecha_entrega_estimada', 'fecha_entrega_real',
                   'cantidad_cajas', 'ingreso (S/.)', 'estado', 'merma_cajas']
    export_final = export_df[export_cols].rename(columns={
        'codigo': 'Código', 'nombre': 'Cliente', 'fecha_salida': 'Salida',
        'fecha_entrega_estimada': 'Entrega Estimada', 'fecha_entrega_real': 'Entrega Real',
        'cantidad_cajas': 'Cajas', 'estado': 'Estado', 'merma_cajas': 'Merma'
    })

    csv = export_final.to_csv(index=False).encode('utf-8-sig')
    st.download_button("⬇️ Descargar reporte en CSV", csv, file_name="reporte_chaski_track.csv", mime="text/csv")

    st.dataframe(export_final, use_container_width=True, height=320)


# ============================================================
# RUTEO DE SECCIONES
# ============================================================

SECCION_FN = {
    "🏠 Dashboard": modulo_dashboard,
    "🧾 Pedidos y Viajes": modulo_pedidos,
    "👥 Clientes": modulo_clientes,
    "👷 Personal": modulo_personal,
    "🚛 Flota y Mantenimiento": modulo_flota,
    "💰 Costos e Ingresos": modulo_costos,
    "📍 Seguimiento en Vivo": modulo_seguimiento,
    "📊 Reportes": modulo_reportes,
}

SECCION_FN.get(seccion, modulo_dashboard)()

st.markdown("---")
st.caption(
    "Chaski Track © 2026 · Plataforma de simulación operativa desarrollada para el curso "
    "Evaluación Financiera de Proyectos (GI4101) - UTEC. Los datos mostrados son de demostración "
    "y se basan en los supuestos definidos en el informe del proyecto."
)
