# 🛣️ VialNet

**Plataforma inteligente de gestión de mantenimiento vial rural**, con almacenamiento **100% en la nube**: cualquier persona que abra el enlace ve los mismos datos, en tiempo real, desde cualquier dispositivo.

Proyecto piloto implementado sobre la red vial del Distrito de Ocongate (Provincia de Quispicanchi, Región Cusco, Perú), validado sobre 5 tramos reales.

---

## 📋 Descripción

VialNet centraliza el ciclo completo de gestión de un tramo vial: inventario, inspección técnica de daños (criterios tipo Provías), cálculo automático de índices de estado, programación de intervenciones y reportes ejecutivos exportables — todo respaldado por una base de datos PostgreSQL en Supabase y un bucket de Supabase Storage para fotos y documentos.

## ✨ Características principales

- **Persistencia real en la nube** — todo registro (tramo, ficha de daño, programación de mantenimiento, foto) queda guardado en PostgreSQL/Supabase, visible para cualquiera que entre al enlace.
- **Fotos y PDFs en Supabase Storage** — cada fotografía y cada adjunto se sube a un bucket público y se referencia por URL; se muestran en la app y se incrustan en los documentos generados.
- **CRUD completo** — crear, consultar, actualizar y eliminar tramos, fichas de daño y programaciones, con manejo de errores y mensajes claros en cada operación.
- **Reportes y dashboards** — indicadores en tiempo real, gráficos interactivos (Plotly), ranking de tramos críticos.
- **Exportación con evidencia fotográfica** — reportes en Excel (openpyxl) y PDF (fpdf2), con una sección de "Evidencia Fotográfica del Mantenimiento" en cuadrícula.

## 🧱 Arquitectura y tecnologías

| Capa | Tecnología |
|---|---|
| Interfaz web | [Streamlit](https://streamlit.io/) |
| Base de datos | **PostgreSQL en Supabase** (conexión vía `psycopg2`, con pool de conexiones) |
| Almacenamiento de archivos | **Supabase Storage** (bucket público `vialnet-archivos`) |
| Procesamiento de datos | Pandas |
| Visualización | Plotly Express / Graph Objects |
| Exportación Excel / PDF | OpenPyXL / fpdf2 |
| Imágenes | Pillow (PIL) |
| Lenguaje | Python 3.10+ |

### ¿Por qué antes no se guardaban los datos?

La versión anterior usaba **SQLite** (`vialnet.db`), un archivo en el disco del propio contenedor donde corre Streamlit. Streamlit Community Cloud **no garantiza almacenamiento persistente**: cada vez que la app se reinicia, se actualiza o se redespliega, ese contenedor se recrea desde cero y el archivo `.db` desaparece — por eso los mantenimientos "se perdían" o no aparecían para otras personas (cada visitante podía además estar viendo una instancia/contenedor distinto). La solución no es un ajuste de configuración: requiere una base de datos externa que viva fuera del ciclo de vida del contenedor — de ahí la migración a Supabase.

## 📁 Estructura de módulos

```
1. 🏠 Inicio                        — Presentación general, KPIs y gráficos resumen
2. 🛣️ Registro de tramos            — Alta de tramos + fotografías del mantenimiento + adjuntos
3. 📂 Consulta de tramos            — Buscar / filtrar / editar / eliminar / descargar
4. 📋 Ficha técnica de daños        — Ficha tipo Provías + clasificación automática + ICT
5. 🗓️ Programación de mantenimiento — Cronograma y programación de intervenciones
6. 📊 Reportes                      — Reportes automáticos + gráficos + exportación Excel/PDF
```

---

## ☁️ Configuración de Supabase (una sola vez)

### 1. Crear el proyecto

1. Entra a [supabase.com](https://supabase.com) → **New project**.
2. Elige nombre, contraseña de base de datos (guárdala) y región (idealmente cercana a tus usuarios, ej. São Paulo para Perú).
3. Espera ~2 minutos a que aprovisione el proyecto.

### 2. Obtener las credenciales

En el dashboard de tu proyecto:

- **Base de datos:** *Project Settings → Database → Connection string → URI*. Copia la cadena y reemplaza `[YOUR-PASSWORD]` por la contraseña que creaste. Esto es tu `SUPABASE_DB_URL`.
- **API:** *Project Settings → API*. Copia el **Project URL** (`SUPABASE_URL`) y la clave **`service_role`** (`SUPABASE_SERVICE_KEY` — es secreta, no la confundas con la `anon` key).

### 3. Crear el bucket de Storage

*Storage → New bucket* → nombre `vialnet-archivos` → márcalo como **Public**. (También puedes crearlo ejecutando `supabase_schema.sql` en el SQL Editor — incluido en este proyecto).

### 4. Las tablas se crean solas

No necesitas ejecutar ningún script manualmente: al arrancar, VialNet crea (o migra) automáticamente las tablas `tramos`, `danos`, `intervenciones` y `tramo_fotos` mediante `CREATE TABLE IF NOT EXISTS` y `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`. El archivo `supabase_schema.sql` se incluye solo como referencia/inspección.

---

## 🚀 Instalación y ejecución en local

**Requisitos previos:** Python 3.10 o superior y un proyecto de Supabase ya configurado (paso anterior).

```bash
# 1. Clonar el repositorio
git clone https://github.com/<tu-usuario>/vialnet.git
cd vialnet

# 2. Crear y activar un entorno virtual
python -m venv .venv
source .venv/bin/activate      # En Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar credenciales
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edita .streamlit/secrets.toml con tus valores reales de Supabase

# 5. Ejecutar
streamlit run vialnet.py
```

La app abrirá en `http://localhost:8501`. Al primer arranque, VialNet crea las tablas en tu base de datos de Supabase y siembra los 5 tramos piloto del proyecto (si aún no existen).

---

## ☁️ Despliegue en Streamlit Community Cloud

1. Sube este proyecto a un repositorio de GitHub (público o privado).
2. Entra a [share.streamlit.io](https://share.streamlit.io) → **New app** → selecciona tu repositorio, rama y el archivo `vialnet.py`.
3. Antes de desplegar (o después, desde *Settings*), abre **Settings → Secrets** y pega el contenido de tu `secrets.toml` con tus valores reales:

   ```toml
   SUPABASE_DB_URL = "postgresql://postgres:tu_password@db.xxxx.supabase.co:5432/postgres"
   SUPABASE_URL = "https://xxxx.supabase.co"
   SUPABASE_SERVICE_KEY = "eyJ..."
   SUPABASE_STORAGE_BUCKET = "vialnet-archivos"
   ```
4. Despliega. A partir de aquí, **cualquier persona que abra el enlace verá los mismos mantenimientos, tramos y fotos**, sin importar desde qué dispositivo entre — porque todos apuntan a la misma base de datos en la nube, no a un archivo local del contenedor.
5. Cada vez que la app se reinicie o redespliegues una actualización de código, los datos **permanecen intactos** en Supabase.

---

## 🔒 Seguridad y buenas prácticas aplicadas

- Todas las credenciales viven en `st.secrets` — nunca hardcodeadas ni versionadas (`.streamlit/secrets.toml` está en `.gitignore`).
- Conexión a PostgreSQL vía **pool de conexiones** (`psycopg2.pool.SimpleConnectionPool`, cacheado con `st.cache_resource`) en vez de abrir una conexión nueva por cada acción — reduce la latencia y la carga sobre la base de datos.
- Cada operación de escritura usa `try/except/finally` con `rollback()` en caso de error, garantizando que las conexiones siempre vuelvan al pool y que una transacción fallida no deje la base de datos en un estado inconsistente.
- Los códigos de tramo duplicados y otros errores de validación de base de datos se capturan y se muestran como mensajes claros en la interfaz, no como errores técnicos crudos.
- La clave `service_role` de Supabase solo se usa en el backend (dentro de `st.secrets`, nunca expuesta al navegador).
- Las descargas de fotos desde Storage se cachean (`st.cache_data`, TTL 1 hora) para no re-descargar la misma imagen varias veces en una sesión.

## ⚠️ Limitaciones conocidas / próximos pasos sugeridos

- El bucket de Storage se creó como **público** para simplificar la visualización de fotos entre usuarios (requisito del proyecto). Si más adelante se necesita restringir el acceso, se puede migrar a URLs firmadas (`create_signed_url`) sin cambiar el resto de la arquitectura.
- No hay un sistema de autenticación de usuarios todavía (cualquiera con el enlace puede crear/editar/eliminar). Si se requiere, Supabase Auth se integra de forma natural sobre esta misma base.
- La conexión física a PostgreSQL abre un socket por acción (mitigado con el pool); para tráfico muy alto conviene evaluar Supabase **Connection Pooling (PgBouncer, modo transaction)** en el `SUPABASE_DB_URL`.

## 🗺️ Contexto del proyecto

VialNet fue desarrollado como Proyecto Preprofesional en la Universidad de Ingeniería y Tecnología (UTEC), orientado a apoyar a la Subgerencia de Gestión de Riesgos y Mantenimiento de la Municipalidad Distrital de Ocongate en la toma de decisiones sobre conservación vial, siguiendo criterios del Manual de Conservación Vial vigente en el Perú.

## 👤 Autor

**Frank Puma Mamani** — Estudiante de Ingeniería Civil, UTEC
Código: 202220055

## 📄 Licencia

Este proyecto se distribuye con fines académicos y de gestión municipal. Consulta con el autor antes de su reutilización o adaptación a otros contextos institucionales.
