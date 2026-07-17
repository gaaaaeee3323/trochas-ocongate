"""
app.py — AgroLink AI (prototipo funcional)
Plataforma de coordinacion inteligente para la exportacion de cafe peruano.

Como correrlo:
    pip install -r requirements.txt
    streamlit run app.py

Este prototipo usa datos simulados (ver data.py) para representar
compradores, transportistas, certificadoras y riesgo portuario. La
logica de "IA" (engine.py) es un sistema de scoring por reglas
ponderadas, pensado para la fase de MVP -- tal como se describe en
el informe de propuesta AgroLink AI para Disruptón 2026.
"""

import re
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from data import (
    COMPRADORES, TRANSPORTISTAS, CERTIFICADORAS, FINANCIAMIENTO, PUERTOS,
    obtener_riesgo_puerto, documentos_requeridos,
)
from engine import (
    buscar_compradores, recomendar_transporte, estimar_financiamiento,
    checklist_documental, generar_plan_exportacion,
)

# ---------------------------------------------------------------------
# Configuracion general y estilos
# ---------------------------------------------------------------------
st.set_page_config(page_title="AgroLink AI", page_icon="☕", layout="wide")

CUSTOM_CSS = """
<style>
:root {
    --brown-dark: #3C2415;
    --brown: #5A3825;
    --gold: #C8A45E;
}
h1, h2, h3 { color: var(--brown-dark) !important; }
.stButton>button {
    background-color: var(--brown-dark);
    color: white;
    border-radius: 6px;
    border: none;
}
.stButton>button:hover { background-color: var(--brown); color: white; }
.metric-card {
    background: #FAF6EE;
    border: 1px solid #E6DCC8;
    border-left: 4px solid var(--gold);
    border-radius: 6px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.alert-high { background:#FBEEEE; border-left:5px solid #A33636; padding:10px 14px; border-radius:5px; margin-bottom:8px;}
.alert-med { background:#FDF3E7; border-left:5px solid #C8A45E; padding:10px 14px; border-radius:5px; margin-bottom:8px;}
.alert-low { background:#EFF6F1; border-left:5px solid #2E6B4F; padding:10px 14px; border-radius:5px; margin-bottom:8px;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Estado de sesion: el "lote" de cafe activo del productor
# ---------------------------------------------------------------------
if "lote" not in st.session_state:
    st.session_state.lote = {
        "tipo_cafe": "Especial",
        "cantidad_kg": 2000,
        "region": "Cajamarca",
        "pais_destino": "Alemania",
        "puerto": "Callao",
        "fecha_embarque": date.today() + timedelta(days=12),
        "docs_marcados": {"Factura comercial", "Packing list"},
    }
if "calificaciones" not in st.session_state:
    st.session_state.calificaciones = []

PAISES_DISPONIBLES = sorted({c["pais"] for c in COMPRADORES})

# ---------------------------------------------------------------------
# Sidebar / navegacion
# ---------------------------------------------------------------------
st.sidebar.markdown("## ☕ AgroLink AI")
st.sidebar.caption("Copiloto inteligente de exportación de café")
pagina = st.sidebar.radio(
    "Módulo",
    [
        "Dashboard",
        "Publicar café",
        "Matching inteligente",
        "Logística",
        "Documentación",
        "Gestión de riesgos",
        "Financiamiento",
        "Seguimiento",
        "Calificaciones",
        "🤖 Agente IA de Exportación",
    ],
)
st.sidebar.markdown("---")
st.sidebar.caption("Prototipo de demo · Disruptón 2026 · Datos simulados")

lote = st.session_state.lote

# ---------------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------------
if pagina == "Dashboard":
    st.title("Dashboard del productor")
    st.caption("Vista general de tu operación de exportación activa")

    col1, col2, col3, col4 = st.columns(4)
    riesgo_actual = obtener_riesgo_puerto(lote["puerto"], lote["fecha_embarque"])
    checklist = checklist_documental(lote["pais_destino"], lote["docs_marcados"])
    faltantes = [c for c in checklist if not c["listo"]]

    with col1:
        st.markdown(f"""<div class="metric-card"><b>Lote activo</b><br>
        {lote['cantidad_kg']:,.0f} kg · {lote['tipo_cafe']}<br>
        <small>{lote['region']}</small></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card"><b>Destino</b><br>
        {lote['pais_destino']}<br><small>Puerto: {lote['puerto']}</small></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card"><b>Riesgo logístico</b><br>
        <span style="color:{riesgo_actual['color']}; font-weight:700">{riesgo_actual['nivel']}</span>
        <br><small>Score: {riesgo_actual['score']}</small></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card"><b>Documentos pendientes</b><br>
        {len(faltantes)} de {len(checklist)}<br>
        <small>{'Todo listo' if not faltantes else 'Revisar módulo de Documentación'}</small></div>""", unsafe_allow_html=True)

    st.markdown("### Línea de tiempo de la operación")
    etapas = ["Producción", "Certificación", "Recojo", "Almacén", "Puerto", "Embarque"]
    estado_etapas = [1, 1, 1, 0.5, 0, 0]  # 1 = completo, 0.5 = en proceso, 0 = pendiente
    cols = st.columns(len(etapas))
    for c, etapa, est in zip(cols, etapas, estado_etapas):
        icono = "✅" if est == 1 else ("🟡" if est == 0.5 else "⚪")
        c.markdown(f"<div style='text-align:center'>{icono}<br><small>{etapa}</small></div>", unsafe_allow_html=True)

    st.markdown("### Alertas activas")
    if riesgo_actual["nivel"] == "Alto":
        st.markdown(f"<div class='alert-high'>⚠️ <b>Riesgo alto en {lote['puerto']}:</b> {riesgo_actual['recomendacion']}</div>", unsafe_allow_html=True)
    elif riesgo_actual["nivel"] == "Medio":
        st.markdown(f"<div class='alert-med'>🟡 <b>Riesgo medio en {lote['puerto']}:</b> {riesgo_actual['recomendacion']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='alert-low'>✅ Condiciones normales en {lote['puerto']}.</div>", unsafe_allow_html=True)
    if faltantes:
        st.markdown(f"<div class='alert-med'>📄 Faltan {len(faltantes)} documento(s): {', '.join(d['documento'] for d in faltantes)}.</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# PUBLICAR CAFE
# ---------------------------------------------------------------------
elif pagina == "Publicar café":
    st.title("Publicar café")
    st.caption("Registra tu lote para que la IA comience a buscar coincidencias")

    with st.form("form_publicar"):
        c1, c2 = st.columns(2)
        with c1:
            tipo_cafe = st.selectbox("Tipo de café", ["Especial", "Organico", "Convencional"],
                                      index=["Especial", "Organico", "Convencional"].index(lote["tipo_cafe"]))
            cantidad_kg = st.number_input("Cantidad (kg)", min_value=100, max_value=100000,
                                           value=int(lote["cantidad_kg"]), step=100)
            region = st.text_input("Región / ubicación", value=lote["region"])
        with c2:
            pais_destino = st.selectbox("País destino deseado", PAISES_DISPONIBLES,
                                         index=PAISES_DISPONIBLES.index(lote["pais_destino"]) if lote["pais_destino"] in PAISES_DISPONIBLES else 0)
            puerto = st.selectbox("Puerto de salida", list(PUERTOS.keys()),
                                   index=list(PUERTOS.keys()).index(lote["puerto"]))
            fecha_embarque = st.date_input("Fecha disponible / embarque estimado", value=lote["fecha_embarque"])

        enviado = st.form_submit_button("Publicar y analizar con IA")

    if enviado:
        st.session_state.lote.update({
            "tipo_cafe": tipo_cafe, "cantidad_kg": cantidad_kg, "region": region,
            "pais_destino": pais_destino, "puerto": puerto, "fecha_embarque": fecha_embarque,
        })
        st.success("Lote publicado. La IA ya analizó tu operación — revisa Matching Inteligente y Gestión de Riesgos.")
        st.rerun()

    st.info(f"Lote actual: **{lote['cantidad_kg']:,.0f} kg** de café **{lote['tipo_cafe']}**, desde **{lote['region']}**, "
            f"con destino **{lote['pais_destino']}** vía puerto **{lote['puerto']}**, embarque estimado **{lote['fecha_embarque']}**.")

# ---------------------------------------------------------------------
# MATCHING INTELIGENTE
# ---------------------------------------------------------------------
elif pagina == "Matching inteligente":
    st.title("Matching inteligente de compradores")
    st.caption("La IA cruza tu lote con la base de compradores según tipo, volumen, precio, reputación y cercanía")

    resultados = buscar_compradores(lote["tipo_cafe"], lote["cantidad_kg"], top_n=5)

    if not resultados:
        st.warning("No se encontraron compradores compatibles con el tipo y volumen actuales. Ajusta el lote en 'Publicar café'.")
    else:
        for r in resultados:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                with c1:
                    st.markdown(f"**{r['nombre']}** · {r['pais']}")
                    st.caption(f"Acepta: {', '.join(r['tipo_cafe'])} · Rango: {r['volumen_min_kg']:,}–{r['volumen_max_kg']:,} kg")
                with c2:
                    st.markdown(f"Precio ofrecido: **US$ {r['precio_usd_kg']}/kg**")
                    st.caption(f"Reputación: {'⭐' * round(r['reputacion'])} ({r['reputacion']}) · Pago a {r['pago_dias']} días")
                with c3:
                    st.metric("Compatibilidad", f"{r['compatibilidad_pct']}%")

# ---------------------------------------------------------------------
# LOGISTICA
# ---------------------------------------------------------------------
elif pagina == "Logística":
    st.title("Logística inteligente")
    st.caption("Cotización de transporte — recomendamos la opción más conveniente, no la más barata")

    dias_disponibles = max(1, (lote["fecha_embarque"] - date.today()).days)
    st.write(f"Días disponibles hasta el embarque estimado: **{dias_disponibles}**")

    transportes = recomendar_transporte(dias_disponibles)
    df = pd.DataFrame(transportes)
    df_display = df[["nombre", "costo_usd", "dias_entrega", "retrasos_historicos_pct", "reputacion", "conveniencia_pct"]]
    df_display.columns = ["Transportista", "Costo (US$)", "Días de entrega", "Retrasos históricos (%)", "Reputación", "Conveniencia (%)"]
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    mejor = transportes[0]
    st.success(f"**Recomendación de la IA:** {mejor['nombre']} — no es el más barato, pero combina "
               f"{mejor['retrasos_historicos_pct']}% de retrasos históricos con {mejor['dias_entrega']} días de entrega "
               f"y reputación de {mejor['reputacion']}/5.")

# ---------------------------------------------------------------------
# DOCUMENTACION
# ---------------------------------------------------------------------
elif pagina == "Documentación":
    st.title("Gestión documental")
    st.caption(f"Documentos requeridos para exportar a {lote['pais_destino']}")

    requeridos = documentos_requeridos(lote["pais_destino"])
    nuevos_marcados = set()
    for doc in requeridos:
        marcado = st.checkbox(doc, value=doc in lote["docs_marcados"], key=f"doc_{doc}")
        if marcado:
            nuevos_marcados.add(doc)
    st.session_state.lote["docs_marcados"] = nuevos_marcados

    faltantes = [d for d in requeridos if d not in nuevos_marcados]
    if faltantes:
        st.markdown(f"<div class='alert-med'>📄 <b>Documentos pendientes:</b> {', '.join(faltantes)}</div>", unsafe_allow_html=True)
        st.markdown("#### ¿Quién puede emitir los documentos faltantes?")
        for c in CERTIFICADORAS:
            emitibles = [d for d in faltantes if d in c["certificados"] or any(d.startswith(cert) for cert in c["certificados"])]
            if emitibles:
                st.write(f"- **{c['nombre']}** puede emitir: {', '.join(c['certificados'])} (≈{c['dias_emision']} días)")
    else:
        st.success("✅ Todos los documentos requeridos están listos.")

    if lote["pais_destino"] in {"Alemania", "Suecia", "Belgica"}:
        st.info("Este destino está en la Unión Europea: recuerda que el Reglamento EUDR exige trazabilidad "
                "geográfica y una declaración de diligencia debida para café, con aplicación plena desde el "
                "30 de diciembre de 2026 (con margen adicional para microempresas).")

# ---------------------------------------------------------------------
# GESTION DE RIESGOS
# ---------------------------------------------------------------------
elif pagina == "Gestión de riesgos":
    st.title("Gestión de riesgos logísticos")
    st.caption("Análisis de congestión portuaria y recomendación de acción — gestión predictiva, no reactiva")

    col1, col2 = st.columns(2)
    for col, puerto in zip([col1, col2], PUERTOS.keys()):
        riesgo = obtener_riesgo_puerto(puerto, lote["fecha_embarque"])
        with col:
            st.markdown(f"#### Puerto: {puerto}")
            st.markdown(f"<span style='color:{riesgo['color']}; font-size:22px; font-weight:700'>{riesgo['nivel']}</span> "
                        f"(score {riesgo['score']})", unsafe_allow_html=True)
            st.caption(f"Tráfico naviero: {riesgo['trafico_naviero']}")
            st.write(riesgo["recomendacion"])

    st.markdown("---")
    st.markdown("#### Simular otra fecha de embarque")
    nueva_fecha = st.date_input("Fecha a evaluar", value=lote["fecha_embarque"], key="fecha_riesgo")
    puerto_sel = st.selectbox("Puerto", list(PUERTOS.keys()), key="puerto_riesgo")
    if st.button("Analizar riesgo para esta fecha"):
        r = obtener_riesgo_puerto(puerto_sel, nueva_fecha)
        st.markdown(f"Riesgo estimado: <span style='color:{r['color']}; font-weight:700'>{r['nivel']}</span> — {r['recomendacion']}",
                    unsafe_allow_html=True)

# ---------------------------------------------------------------------
# FINANCIAMIENTO
# ---------------------------------------------------------------------
elif pagina == "Financiamiento":
    st.title("Financiamiento de la operación")

    compradores = buscar_compradores(lote["tipo_cafe"], lote["cantidad_kg"], top_n=1)
    precio_ref = compradores[0]["precio_usd_kg"] if compradores else 7.0
    fin = estimar_financiamiento(lote["cantidad_kg"], precio_ref)

    c1, c2 = st.columns(2)
    c1.metric("Valor estimado de la operación", f"US$ {fin['valor_operacion_usd']:,.0f}")
    c2.metric("Capital de trabajo estimado (35%)", f"US$ {fin['capital_estimado_usd']:,.0f}")

    st.markdown("#### Opciones de financiamiento disponibles")
    df_fin = pd.DataFrame(fin["opciones"])
    df_fin.columns = ["Entidad", "Tasa anual (%)", "Plazo máximo (días)"]
    st.dataframe(df_fin, use_container_width=True, hide_index=True)
    st.caption("Estimación basada en un supuesto de 35% de capital de trabajo sobre el valor de la operación; "
               "ajustar con datos reales de costos fijos del productor en una fase posterior.")

# ---------------------------------------------------------------------
# SEGUIMIENTO
# ---------------------------------------------------------------------
elif pagina == "Seguimiento":
    st.title("Seguimiento de la exportación")
    etapas = [
        ("Producción", "Completado", "✅"),
        ("Certificación", "Completado", "✅"),
        ("Recojo", "Completado", "✅"),
        ("Almacén", "En proceso", "🟡"),
        ("Puerto", "Pendiente", "⚪"),
        ("Embarque", "Pendiente", "⚪"),
    ]
    for etapa, estado, icono in etapas:
        st.write(f"{icono} **{etapa}** — {estado}")
    st.progress(0.55, text="55% del proceso completado (estimado)")

# ---------------------------------------------------------------------
# CALIFICACIONES
# ---------------------------------------------------------------------
elif pagina == "Calificaciones":
    st.title("Calificaciones")
    st.caption("Al cerrar una operación, cada actor califica a los demás — esto alimenta al motor de matching")

    with st.form("form_calificacion"):
        actor = st.selectbox("Actor a calificar", ["Transportista", "Comprador", "Certificadora", "Agente de aduanas"])
        nombre = st.text_input("Nombre de la empresa")
        estrellas = st.slider("Calificación", 1, 5, 5)
        comentario = st.text_area("Comentario (opcional)")
        enviar = st.form_submit_button("Guardar calificación")
    if enviar and nombre:
        st.session_state.calificaciones.append({"actor": actor, "nombre": nombre, "estrellas": estrellas, "comentario": comentario})
        st.success("Calificación registrada.")

    if st.session_state.calificaciones:
        st.markdown("#### Historial de calificaciones de esta sesión")
        df_cal = pd.DataFrame(st.session_state.calificaciones)
        st.dataframe(df_cal, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------
# AGENTE IA DE EXPORTACION
# ---------------------------------------------------------------------
elif pagina == "🤖 Agente IA de Exportación":
    st.title("🤖 Agente IA de Exportación")
    st.caption('Escribe tu situación en una frase, como: "Tengo 3 toneladas de café especial listas para exportar a Alemania"')

    ejemplo = "Tengo 3 toneladas de café especial listas para exportar a Alemania"
    instruccion = st.text_input("Tu instrucción", value=ejemplo)

    def parsear_instruccion(texto: str) -> dict:
        texto_low = texto.lower()
        cantidad_kg = lote["cantidad_kg"]
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*(tonelada|ton|kg|kilo)", texto_low)
        if m:
            valor = float(m.group(1).replace(",", "."))
            unidad = m.group(2)
            cantidad_kg = valor * 1000 if unidad.startswith(("ton", "tone")) else valor

        tipo_cafe = lote["tipo_cafe"]
        for t in ["especial", "organico", "orgánico", "convencional"]:
            if t in texto_low:
                tipo_cafe = "Organico" if "organ" in t else t.capitalize()
                break

        pais_destino = lote["pais_destino"]
        for pais in PAISES_DISPONIBLES:
            if pais.lower() in texto_low:
                pais_destino = pais
                break

        return {"cantidad_kg": cantidad_kg, "tipo_cafe": tipo_cafe, "pais_destino": pais_destino}

    if st.button("Generar plan de exportación"):
        datos = parsear_instruccion(instruccion)
        st.session_state.lote.update(datos)
        lote = st.session_state.lote

        with st.spinner("Analizando compradores, transporte, riesgos y documentos..."):
            plan = generar_plan_exportacion(
                cantidad_kg=lote["cantidad_kg"],
                tipo_cafe=lote["tipo_cafe"],
                pais_destino=lote["pais_destino"],
                puerto=lote["puerto"],
                fecha_embarque=lote["fecha_embarque"],
                docs_marcados=lote["docs_marcados"],
            )

        st.markdown(f"### Plan de exportación — {lote['cantidad_kg']:,.0f} kg de café {lote['tipo_cafe']} a {lote['pais_destino']}")

        for alerta in plan["alertas"]:
            st.markdown(f"<div class='alert-med'>⚠️ {alerta}</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🎯 Comprador recomendado")
            if plan["mejor_comprador"]:
                mc = plan["mejor_comprador"]
                st.write(f"**{mc['nombre']}** ({mc['pais']}) — US$ {mc['precio_usd_kg']}/kg — "
                         f"{mc['compatibilidad_pct']}% compatibilidad")
            else:
                st.write("Sin coincidencias en la base actual.")

            st.markdown("#### 🚛 Transporte recomendado")
            if plan["mejor_transporte"]:
                mt = plan["mejor_transporte"]
                st.write(f"**{mt['nombre']}** — US$ {mt['costo_usd']} — {mt['dias_entrega']} días — "
                         f"{mt['conveniencia_pct']}% conveniencia")

        with c2:
            st.markdown("#### ⚠️ Riesgo logístico")
            r = plan["riesgo"]
            st.markdown(f"Puerto **{r['puerto']}**: <span style='color:{r['color']}; font-weight:700'>{r['nivel']}</span>",
                        unsafe_allow_html=True)
            st.caption(r["recomendacion"])

            st.markdown("#### 💰 Financiamiento estimado")
            fin = plan["financiamiento"]
            st.write(f"Valor de la operación: US$ {fin['valor_operacion_usd']:,.0f}")
            st.write(f"Capital de trabajo estimado: US$ {fin['capital_estimado_usd']:,.0f}")

        st.markdown("#### 📄 Documentos")
        for c in plan["checklist"]:
            st.write(f"{'✅' if c['listo'] else '❌'} {c['documento']}")
