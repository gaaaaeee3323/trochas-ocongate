# 🛣️ VialNet

**Plataforma inteligente de gestión de mantenimiento vial rural**, desarrollada para el registro, inspección técnica y programación del mantenimiento de trochas carrozables no pavimentadas.

Proyecto piloto implementado sobre la red vial del Distrito de Ocongate (Provincia de Quispicanchi, Región Cusco, Perú), validado sobre 5 tramos reales.

---

## 📋 Descripción

VialNet centraliza en una sola herramienta el ciclo completo de gestión de un tramo vial: inventario, inspección técnica de daños (siguiendo criterios tipo Provías), cálculo automático de índices de estado, programación de intervenciones y generación de reportes ejecutivos exportables. Está pensada para equipos técnicos municipales que necesitan pasar de registros dispersos en papel/Excel a un sistema trazable y auditable.

## ✨ Características principales

- **Inventario de tramos** — registro de tramos viales con evidencia fotográfica y documentos adjuntos.
- **Ficha técnica de daños** — clasificación automática de severidad y cálculo del Índice de Condición del Tramo (ICT).
- **Programación de mantenimiento** — cronograma de intervenciones (rutinario / periódico) con seguimiento por tramo.
- **Reportes y dashboards** — indicadores en tiempo real, gráficos interactivos (Plotly) y ranking de tramos críticos.
- **Exportación** — reportes descargables en Excel (openpyxl) y PDF (fpdf2).
- **Persistencia local** — base de datos SQLite autocontenida, sin dependencias de infraestructura externa.

## 🧱 Tecnologías utilizadas

| Categoría        | Tecnología           |
|-------------------|----------------------|
| Framework web     | [Streamlit](https://streamlit.io/) |
| Procesamiento     | Pandas               |
| Visualización     | Plotly Express / Graph Objects |
| Base de datos     | SQLite3 (estándar de Python) |
| Exportación Excel | OpenPyXL             |
| Exportación PDF   | fpdf2                |
| Manejo de imágenes| Pillow (PIL)         |
| Lenguaje          | Python 3.10+         |

## 📁 Estructura de módulos

```
1. 🏠 Inicio                        — Presentación general, KPIs y gráficos resumen
2. 🛣️ Registro de tramos            — Alta de tramos + evidencia fotográfica + adjuntos
3. 📂 Consulta de tramos            — Buscar / filtrar / editar / eliminar / descargar
4. 📋 Ficha técnica de daños        — Ficha tipo Provías + clasificación automática + ICT
5. 🗓️ Programación de mantenimiento — Cronograma y programación de intervenciones
6. 📊 Reportes                      — Reportes automáticos + gráficos + exportación Excel/PDF
```

## 🚀 Instalación

**Requisitos previos:** Python 3.10 o superior.

```bash
# 1. Clonar el repositorio
git clone https://github.com/<tu-usuario>/vialnet.git
cd vialnet

# 2. Crear y activar un entorno virtual (recomendado)
python -m venv .venv
source .venv/bin/activate      # En Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt
```

## ▶️ Uso

```bash
streamlit run vialnet.py
```

La aplicación se abrirá automáticamente en `http://localhost:8501`. La base de datos SQLite (`vialnet.db`) se crea de forma automática en el primer arranque, incluyendo la siembra inicial de los 5 tramos piloto del proyecto.

## 🗺️ Contexto del proyecto

VialNet fue desarrollado como Proyecto Preprofesional en la Universidad de Ingeniería y Tecnología (UTEC), orientado a apoyar a la Subgerencia de Gestión de Riesgos y Mantenimiento de la Municipalidad Distrital de Ocongate en la toma de decisiones sobre conservación vial, siguiendo criterios del Manual de Conservación Vial vigente en el Perú.

## 👤 Autor

**Frank Puma Mamani** — Estudiante de Ingeniería Civil, UTEC
Código: 202220055

## 📄 Licencia

Este proyecto se distribuye con fines académicos y de gestión municipal. Consulta con el autor antes de su reutilización o adaptación a otros contextos institucionales.
