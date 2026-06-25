# -*- coding: utf-8 -*-
"""
CHASKI TRACK - Plataforma de Gestión del Proyecto de Transporte de Tunas
Servicio de Flete Ayacucho -> Mercado Mayorista de Frutas N° 2, Lima
Proyecto: Evaluación Financiera de Proyectos (GI4101) - UTEC

Autor: Grupo PC2 - Huanuco Mayta, Puma Mamani, Vargas Inga, Viracocha Cruz

Módulos:
    1. Inicio / Dashboard
    2. Usuarios del sistema
    3. Registro de clientes
    4. Registro de viajes o fletes
    5. Control de unidades / vehículos
    6. Costos e ingresos
    7. Reportes
    8. Panel de seguimiento

Ejecutar:
    streamlit run chaski_track_platform.py
"""

import sqlite3
import random
import hashlib
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
    page_title="Chaski Track | Transporte de Tunas",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY = "#1B5E20"
SECONDARY = "#2E7D32"
ACCENT = "#F9A825"
DANGER = "#C62828"
INFO = "#1565C0"
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
.badge {{
    display:inline-block; padding:3px 10px; border-radius:20px;
    font-size:12px; font-weight:600; color:white;
}}
.badge-ok {{ background-color: {SECONDARY}; }}
.badge-warn {{ background-color: {ACCENT}; color:#3a2f00; }}
.badge-bad {{ background-color: {DANGER}; }}
.badge-info {{ background-color: {INFO}; }}
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
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    usuario TEXT UNIQUE NOT NULL,
    clave_hash TEXT NOT NULL,
    rol TEXT NOT NULL,         -- Administrador / Transportista / Cliente / Operador logístico
    telefono TEXT,
    estado TEXT DEFAULT 'Activo',
    fecha_registro TEXT
);

CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    empresa TEXT,
    contacto TEXT,
    ubicacion TEXT,
    tipo_carga TEXT DEFAULT 'Tuna',
    fecha_registro TEXT
);

CREATE TABLE IF NOT EXISTS vehiculos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    placa TEXT NOT NULL,
    capacidad_cajas INTEGER,
    chofer_asignado TEXT,
    estado TEXT DEFAULT 'Operativo',     -- Operativo / Mantenimiento / Inactivo
    km_recorridos REAL DEFAULT 0,
    ultimo_mantenimiento TEXT,
    proximo_mantenimiento TEXT
);

CREATE TABLE IF NOT EXISTS viajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE,
    cliente_id INTEGER,
    origen TEXT DEFAULT 'Ayacucho',
    destino TEXT DEFAULT 'Mercado Mayorista de Frutas N°2 - Lima',
    fecha TEXT,
    fecha_entrega_estimada TEXT,
    fecha_entrega_real TEXT,
    cantidad_cajas INTEGER,
    tarifa_caja REAL DEFAULT 21.0,
    costo_viaje REAL,
    vehiculo_id INTEGER,
    chofer TEXT,
    estado TEXT DEFAULT 'Pendiente',   -- Pendiente / En ruta / Entregado / Incidencia / Cancelado
    avance_pct INTEGER DEFAULT 0,
    incidencia TEXT,
    merma_cajas INTEGER DEFAULT 0,
    observaciones TEXT,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id)
);

CREATE TABLE IF NOT EXISTS costos_ingresos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    viaje_id INTEGER,
    combustible REAL DEFAULT 0,
    peajes REAL DEFAULT 0,
    pago_chofer REAL DEFAULT 0,
    mantenimiento REAL DEFAULT 0,
    otros REAL DEFAULT 0,
    ingreso_viaje REAL DEFAULT 0,
    fecha TEXT,
    FOREIGN KEY (viaje_id) REFERENCES viajes(id)
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


def hash_clave(clave: str) -> str:
    return hashlib.sha256(clave.encode()).hexdigest()


# ============================================================
# AUTO-SEED (datos iniciales basados en el informe del proyecto)
# ============================================================

USUARIOS_SEED = [
    ("Marco Cárdenas Soto", "admin", "admin123", "Administrador", "999 112 233"),
    ("Juan Carlos Quispe", "jquispe", "chofer123", "Transportista / Conductor", "987 654 321"),
    ("Comercial Frutera Lima Norte", "cfrutera", "cliente123", "Cliente", "01-3349812"),
    ("Lucía Fernández Paredes", "lfernandez", "operador123", "Operador logístico", "955 220 884"),
]

CLIENTES_SEED = [
    ("Asociación de Productores de Tuna Cangallo", "Asoc. Productores Cangallo", "066-441122", "Ayacucho - Cangallo", "Tuna"),
    ("Eusebio Mendoza Ttito", "Productor independiente", "966-552231", "Ayacucho - Vischongo", "Tuna"),
    ("Comercial Frutera Lima Norte", "Comercial Frutera Lima Norte SAC", "01-3349812", "Mercado Mayorista N°2", "Tuna"),
    ("Tula Rojas Quispe", "Doña Tula Distribuidora", "01-4471092", "Mercado Mayorista N°2", "Tuna"),
    ("Frutos del Sur SAC", "Frutos del Sur SAC", "01-2280456", "Mercado Mayorista N°2", "Tuna"),
    ("Cooperativa Agro Huamanga", "Productores Huamanga Agro", "066-778455", "Ayacucho - Huamanga", "Tuna"),
]

VEHICULOS_SEED = [
    ("AYA-1024", 300, "Juan Carlos Quispe", "Operativo", 18450, "2026-04-12", "2026-08-12"),
    ("AYA-7790", 270, "Sin asignar (respaldo)", "Operativo", 5210, "2026-05-02", "2026-09-02"),
]

ESTADOS_VIAJE = ["Pendiente", "En ruta", "Entregado", "Incidencia", "Cancelado"]
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

    cur.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone()[0] == 0:
        hoy = datetime.now().strftime("%Y-%m-%d")
        for nombre, usuario, clave, rol, tel in USUARIOS_SEED:
            cur.execute(
                "INSERT INTO usuarios (nombre, usuario, clave_hash, rol, telefono, fecha_registro) VALUES (?,?,?,?,?,?)",
                (nombre, usuario, hash_clave(clave), rol, tel, hoy),
            )

    cur.execute("SELECT COUNT(*) FROM clientes")
    if cur.fetchone()[0] == 0:
        hoy_dt = datetime.now()
        rows = [(n, e, c, u, t, (hoy_dt - timedelta(days=random.randint(10, 400))).strftime("%Y-%m-%d"))
                for (n, e, c, u, t) in CLIENTES_SEED]
        cur.executemany(
            "INSERT INTO clientes (nombre, empresa, contacto, ubicacion, tipo_carga, fecha_registro) VALUES (?,?,?,?,?,?)",
            rows,
        )

    cur.execute("SELECT COUNT(*) FROM vehiculos")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO vehiculos (placa, capacidad_cajas, chofer_asignado, estado, km_recorridos, "
            "ultimo_mantenimiento, proximo_mantenimiento) VALUES (?,?,?,?,?,?,?)",
            VEHICULOS_SEED,
        )
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM viajes")
    if cur.fetchone()[0] == 0:
        cur.execute("SELECT id FROM clientes")
        cliente_ids = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT id, placa, chofer_asignado FROM vehiculos")
        vehiculos = cur.fetchall()

        hoy = datetime.now()
        n_viajes = 30
        for i in range(1, n_viajes + 1):
            dias_atras = random.randint(0, 45)
            f_salida = hoy - timedelta(days=dias_atras, hours=random.randint(0, 10))
            f_estimada = f_salida + timedelta(hours=20)
            cajas = random.choice([140, 150, 160, 180, 200, 220, 260, 300])
            tarifa = 21.0
            vehiculo = random.choice(vehiculos)
            vehiculo_id, placa, chofer = vehiculo
            chofer_real = chofer if chofer != "Sin asignar (respaldo)" else "Juan Carlos Quispe"

            if dias_atras <= 1:
                estado = random.choice(["Pendiente", "En ruta"])
                avance = 0 if estado == "Pendiente" else random.randint(15, 80)
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
            combustible = round(random.uniform(420, 520), 2)
            peajes = round(random.uniform(55, 70), 2)
            pago_chofer = round(random.uniform(180, 260), 2)
            mantenimiento = round(random.uniform(0, 150), 2) if random.random() < 0.15 else 0
            ingreso_viaje = round(cajas * tarifa, 2)
            costo_total_viaje = round(combustible + peajes + pago_chofer + mantenimiento, 2)

            cur.execute(
                """INSERT INTO viajes
                (codigo, cliente_id, origen, destino, fecha, fecha_entrega_estimada, fecha_entrega_real,
                 cantidad_cajas, tarifa_caja, costo_viaje, vehiculo_id, chofer, estado, avance_pct,
                 incidencia, merma_cajas, observaciones)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    codigo_viaje(i), random.choice(cliente_ids), "Ayacucho",
                    "Mercado Mayorista de Frutas N°2 - Lima",
                    f_salida.strftime("%Y-%m-%d %H:%M"), f_estimada.strftime("%Y-%m-%d %H:%M"),
                    f_real.strftime("%Y-%m-%d %H:%M") if f_real else None,
                    cajas, tarifa, costo_total_viaje, vehiculo_id, chofer_real, estado, avance,
                    incid, merma, "Viaje generado en carga inicial de demostración.",
                ),
            )
            viaje_id = cur.lastrowid

            cur.execute(
                """INSERT INTO costos_ingresos
                (viaje_id, combustible, peajes, pago_chofer, mantenimiento, otros, ingreso_viaje, fecha)
                VALUES (?,?,?,?,?,?,?,?)""",
                (viaje_id, combustible, peajes, pago_chofer, mantenimiento, 0, ingreso_viaje,
                 f_salida.strftime("%Y-%m-%d")),
            )

            eventos = [("Viaje registrado", "Pedido programado y asignado a unidad de transporte")]
            if estado in ("En ruta", "Entregado", "Incidencia"):
                eventos.append(("En ruta", "Camión en tránsito hacia Lima"))
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
        "Pendiente": "info",
        "En ruta": "warn",
        "Entregado": "ok",
        "Incidencia": "bad",
        "Cancelado": "bad",
    }.get(estado, "info")


# ============================================================
# SIDEBAR — LOGIN / SELECCIÓN DE ROL
# ============================================================

ROLES_MENU = {
    "Administrador": ["1. Inicio / Dashboard", "2. Usuarios del sistema", "3. Registro de clientes",
                       "4. Registro de viajes o fletes", "5. Control de unidades / vehículos",
                       "6. Costos e ingresos", "7. Reportes", "8. Panel de seguimiento"],
    "Transportista / Conductor": ["1. Inicio / Dashboard", "4. Registro de viajes o fletes",
                                   "8. Panel de seguimiento"],
    "Cliente": ["1. Inicio / Dashboard", "8. Panel de seguimiento"],
    "Operador logístico": ["1. Inicio / Dashboard", "3. Registro de clientes",
                            "4. Registro de viajes o fletes", "5. Control de unidades / vehículos",
                            "7. Reportes", "8. Panel de seguimiento"],
}

with st.sidebar:
    st.markdown("## 🚚 CHASKI TRACK")
    st.caption("Plataforma de Gestión del Proyecto de Transporte de Tunas")
    st.divider()

    rol_sel = st.selectbox("Ingresar como:", list(ROLES_MENU.keys()), index=0)
    usuarios_rol = df_query("SELECT nombre, usuario FROM usuarios WHERE rol=?", (rol_sel,))
    if len(usuarios_rol):
        usuario_actual = st.selectbox("Usuario", usuarios_rol['nombre'])
    else:
        usuario_actual = rol_sel
    st.success(f"Sesión activa: **{usuario_actual}**\n\nRol: *{rol_sel}*")

    st.divider()
    seccion = st.radio("Navegación", ROLES_MENU[rol_sel])

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

st.title("🚚 Chaski Track")
st.caption("Plataforma de Gestión del Proyecto de Transporte de Tunas · Ayacucho → Mercado Mayorista de Frutas N°2, Lima")
st.markdown("---")

# ============================================================
# MÓDULO 1: INICIO / DASHBOARD
# ============================================================

def modulo_dashboard():
    st.markdown("<h3 class='section-title'>1. Inicio / Dashboard</h3>", unsafe_allow_html=True)

    st.markdown("""
    **Resumen del proyecto:** Servicio de transporte de carga (flete) especializado en el traslado
    de cajas de tuna desde las zonas productoras de Ayacucho hacia el Mercado Mayorista de Frutas
    N° 2 de Lima, mediante una unidad principal con sistema de monitoreo y seguimiento en tiempo real.
    """)

    viajes = df_query("SELECT * FROM viajes")
    clientes = df_query("SELECT * FROM clientes")
    vehiculos = df_query("SELECT * FROM vehiculos")
    ci = df_query("SELECT * FROM costos_ingresos")

    total_viajes = len(viajes)
    pedidos_registrados = total_viajes
    ingresos_estimados = ci['ingreso_viaje'].sum() if len(ci) else 0
    unidades_operativas = len(vehiculos[vehiculos['estado'] == 'Operativo'])
    unidades_totales = len(vehiculos)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("N° de viajes", total_viajes)
    c2.metric("Ingresos estimados", f"S/ {ingresos_estimados:,.2f}")
    c3.metric("Pedidos registrados", pedidos_registrados)
    c4.metric("Estado de unidades", f"{unidades_operativas}/{unidades_totales} operativas")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Clientes registrados", len(clientes))
    c6.metric("Viajes en ruta", len(viajes[viajes['estado'] == 'En ruta']) if total_viajes else 0)
    c7.metric("Entregados", len(viajes[viajes['estado'] == 'Entregado']) if total_viajes else 0)
    c8.metric("Incidencias", len(viajes[viajes['estado'] == 'Incidencia']) if total_viajes else 0)

    st.markdown("---")
    col1, col2 = st.columns([1.3, 1])
    with col1:
        st.markdown("##### Estado actual de los viajes")
        if total_viajes:
            conteo = viajes['estado'].value_counts().reset_index()
            conteo.columns = ['Estado', 'Cantidad']
            fig = px.bar(conteo, x='Estado', y='Cantidad', color='Estado', text='Cantidad',
                         color_discrete_map={
                             "Pendiente": INFO, "En ruta": ACCENT, "Entregado": SECONDARY,
                             "Incidencia": DANGER, "Cancelado": "#777"
                         })
            fig.update_layout(showlegend=False, height=320, margin=dict(t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("##### Estado de unidades vehiculares")
        if len(vehiculos):
            fig2 = px.pie(vehiculos, names='estado', hole=0.45,
                          color_discrete_sequence=[SECONDARY, ACCENT, DANGER])
            fig2.update_layout(height=320, margin=dict(t=10, b=0))
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("##### Evolución de viajes (últimos 45 días)")
    if total_viajes:
        v = viajes.copy()
        v['f'] = pd.to_datetime(v['fecha']).dt.date
        serie = v.groupby('f').size().reset_index(name='viajes')
        fig3 = px.area(serie, x='f', y='viajes', color_discrete_sequence=[SECONDARY])
        fig3.update_layout(height=260, margin=dict(t=10, b=0))
        st.plotly_chart(fig3, use_container_width=True)


# ============================================================
# MÓDULO 2: USUARIOS DEL SISTEMA
# ============================================================

def modulo_usuarios():
    st.markdown("<h3 class='section-title'>2. Usuarios del Sistema</h3>", unsafe_allow_html=True)
    st.caption("Roles: Administrador · Transportista / Conductor · Cliente · Operador logístico")

    tab1, tab2 = st.tabs(["👥 Listado de usuarios", "➕ Registrar usuario"])

    with tab1:
        usuarios = df_query("SELECT id, nombre, usuario, rol, telefono, estado, fecha_registro FROM usuarios")
        c1, c2, c3, c4 = st.columns(4)
        for col, r in zip([c1, c2, c3, c4], ROLES_MENU.keys()):
            col.metric(r, len(usuarios[usuarios['rol'] == r]))

        st.dataframe(
            usuarios.rename(columns={
                'nombre': 'Nombre', 'usuario': 'Usuario', 'rol': 'Rol',
                'telefono': 'Teléfono / Contacto', 'estado': 'Estado', 'fecha_registro': 'Registrado el'
            }),
            use_container_width=True, height=320
        )

        st.markdown("##### Activar / Desactivar usuario")
        if len(usuarios):
            sel = st.selectbox("Selecciona un usuario", usuarios['usuario'])
            row = usuarios[usuarios['usuario'] == sel].iloc[0]
            nuevo_estado = st.selectbox("Estado", ["Activo", "Inactivo"],
                                         index=0 if row['estado'] == "Activo" else 1)
            if st.button("Guardar cambio de estado"):
                execute("UPDATE usuarios SET estado=? WHERE id=?", (nuevo_estado, int(row['id'])))
                st.success(f"Usuario {sel} actualizado a estado: {nuevo_estado}")
                st.rerun()

    with tab2:
        with st.form("nuevo_usuario_form"):
            nombre = st.text_input("Nombre completo")
            usuario = st.text_input("Usuario (login)")
            clave = st.text_input("Contraseña", type="password")
            rol = st.selectbox("Rol del sistema", list(ROLES_MENU.keys()))
            telefono = st.text_input("Teléfono / Contacto")
            ok = st.form_submit_button("Registrar usuario", type="primary")
            if ok and nombre and usuario and clave:
                existentes = df_query("SELECT id FROM usuarios WHERE usuario=?", (usuario,))
                if len(existentes):
                    st.error("Ya existe un usuario con ese nombre de login.")
                else:
                    execute(
                        "INSERT INTO usuarios (nombre, usuario, clave_hash, rol, telefono, fecha_registro) "
                        "VALUES (?,?,?,?,?,?)",
                        (nombre, usuario, hash_clave(clave), rol, telefono, datetime.now().strftime("%Y-%m-%d")),
                    )
                    st.success(f"Usuario **{nombre}** registrado con rol **{rol}**.")
                    st.rerun()

    st.markdown("---")
    st.markdown("##### Permisos por rol")
    permisos = pd.DataFrame({
        "Módulo": ["Dashboard", "Usuarios del sistema", "Registro de clientes", "Registro de viajes",
                   "Control de vehículos", "Costos e ingresos", "Reportes", "Panel de seguimiento"],
        "Administrador": ["✅"] * 8,
        "Transportista / Conductor": ["✅", "❌", "❌", "✅", "❌", "❌", "❌", "✅"],
        "Cliente": ["✅", "❌", "❌", "❌", "❌", "❌", "❌", "✅"],
        "Operador logístico": ["✅", "❌", "✅", "✅", "✅", "❌", "✅", "✅"],
    })
    st.dataframe(permisos, use_container_width=True, hide_index=True)


# ============================================================
# MÓDULO 3: REGISTRO DE CLIENTES
# ============================================================

def modulo_clientes():
    st.markdown("<h3 class='section-title'>3. Registro de Clientes</h3>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📇 Listado de clientes", "➕ Registrar cliente"])

    with tab1:
        clientes = df_query("SELECT * FROM clientes ORDER BY nombre")
        viajes = df_query("SELECT cliente_id, cantidad_cajas, tarifa_caja FROM viajes")

        resumen = viajes.groupby('cliente_id').agg(
            viajes=('cliente_id', 'count'), cajas=('cantidad_cajas', 'sum')
        ).reset_index()
        if len(viajes):
            resumen['ingreso (S/.)'] = (viajes.assign(ing=viajes['cantidad_cajas'] * viajes['tarifa_caja'])
                                         .groupby('cliente_id')['ing'].sum().values)
        tabla = clientes.merge(resumen, left_on='id', right_on='cliente_id', how='left').fillna(0)

        st.dataframe(
            tabla[['nombre', 'empresa', 'contacto', 'ubicacion', 'tipo_carga', 'viajes', 'cajas', 'ingreso (S/.)']]
            .rename(columns={
                'nombre': 'Nombre', 'empresa': 'Empresa', 'contacto': 'Contacto',
                'ubicacion': 'Ubicación', 'tipo_carga': 'Tipo de carga'
            }),
            use_container_width=True, height=380
        )

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### Clientes por ubicación")
            fig = px.pie(clientes, names='ubicacion', hole=0.45)
            fig.update_layout(height=280)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("##### Top clientes por carga transportada")
            top = tabla.sort_values('cajas', ascending=False).head(6)
            fig2 = px.bar(top, x='nombre', y='cajas', color_discrete_sequence=[SECONDARY])
            fig2.update_layout(height=280, xaxis_title="", margin=dict(t=10))
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        with st.form("nuevo_cliente_form"):
            nombre = st.text_input("Nombre")
            empresa = st.text_input("Empresa")
            contacto = st.text_input("Contacto (teléfono / correo)")
            ubicacion = st.text_input("Ubicación")
            tipo_carga = st.selectbox("Tipo de carga", ["Tuna", "Tuna + Cochinilla", "Otros productos agrícolas"])
            ok = st.form_submit_button("Registrar cliente", type="primary")
            if ok and nombre:
                execute(
                    "INSERT INTO clientes (nombre, empresa, contacto, ubicacion, tipo_carga, fecha_registro) "
                    "VALUES (?,?,?,?,?,?)",
                    (nombre, empresa, contacto, ubicacion, tipo_carga, datetime.now().strftime("%Y-%m-%d")),
                )
                st.success(f"Cliente **{nombre}** registrado correctamente.")
                st.rerun()


# ============================================================
# MÓDULO 4: REGISTRO DE VIAJES O FLETES
# ============================================================

def modulo_viajes():
    st.markdown("<h3 class='section-title'>4. Registro de Viajes o Fletes</h3>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📋 Listado de viajes", "➕ Registrar nuevo viaje"])

    with tab1:
        viajes = df_query("""
            SELECT v.id, v.codigo, c.nombre AS cliente, v.origen, v.destino, v.fecha,
                   v.cantidad_cajas, v.costo_viaje, v.chofer, ve.placa AS vehiculo,
                   v.estado, v.avance_pct, v.merma_cajas, v.incidencia
            FROM viajes v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            LEFT JOIN vehiculos ve ON v.vehiculo_id = ve.id
            ORDER BY v.fecha DESC
        """)

        colf1, colf2, colf3 = st.columns(3)
        with colf1:
            f_estado = st.multiselect("Filtrar por estado", ESTADOS_VIAJE)
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

        st.dataframe(
            vf[['codigo', 'cliente', 'origen', 'destino', 'fecha', 'cantidad_cajas', 'costo_viaje',
                'chofer', 'vehiculo', 'estado', 'avance_pct', 'merma_cajas']].rename(columns={
                'codigo': 'Código', 'cliente': 'Cliente', 'origen': 'Origen', 'destino': 'Destino',
                'fecha': 'Fecha', 'cantidad_cajas': 'Cant. cajas', 'costo_viaje': 'Costo del viaje (S/.)',
                'chofer': 'Chofer', 'vehiculo': 'Vehículo', 'estado': 'Estado',
                'avance_pct': 'Avance (%)', 'merma_cajas': 'Merma'
            }),
            use_container_width=True, height=380
        )

        st.markdown("##### Actualizar estado del viaje")
        if len(vf):
            sel = st.selectbox("Selecciona el código de viaje", vf['codigo'].tolist())
            row = viajes[viajes['codigo'] == sel].iloc[0]
            c1, c2, c3 = st.columns(3)
            with c1:
                nuevo_estado = st.selectbox("Nuevo estado", ESTADOS_VIAJE,
                                             index=ESTADOS_VIAJE.index(row['estado']) if row['estado'] in ESTADOS_VIAJE else 0)
            with c2:
                avance = st.slider("Avance del viaje (%)", 0, 100, int(row['avance_pct']))
            with c3:
                merma = st.number_input("Merma de cajas", min_value=0, value=int(row['merma_cajas']))
            obs = st.text_area("Observación / incidencia", value=row['incidencia'] or "")

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
        st.markdown("##### Registrar un nuevo viaje / flete")
        clientes = df_query("SELECT id, nombre FROM clientes ORDER BY nombre")
        vehiculos = df_query("SELECT id, placa, chofer_asignado, capacidad_cajas FROM vehiculos WHERE estado='Operativo'")

        with st.form("nuevo_viaje_form"):
            c1, c2 = st.columns(2)
            with c1:
                cliente_sel = st.selectbox("Cliente", clientes['nombre'])
                origen = st.text_input("Origen", value="Ayacucho")
                destino = st.text_input("Destino", value="Mercado Mayorista de Frutas N°2 - Lima")
                fecha_viaje = st.date_input("Fecha del viaje", value=date.today())
            with c2:
                vehiculo_sel = st.selectbox(
                    "Vehículo asignado",
                    vehiculos['placa'] if len(vehiculos) else ["Sin vehículo disponible"]
                )
                cajas = st.number_input("Cantidad de cajas (tuna)", min_value=1, max_value=320, value=150, step=10)
                tarifa = st.number_input("Tarifa por caja (S/.)", min_value=1.0, value=21.0, step=0.5)
                costo_estimado = st.number_input("Costo estimado del viaje (S/.)", min_value=0.0, value=750.0, step=10.0)

            obs = st.text_area("Observaciones del viaje")
            submitted = st.form_submit_button("🚚 Registrar viaje", type="primary")

            if submitted:
                cliente_id = int(clientes[clientes['nombre'] == cliente_sel]['id'].iloc[0])
                vehiculo_id, chofer = None, "Por asignar"
                if len(vehiculos):
                    vrow = vehiculos[vehiculos['placa'] == vehiculo_sel].iloc[0]
                    vehiculo_id = int(vrow['id'])
                    chofer = vrow['chofer_asignado']

                f_estimada = datetime.combine(fecha_viaje, datetime.min.time()) + timedelta(hours=20)
                codigo = next_codigo()

                viaje_id = execute(
                    """INSERT INTO viajes
                    (codigo, cliente_id, origen, destino, fecha, fecha_entrega_estimada, cantidad_cajas,
                     tarifa_caja, costo_viaje, vehiculo_id, chofer, estado, avance_pct, observaciones)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (codigo, cliente_id, origen, destino, fecha_viaje.strftime("%Y-%m-%d %H:%M"),
                     f_estimada.strftime("%Y-%m-%d %H:%M"), cajas, tarifa, costo_estimado, vehiculo_id,
                     chofer, "Pendiente", 0, obs),
                )

                ingreso = round(cajas * tarifa, 2)
                execute(
                    """INSERT INTO costos_ingresos
                    (viaje_id, combustible, peajes, pago_chofer, mantenimiento, otros, ingreso_viaje, fecha)
                    VALUES (?,?,?,?,?,?,?,?)""",
                    (viaje_id, round(costo_estimado * 0.62, 2), round(costo_estimado * 0.08, 2),
                     round(costo_estimado * 0.25, 2), 0, round(costo_estimado * 0.05, 2), ingreso,
                     fecha_viaje.strftime("%Y-%m-%d")),
                )
                execute(
                    "INSERT INTO seguimiento (viaje_id, evento, detalle, timestamp) VALUES (?,?,?,?)",
                    (viaje_id, "Viaje registrado", f"Flete {codigo} programado para {cliente_sel}",
                     datetime.now().strftime("%Y-%m-%d %H:%M")),
                )
                st.success(f"✅ Viaje **{codigo}** registrado. Ingreso estimado: S/ {ingreso:,.2f}")
                st.balloons()


# ============================================================
# MÓDULO 5: CONTROL DE UNIDADES / VEHÍCULOS
# ============================================================

def modulo_vehiculos():
    st.markdown("<h3 class='section-title'>5. Control de Unidades / Vehículos</h3>", unsafe_allow_html=True)

    vehiculos = df_query("SELECT * FROM vehiculos")
    c1, c2, c3 = st.columns(3)
    c1.metric("Unidades registradas", len(vehiculos))
    c2.metric("Operativas", len(vehiculos[vehiculos['estado'] == 'Operativo']))
    c3.metric("En mantenimiento / inactivas", len(vehiculos[vehiculos['estado'] != 'Operativo']))

    for _, r in vehiculos.iterrows():
        with st.container(border=True):
            cc1, cc2, cc3, cc4 = st.columns([1.2, 1, 1, 1])
            cc1.markdown(f"**🚛 Placa: {r['placa']}**")
            cc2.markdown(f"Capacidad: **{r['capacidad_cajas']} cajas**")
            cc3.markdown(f"Chofer asignado: **{r['chofer_asignado']}**")
            kind = "ok" if r['estado'] == "Operativo" else ("warn" if r['estado'] == "Mantenimiento" else "bad")
            cc4.markdown(badge(r['estado'], kind), unsafe_allow_html=True)
            st.caption(f"Km recorridos: {r['km_recorridos']:,.0f} km · "
                       f"Último mantenimiento: {r['ultimo_mantenimiento']} · "
                       f"Próximo mantenimiento: {r['proximo_mantenimiento']}")

    st.markdown("##### Actualizar unidad / registrar mantenimiento")
    if len(vehiculos):
        sel = st.selectbox("Vehículo", vehiculos['placa'])
        row = vehiculos[vehiculos['placa'] == sel].iloc[0]
        c1, c2 = st.columns(2)
        with c1:
            nuevo_estado = st.selectbox("Nuevo estado", ["Operativo", "Mantenimiento", "Inactivo"])
            chofer_asig = st.text_input("Chofer asignado", value=row['chofer_asignado'])
        with c2:
            fecha_mant = st.date_input("Fecha de mantenimiento", value=date.today())
            prox_mant = st.date_input("Próximo mantenimiento programado",
                                       value=date.today() + timedelta(days=120))
        if st.button("Guardar actualización de unidad", type="primary"):
            vid = int(row['id'])
            execute(
                "UPDATE vehiculos SET estado=?, chofer_asignado=?, ultimo_mantenimiento=?, proximo_mantenimiento=? "
                "WHERE id=?",
                (nuevo_estado, chofer_asig, fecha_mant.strftime("%Y-%m-%d"), prox_mant.strftime("%Y-%m-%d"), vid),
            )
            st.success(f"Vehículo {sel} actualizado correctamente.")
            st.rerun()

    with st.expander("➕ Registrar nueva unidad vehicular"):
        with st.form("nuevo_vehiculo_form"):
            placa = st.text_input("Placa")
            capacidad = st.number_input("Capacidad (cajas)", min_value=50, value=300, step=10)
            chofer = st.text_input("Chofer asignado")
            ok = st.form_submit_button("Registrar unidad")
            if ok and placa:
                execute(
                    "INSERT INTO vehiculos (placa, capacidad_cajas, chofer_asignado, estado, "
                    "ultimo_mantenimiento, proximo_mantenimiento) VALUES (?,?,?,?,?,?)",
                    (placa, capacidad, chofer or "Por asignar", "Operativo",
                     date.today().strftime("%Y-%m-%d"), (date.today() + timedelta(days=120)).strftime("%Y-%m-%d")),
                )
                st.success(f"Unidad {placa} registrada correctamente.")
                st.rerun()

    st.markdown("---")
    st.info("""
    Conforme al diseño del proyecto, ante una falla del vehículo principal o mantenimiento programado,
    se activa el **camión de respaldo** para no interrumpir el servicio (Costos Indirectos de
    Fabricación: alquiler de camión en caso fortuito / mantenimiento).
    """)


# ============================================================
# MÓDULO 6: COSTOS E INGRESOS
# ============================================================

def modulo_costos_ingresos():
    st.markdown("<h3 class='section-title'>6. Costos e Ingresos</h3>", unsafe_allow_html=True)

    ci = df_query("""
        SELECT ci.*, v.codigo, v.cantidad_cajas
        FROM costos_ingresos ci LEFT JOIN viajes v ON ci.viaje_id = v.id
    """)
    if not len(ci):
        st.info("No hay registros de costos e ingresos todavía.")
        return

    ci['utilidad_viaje'] = (ci['ingreso_viaje'] - ci['combustible'] - ci['peajes']
                            - ci['pago_chofer'] - ci['mantenimiento'] - ci['otros'])

    total_combustible = ci['combustible'].sum()
    total_peajes = ci['peajes'].sum()
    total_pago_chofer = ci['pago_chofer'].sum()
    total_mantenimiento = ci['mantenimiento'].sum()
    total_ingresos = ci['ingreso_viaje'].sum()
    total_utilidad = ci['utilidad_viaje'].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Combustible", f"S/ {total_combustible:,.2f}")
    c2.metric("Peajes", f"S/ {total_peajes:,.2f}")
    c3.metric("Pago a choferes", f"S/ {total_pago_chofer:,.2f}")
    c4.metric("Mantenimiento", f"S/ {total_mantenimiento:,.2f}")

    c5, c6 = st.columns(2)
    c5.metric("Ingreso total por viajes", f"S/ {total_ingresos:,.2f}")
    c6.metric("Utilidad total estimada", f"S/ {total_utilidad:,.2f}",
              delta=f"{(total_utilidad/total_ingresos*100 if total_ingresos else 0):.1f}% margen")

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📊 Distribución de costos", "📋 Utilidad por viaje", "➕ Registrar costos"])

    with tab1:
        dist = pd.DataFrame({
            "Categoría": ["Combustible", "Peajes", "Pago al chofer", "Mantenimiento", "Otros"],
            "Monto": [total_combustible, total_peajes, total_pago_chofer, total_mantenimiento, ci['otros'].sum()],
        })
        cc1, cc2 = st.columns([1, 1.3])
        with cc1:
            fig = px.pie(dist, names='Categoría', values='Monto', hole=0.4)
            fig.update_layout(height=320)
            st.plotly_chart(fig, use_container_width=True)
        with cc2:
            st.dataframe(dist.rename(columns={'Monto': 'Monto (S/.)'}), use_container_width=True, height=320)

    with tab2:
        tabla = ci[['codigo', 'cantidad_cajas', 'ingreso_viaje', 'combustible', 'peajes',
                    'pago_chofer', 'mantenimiento', 'utilidad_viaje']].rename(columns={
            'codigo': 'Viaje', 'cantidad_cajas': 'Cajas', 'ingreso_viaje': 'Ingreso (S/.)',
            'combustible': 'Combustible (S/.)', 'peajes': 'Peajes (S/.)',
            'pago_chofer': 'Pago chofer (S/.)', 'mantenimiento': 'Mantenimiento (S/.)',
            'utilidad_viaje': 'Utilidad (S/.)'
        })
        st.dataframe(tabla, use_container_width=True, height=380)
        fig2 = px.bar(tabla.tail(15), x='Viaje', y='Utilidad (S/.)', color_discrete_sequence=[SECONDARY])
        fig2.update_layout(height=300, xaxis_title="")
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        viajes_lista = df_query("SELECT id, codigo FROM viajes ORDER BY fecha DESC")
        with st.form("nuevo_costo_form"):
            viaje_sel = st.selectbox("Viaje asociado", viajes_lista['codigo'])
            c1, c2, c3 = st.columns(3)
            with c1:
                combustible = st.number_input("Combustible (S/.)", min_value=0.0, step=10.0)
                peajes = st.number_input("Peajes (S/.)", min_value=0.0, step=5.0)
            with c2:
                pago_chofer = st.number_input("Pago al chofer (S/.)", min_value=0.0, step=10.0)
                mantenimiento = st.number_input("Mantenimiento (S/.)", min_value=0.0, step=10.0)
            with c3:
                otros = st.number_input("Otros costos (S/.)", min_value=0.0, step=5.0)
                ingreso = st.number_input("Ingreso del viaje (S/.)", min_value=0.0, step=10.0)
            ok = st.form_submit_button("Registrar movimiento", type="primary")
            if ok:
                vid = int(viajes_lista[viajes_lista['codigo'] == viaje_sel]['id'].iloc[0])
                existe = df_query("SELECT id FROM costos_ingresos WHERE viaje_id=?", (vid,))
                if len(existe):
                    execute(
                        "UPDATE costos_ingresos SET combustible=?, peajes=?, pago_chofer=?, mantenimiento=?, "
                        "otros=?, ingreso_viaje=?, fecha=? WHERE viaje_id=?",
                        (combustible, peajes, pago_chofer, mantenimiento, otros, ingreso,
                         date.today().strftime("%Y-%m-%d"), vid),
                    )
                else:
                    execute(
                        "INSERT INTO costos_ingresos (viaje_id, combustible, peajes, pago_chofer, mantenimiento, "
                        "otros, ingreso_viaje, fecha) VALUES (?,?,?,?,?,?,?,?)",
                        (vid, combustible, peajes, pago_chofer, mantenimiento, otros, ingreso,
                         date.today().strftime("%Y-%m-%d")),
                    )
                st.success(f"Movimiento de costos/ingresos del viaje {viaje_sel} registrado.")
                st.rerun()


# ============================================================
# MÓDULO 7: REPORTES
# ============================================================

def modulo_reportes():
    st.markdown("<h3 class='section-title'>7. Reportes</h3>", unsafe_allow_html=True)

    viajes = df_query("SELECT * FROM viajes")
    clientes = df_query("SELECT * FROM clientes")
    ci = df_query("SELECT * FROM costos_ingresos")

    if not len(viajes):
        st.info("No hay datos suficientes para generar reportes.")
        return

    rango = st.date_input(
        "Rango de fechas para el reporte",
        value=(pd.to_datetime(viajes['fecha']).min().date(), pd.to_datetime(viajes['fecha']).max().date())
    )
    viajes['f'] = pd.to_datetime(viajes['fecha']).dt.date
    vf = viajes[(viajes['f'] >= rango[0]) & (viajes['f'] <= rango[1])] if isinstance(rango, tuple) and len(rango) == 2 else viajes

    ids = vf['id'].tolist()
    cif = ci[ci['viaje_id'].isin(ids)]

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["🚚 Viajes realizados", "💰 Ingresos mensuales", "📉 Costos mensuales",
         "⭐ Clientes frecuentes", "🛣️ Rutas más usadas"]
    )

    with tab1:
        st.metric("Viajes en el periodo", len(vf))
        conteo = vf['estado'].value_counts().reset_index()
        conteo.columns = ['Estado', 'Cantidad']
        fig = px.bar(conteo, x='Estado', y='Cantidad', color='Estado', text='Cantidad')
        fig.update_layout(height=320, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(
            vf[['codigo', 'fecha', 'cantidad_cajas', 'estado', 'chofer']].rename(columns={
                'codigo': 'Código', 'fecha': 'Fecha', 'cantidad_cajas': 'Cajas',
                'estado': 'Estado', 'chofer': 'Chofer'
            }).sort_values('Fecha', ascending=False),
            use_container_width=True, height=300
        )

    with tab2:
        vf2 = vf.merge(cif[['viaje_id', 'ingreso_viaje']], left_on='id', right_on='viaje_id', how='left')
        vf2['mes'] = pd.to_datetime(vf2['fecha']).dt.to_period('M').astype(str)
        ing_mes = vf2.groupby('mes')['ingreso_viaje'].sum().reset_index()
        st.metric("Ingreso total del periodo", f"S/ {ing_mes['ingreso_viaje'].sum():,.2f}")
        fig2 = px.bar(ing_mes, x='mes', y='ingreso_viaje', color_discrete_sequence=[SECONDARY], text_auto='.2s')
        fig2.update_layout(height=320, xaxis_title="Mes", yaxis_title="Ingreso (S/.)")
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        cif2 = cif.merge(vf[['id', 'fecha']], left_on='viaje_id', right_on='id', how='left')
        cif2['mes'] = pd.to_datetime(cif2['fecha']).dt.to_period('M').astype(str)
        cif2['costo_total'] = cif2['combustible'] + cif2['peajes'] + cif2['pago_chofer'] + cif2['mantenimiento'] + cif2['otros']
        costo_mes = cif2.groupby('mes')['costo_total'].sum().reset_index()
        st.metric("Costo total del periodo", f"S/ {costo_mes['costo_total'].sum():,.2f}")
        fig3 = px.bar(costo_mes, x='mes', y='costo_total', color_discrete_sequence=[DANGER], text_auto='.2s')
        fig3.update_layout(height=320, xaxis_title="Mes", yaxis_title="Costo (S/.)")
        st.plotly_chart(fig3, use_container_width=True)

    with tab4:
        merge = vf.merge(clientes, left_on='cliente_id', right_on='id', suffixes=('', '_cli'))
        frec = merge.groupby('nombre').agg(viajes=('nombre', 'count'), cajas=('cantidad_cajas', 'sum')).reset_index()
        frec = frec.sort_values('viajes', ascending=False)
        fig4 = px.bar(frec.head(8), x='nombre', y='viajes', text='cajas', color_discrete_sequence=[ACCENT])
        fig4.update_layout(height=320, xaxis_title="")
        st.plotly_chart(fig4, use_container_width=True)
        st.dataframe(frec.rename(columns={'nombre': 'Cliente', 'viajes': 'N° viajes', 'cajas': 'Cajas totales'}),
                     use_container_width=True, height=260)

    with tab5:
        rutas = vf.groupby(['origen', 'destino']).size().reset_index(name='viajes')
        rutas['ruta'] = rutas['origen'] + " → " + rutas['destino']
        fig5 = px.bar(rutas.sort_values('viajes', ascending=False), x='ruta', y='viajes',
                      color_discrete_sequence=[INFO])
        fig5.update_layout(height=320, xaxis_title="")
        st.plotly_chart(fig5, use_container_width=True)
        st.dataframe(rutas[['ruta', 'viajes']].rename(columns={'ruta': 'Ruta', 'viajes': 'N° viajes'}),
                     use_container_width=True, height=200)

    st.markdown("---")
    st.markdown("##### Exportar reporte general")
    export = vf.merge(clientes, left_on='cliente_id', right_on='id', suffixes=('', '_cli'))
    export = export.merge(cif[['viaje_id', 'ingreso_viaje']], left_on='id', right_on='viaje_id', how='left')
    export_cols = export[['codigo', 'nombre', 'origen', 'destino', 'fecha', 'cantidad_cajas',
                           'costo_viaje', 'ingreso_viaje', 'estado']].rename(columns={
        'codigo': 'Código', 'nombre': 'Cliente', 'origen': 'Origen', 'destino': 'Destino',
        'fecha': 'Fecha', 'cantidad_cajas': 'Cajas', 'costo_viaje': 'Costo Viaje (S/.)',
        'ingreso_viaje': 'Ingreso (S/.)', 'estado': 'Estado'
    })
    csv = export_cols.to_csv(index=False).encode('utf-8-sig')
    st.download_button("⬇️ Descargar reporte en CSV", csv, file_name="reporte_chaski_track.csv", mime="text/csv")
    st.dataframe(export_cols, use_container_width=True, height=300)


# ============================================================
# MÓDULO 8: PANEL DE SEGUIMIENTO
# ============================================================

def modulo_seguimiento():
    st.markdown("<h3 class='section-title'>8. Panel de Seguimiento</h3>", unsafe_allow_html=True)
    st.caption("Estados de viaje: Pendiente · En ruta · Entregado")

    viajes = df_query("""
        SELECT v.id, v.codigo, c.nombre AS cliente, v.chofer, ve.placa AS vehiculo,
               v.estado, v.avance_pct, v.fecha, v.fecha_entrega_estimada,
               v.cantidad_cajas, v.incidencia
        FROM viajes v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        LEFT JOIN vehiculos ve ON v.vehiculo_id = ve.id
        ORDER BY v.fecha DESC
    """)

    c1, c2, c3 = st.columns(3)
    c1.metric("🕓 Pendientes", len(viajes[viajes['estado'] == 'Pendiente']))
    c2.metric("🚚 En ruta", len(viajes[viajes['estado'] == 'En ruta']))
    c3.metric("✅ Entregados", len(viajes[viajes['estado'] == 'Entregado']))

    tab1, tab2, tab3 = st.tabs(["🕓 Pendiente", "🚚 En ruta", "✅ Entregado"])
    mapping = {"🕓 Pendiente": "Pendiente", "🚚 En ruta": "En ruta", "✅ Entregado": "Entregado"}

    for tab, label in zip([tab1, tab2, tab3], mapping.keys()):
        with tab:
            estado_f = mapping[label]
            subset = viajes[viajes['estado'] == estado_f]
            if not len(subset):
                st.info(f"No hay viajes en estado '{estado_f}' en este momento.")
            for _, r in subset.iterrows():
                with st.container(border=True):
                    col1, col2, col3 = st.columns([1.4, 1, 1])
                    with col1:
                        st.markdown(f"### {r['codigo']}")
                        st.markdown(f"**Cliente:** {r['cliente']}")
                        st.markdown(f"**Chofer:** {r['chofer']} · **Vehículo:** {r['vehiculo']}")
                    with col2:
                        st.markdown(f"**Fecha:** {r['fecha']}")
                        st.markdown(f"**Entrega estimada:** {r['fecha_entrega_estimada']}")
                        st.markdown(f"**Carga:** {r['cantidad_cajas']} cajas")
                    with col3:
                        kind = estado_kind(r['estado'])
                        st.markdown(badge(r['estado'], kind), unsafe_allow_html=True)
                        if r['incidencia']:
                            st.warning(f"⚠️ {r['incidencia']}")
                    st.progress(int(r['avance_pct']) / 100, text=f"Avance: {r['avance_pct']}%")

                    hist = df_query(
                        "SELECT evento, detalle, timestamp FROM seguimiento WHERE viaje_id=? ORDER BY timestamp",
                        (int(r['id']),)
                    )
                    with st.expander("📜 Historial de eventos"):
                        for _, h in hist.iterrows():
                            st.markdown(f"- **{h['timestamp']}** — *{h['evento']}*: {h['detalle']}")

    st.markdown("---")
    st.markdown("##### Buscar un viaje por código")
    codigo_busqueda = st.text_input("Ingresa el código de viaje (ej. ACHS-0005)")
    if codigo_busqueda:
        res = viajes[viajes['codigo'].str.contains(codigo_busqueda, case=False, na=False)]
        if len(res):
            r = res.iloc[0]
            st.success(f"Viaje {r['codigo']} — Estado: {r['estado']} — Avance: {r['avance_pct']}%")
        else:
            st.error("No se encontró ningún viaje con ese código.")


# ============================================================
# RUTEO DE SECCIONES
# ============================================================

SECCION_FN = {
    "1. Inicio / Dashboard": modulo_dashboard,
    "2. Usuarios del sistema": modulo_usuarios,
    "3. Registro de clientes": modulo_clientes,
    "4. Registro de viajes o fletes": modulo_viajes,
    "5. Control de unidades / vehículos": modulo_vehiculos,
    "6. Costos e ingresos": modulo_costos_ingresos,
    "7. Reportes": modulo_reportes,
    "8. Panel de seguimiento": modulo_seguimiento,
}

SECCION_FN.get(seccion, modulo_dashboard)()

st.markdown("---")
st.caption(
    "Chaski Track © 2026 · Plataforma de gestión del proyecto de transporte de tunas, desarrollada "
    "para el curso Evaluación Financiera de Proyectos (GI4101) - UTEC. Los datos mostrados son de "
    "demostración y se basan en los supuestos definidos en el informe del proyecto."
)
