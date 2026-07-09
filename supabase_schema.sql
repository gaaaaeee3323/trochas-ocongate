-- ══════════════════════════════════════════════════════════════════════════
-- ESQUEMA DE BASE DE DATOS — VialNet (PostgreSQL / Supabase)
--
-- Este script es de referencia: VialNet crea y migra estas tablas
-- automáticamente al arrancar (ver init_db() en vialnet.py). Solo necesitas
-- ejecutar esto a mano si quieres inspeccionar el esquema antes de tiempo,
-- o recrear la base de datos manualmente en el SQL Editor de Supabase.
-- ══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS tramos (
    id SERIAL PRIMARY KEY,
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
    adjunto_pdf TEXT,             -- URL pública en Supabase Storage (no el archivo en sí)
    adjunto_pdf_nombre TEXT,
    altitud_msnm REAL,
    estado_drenaje TEXT,
    senalizacion TEXT,
    n_puentes INTEGER,
    n_badenes INTEGER,
    accesibilidad TEXT,
    cantera_fuente TEXT,
    fuente_lastre TEXT,
    ultima_intervencion TEXT,
    costo_rutinario REAL,
    costo_periodico REAL,
    gps_lat REAL,
    gps_lon REAL,
    observaciones TEXT
);

CREATE TABLE IF NOT EXISTS danos (
    id SERIAL PRIMARY KEY,
    tramo_id INTEGER REFERENCES tramos(id),
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
    tipo_mantenimiento TEXT,
    foto_dano TEXT                -- URL pública en Supabase Storage
);

CREATE TABLE IF NOT EXISTS intervenciones (
    id SERIAL PRIMARY KEY,
    tramo_id INTEGER REFERENCES tramos(id),
    dano_id INTEGER REFERENCES danos(id),
    tipo_mantenimiento TEXT,
    componente TEXT,
    prioridad TEXT,
    actividades TEXT,
    expediente TEXT,
    fecha_programada TEXT,
    fecha_fin TEXT,
    duracion_dias REAL,
    costo_estimado REAL,
    estado TEXT,
    responsable TEXT,
    observaciones TEXT,
    foto_evidencia TEXT           -- URL pública en Supabase Storage
);

CREATE TABLE IF NOT EXISTS tramo_fotos (
    id SERIAL PRIMARY KEY,
    tramo_id INTEGER NOT NULL REFERENCES tramos(id),
    nombre_archivo TEXT,
    imagen TEXT NOT NULL,         -- URL pública en Supabase Storage
    pie_foto TEXT,
    fecha_carga TEXT,
    orden INTEGER
);

-- Índices recomendados para acelerar las consultas más frecuentes.
CREATE INDEX IF NOT EXISTS idx_danos_tramo_id ON danos(tramo_id);
CREATE INDEX IF NOT EXISTS idx_intervenciones_tramo_id ON intervenciones(tramo_id);
CREATE INDEX IF NOT EXISTS idx_intervenciones_dano_id ON intervenciones(dano_id);
CREATE INDEX IF NOT EXISTS idx_tramo_fotos_tramo_id ON tramo_fotos(tramo_id);

-- ══════════════════════════════════════════════════════════════════════════
-- STORAGE — crear el bucket público donde se guardan fotos y PDFs adjuntos.
-- Puedes ejecutar esto aquí, o crearlo desde Storage → New bucket en el
-- dashboard de Supabase (nombre: vialnet-archivos, marcado como "Public").
-- ══════════════════════════════════════════════════════════════════════════
insert into storage.buckets (id, name, public)
values ('vialnet-archivos', 'vialnet-archivos', true)
on conflict (id) do nothing;
