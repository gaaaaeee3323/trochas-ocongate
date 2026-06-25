# 🛣️ Plataforma de Gestión de Trochas Carrozables — Ocongate

Sistema web de gestión preventiva de mantenimiento vial para trochas carrozables.

---

## 📋 Módulos de la plataforma

### 🏠 Inicio
Presentación del sistema, indicadores rápidos (tramos registrados, km inventariados, estado de la red) y gráficos resumen. Permite filtrar toda la vista por un tramo activo desde el panel lateral.

### 🛣️ Registro de Tramos
Dos pestañas integradas en un mismo flujo:
- **Nuevo tramo:** datos generales, datos técnicos avanzados (altitud, drenaje, señalización, puentes, badenes, accesibilidad, canteras, coordenadas GPS), evidencia fotográfica (4 tipos de foto), archivos PDF adjuntos y observaciones técnicas.
- **Programar mantenimiento del tramo:** motor de planificación inteligente que sugiere automáticamente fechas de inicio/fin según el tipo de mantenimiento, evita la temporada de lluvias (dic-mar) para componentes sensibles, y alerta sobre la criticidad del tramo.

### 📂 Consulta de Tramos
Búsqueda y filtros (código, nombre, comunidad, estado, longitud), edición y eliminación de tramos, visualización de fotografías, y descarga de la ficha técnica individual en **Excel** y **PDF** (con foto incrustada y las fichas 1-B / 1-D completas).

### 📋 Ficha Técnica de Daños
- Registro de daños con **clasificación automática**: tipo de falla, nivel de gravedad, estado resultante, transitabilidad, prioridad, tiempo estimado de reparación, Índice de Condición de Trocha (ICT) y tipo de mantenimiento recomendado (de los 5 definidos).
- Paneles de **datos técnicos** y **recursos y logística** por tramo.
- **Curva de deterioro del IEC** (con/sin mantenimiento) según el Manual de Conservación Vial MCV-2014.
- **Expediente Técnico Resumido**: fichas 1-B (Itinerario) y 1-D (Daños) en formato Provías Descentralizado, evidencia fotográfica y descarga del expediente completo en Excel/PDF.
- Ranking de tramos críticos por ICT.

### 🗓️ Programación de Mantenimiento
Panel de control técnico con:
- Tarjetas KPI por cada uno de los **5 tipos de mantenimiento** (Rutinario, Periódico, Emergencia, Rehabilitación, Reconstrucción).
- **Diagrama de Gantt** consolidado de todas las intervenciones programadas, coloreado por tipo de mantenimiento.
- Cronograma detallado por tipo, resumen por tramo, tabla completa con actualización de estado, y fichas de planificación con evidencia fotográfica.
- Sincronización automática: toda intervención registrada en Registro de Tramos se refleja de inmediato aquí, con redirección automática tras guardar.

### 📊 Reportes
Inventario completo, análisis de daños (por tipo, gravedad, kilómetros afectados), costos e intervenciones, histórico de expedientes ejecutados (2021-2024), y exportación a **Excel** y **PDF**.

---

## ⚙️ Tipos de mantenimiento contemplados

| Tipo | Componentes típicos | Frecuencia recomendada |
|---|---|---|
| Mantenimiento Rutinario | Superficie, Drenaje | 90 días |
| Mantenimiento Periódico | Superficie, Estructura | ~18 meses |
| Mantenimiento de Emergencia | Drenaje, Estructura | Inmediato |
| Rehabilitación | Estructura | ~3 años |
| Reconstrucción | Estructura | ~5 años |

---

## 🧱 Tecnologías

- **Streamlit** — interfaz web e interactividad
- **SQLite** — persistencia local (`trochas_ocongate.db`, se crea automáticamente)
- **Plotly** — gráficos interactivos y diagramas de Gantt
- **Pandas** — manejo y transformación de datos
- **OpenPyXL** — generación de reportes y fichas en Excel (con imágenes incrustadas)
- **FPDF2** — generación de reportes y fichas en PDF (con imágenes incrustadas)
- **Pillow (PIL)** — procesamiento de imágenes para incrustación en PDF

---

## 🚀 Ejecución local

```bash
pip install -r requirements.txt
streamlit run plataforma_trochas.py
```

La base de datos SQLite se crea automáticamente en la primera ejecución, con los 5 tramos reales del proyecto (M1–M5) y una intervención de ejemplo por cada tipo de mantenimiento ya precargados.

## ☁️ Despliegue en Streamlit Community Cloud

1. Sube `plataforma_trochas.py` y `requirements.txt` a este repositorio.
2. En [share.streamlit.io](https://share.streamlit.io), conecta el repo y selecciona `plataforma_trochas.py` como archivo principal.
3. Streamlit Cloud instalará automáticamente las dependencias de `requirements.txt`.

> **Nota:** el almacenamiento en Streamlit Community Cloud es efímero. Si la app se reinicia (inactividad prolongada o redeploy), la base de datos SQLite vuelve a su estado inicial (los 5 tramos + 5 intervenciones de ejemplo). Para persistencia permanente en producción, se recomienda migrar a una base de datos externa (PostgreSQL, Supabase, etc.).

---

## 📚 Referencias técnicas

- Manual de Conservación Vial MCV-2014 (MTC)
- Formatos técnicos de Provías Descentralizado (Fichas 1-B y 1-D)
- PMBOK 8va edición (PMI, 2025)

---

*Plataforma desarrollada como demostración técnica — Proyecto Preprofesional UTEC 2026-I · Frank Puma Mamani (202220055) · Municipalidad Distrital de Ocongate.*
