

CREATE SCHEMA IF NOT EXISTS contabilidad;
SET search_path TO contabilidad;

-- ==============================
-- TABLA DE USUARIOS
-- ==============================
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    nombre_completo VARCHAR(100),
    rol VARCHAR(50),
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==============================
-- TABLA DE CATALOGO DE CUENTAS
-- ==============================
CREATE TABLE IF NOT EXISTS cuentas (
    id_cuenta SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    tipo VARCHAR(20) CHECK (tipo IN ('Activo', 'Pasivo', 'Capital', 'Ingreso', 'Gasto')),
    nivel INT NOT NULL DEFAULT 1,
    cuenta_padre INT REFERENCES cuentas(id_cuenta) ON DELETE SET NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_usuario_crea INT REFERENCES usuarios(id_usuario)
);

-- ==============================
-- TABLA DE MANUAL DE CUENTAS
-- ==============================
CREATE TABLE IF NOT EXISTS manual_cuentas (
    id_manual SERIAL PRIMARY KEY,
    id_cuenta INT NOT NULL REFERENCES cuentas(id_cuenta) ON DELETE CASCADE,
    descripcion TEXT NOT NULL,
    ejemplos TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_usuario_crea INT REFERENCES usuarios(id_usuario)
);

-- ==============================
-- TABLA PARTIDAS (DIARIO GENERAL)
-- ==============================
CREATE TABLE IF NOT EXISTS partidas (
    id_partida SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    descripcion TEXT NOT NULL,
    tipo VARCHAR(20) DEFAULT 'DIARIO' CHECK (tipo IN ('DIARIO', 'AJUSTE', 'CIERRE')),
    id_usuario_crea INT REFERENCES usuarios(id_usuario),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==============================
-- DETALLE DE PARTIDAS (ASIENTOS)
-- ==============================
CREATE TABLE IF NOT EXISTS partida_detalle (
    id_detalle SERIAL PRIMARY KEY,
    id_partida INT NOT NULL REFERENCES partidas(id_partida) ON DELETE CASCADE,
    id_cuenta INT NOT NULL REFERENCES cuentas(id_cuenta),
    debe NUMERIC(12,2) DEFAULT 0,
    haber NUMERIC(12,2) DEFAULT 0,
    descripcion TEXT
);

-- ==============================
-- MAYORIZACIÓN
-- ==============================
CREATE TABLE IF NOT EXISTS mayor (
    id_mayor SERIAL PRIMARY KEY,
    id_cuenta INT NOT NULL REFERENCES cuentas(id_cuenta),
    saldo_debe NUMERIC(12,2) DEFAULT 0,
    saldo_haber NUMERIC(12,2) DEFAULT 0,
    saldo_final NUMERIC(12,2) DEFAULT 0,
    periodo DATE NOT NULL,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==============================
-- BALANZA DE COMPROBACIÓN
-- ==============================
CREATE TABLE IF NOT EXISTS balanza (
    id_balanza SERIAL PRIMARY KEY,
    periodo DATE NOT NULL,
    id_cuenta INT NOT NULL REFERENCES cuentas(id_cuenta),
    saldo_anterior NUMERIC(12,2) DEFAULT 0,
    movimientos_debe NUMERIC(12,2) DEFAULT 0,
    movimientos_haber NUMERIC(12,2) DEFAULT 0,
    saldo_final NUMERIC(12,2) DEFAULT 0
);

-- ==============================
-- FACTURAS
-- ==============================
CREATE TABLE IF NOT EXISTS facturas (
    id_factura SERIAL PRIMARY KEY,
    numero_factura VARCHAR(20) UNIQUE NOT NULL,
    fecha DATE NOT NULL,
    cliente VARCHAR(100),
    total NUMERIC(12,2) NOT NULL,
    iva NUMERIC(12,2) DEFAULT 0,
    total_con_iva NUMERIC(12,2) GENERATED ALWAYS AS (total + iva) STORED,
    id_usuario_crea INT REFERENCES usuarios(id_usuario),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==============================
-- REPORTE DE VENTAS DIARIAS (VIEW)
-- ==============================
CREATE OR REPLACE VIEW reporte_ventas_diarias AS
SELECT
    fecha,
    COUNT(*) AS cantidad_facturas,
    SUM(total) AS total_ventas,
    SUM(iva) AS total_iva,
    SUM(total + iva) AS total_con_iva
FROM facturas
GROUP BY fecha
ORDER BY fecha DESC;

-- ==============================
-- TABLA DE AUDITORÍA
-- ==============================
CREATE TABLE IF NOT EXISTS auditoria (
    id_auditoria SERIAL PRIMARY KEY,
    tabla_afectada VARCHAR(50),
    accion VARCHAR(20),
    id_registro INT,
    id_usuario INT REFERENCES usuarios(id_usuario),
    fecha_accion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    descripcion TEXT
);
