
-- Nota: los parámetros de paginación tienen valores predeterminados.
-- Los filtros son opcionales y se combinan mediante AND.

CREATE OR REPLACE FUNCTION filtrar_medicos(
    p_apellido              TEXT DEFAULT NULL,
    p_id_especialidad       INTEGER DEFAULT NULL,
    p_id_subespecialidad    INTEGER DEFAULT NULL,
    p_id_asociacion         INTEGER DEFAULT NULL,
    p_certificacion_vigente BOOLEAN DEFAULT NULL,
    p_id_provincia          INTEGER DEFAULT NULL,
    p_lugar_trabajo         TEXT DEFAULT NULL,
    p_pagina                INTEGER DEFAULT 1,
    p_tamano_pagina         INTEGER DEFAULT 20
)
RETURNS TABLE (
    id_medico             INTEGER,
    nombre_completo       TEXT,
    numero_idoneidad      TEXT,
    especialidades        TEXT,
    asociaciones          TEXT,
    certificacion_vigente BOOLEAN,
    provincia             TEXT,
    lugar_trabajo         TEXT,
    total_resultados      BIGINT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_apellido TEXT := NULLIF(BTRIM(p_apellido), '');
    v_lugar    TEXT := NULLIF(BTRIM(p_lugar_trabajo), '');
BEGIN
    IF p_pagina IS NULL OR p_pagina < 1 THEN
        RAISE EXCEPTION 'La página debe ser mayor o igual que 1';
    END IF;

    IF p_tamano_pagina IS NULL
       OR p_tamano_pagina < 1
       OR p_tamano_pagina > 100 THEN
        RAISE EXCEPTION 'El tamaño de página debe estar entre 1 y 100';
    END IF;

    RETURN QUERY
    WITH base AS (
        SELECT
            m.id_medico,
            m.apellido_paterno,
            m.apellido_materno,
            m.primer_nombre,

            BTRIM(CONCAT_WS(
                ' ',
                m.primer_nombre,
                m.segundo_nombre,
                m.apellido_paterno,
                m.apellido_materno
            ))::TEXT AS nombre_completo,

            m.numero_idoneidad::TEXT AS numero_idoneidad,

            (
                SELECT STRING_AGG(e.nombre, ', ' ORDER BY e.nombre)
                FROM medico_especialidad me
                JOIN especialidad e
                    ON e.id_especialidad = me.id_especialidad
                WHERE me.id_medico = m.id_medico
            )::TEXT AS especialidades,

            (
                SELECT STRING_AGG(a.nombre, ', ' ORDER BY a.nombre)
                FROM medico_asociacion ma
                JOIN asociacion a
                    ON a.id_asociacion = ma.id_asociacion
                WHERE ma.id_medico = m.id_medico
            )::TEXT AS asociaciones,

            EXISTS (
                SELECT 1
                FROM certificacion c
                WHERE c.id_medico = m.id_medico
                  AND c.fecha_expiracion >= CURRENT_DATE
            ) AS vigente,

            pr.nombre::TEXT AS provincia,
            d.id_provincia,

            (
                SELECT STRING_AGG(
                    lt.empresa_institucion,
                    ', ' ORDER BY lt.empresa_institucion
                )
                FROM lugar_trabajo lt
                WHERE lt.id_medico = m.id_medico
            )::TEXT AS lugares

        FROM medico m
        LEFT JOIN direccion d
            ON d.id_direccion = m.id_direccion
        LEFT JOIN provincia pr
            ON pr.id_provincia = d.id_provincia
    ),
    filtrados AS (
        SELECT b.*
        FROM base b
        WHERE (
            v_apellido IS NULL
            OR LOWER(COALESCE(b.apellido_paterno, ''))
                LIKE '%' || LOWER(v_apellido) || '%'
            OR LOWER(COALESCE(b.apellido_materno, ''))
                LIKE '%' || LOWER(v_apellido) || '%'
        )
        AND (
            p_id_especialidad IS NULL
            OR EXISTS (
                SELECT 1
                FROM medico_especialidad x
                WHERE x.id_medico = b.id_medico
                  AND x.id_especialidad = p_id_especialidad
            )
        )
        AND (
            p_id_subespecialidad IS NULL
            OR EXISTS (
                SELECT 1
                FROM medico_subespecialidad x
                WHERE x.id_medico = b.id_medico
                  AND x.id_subespecialidad = p_id_subespecialidad
            )
        )
        AND (
            p_id_asociacion IS NULL
            OR EXISTS (
                SELECT 1
                FROM medico_asociacion x
                WHERE x.id_medico = b.id_medico
                  AND x.id_asociacion = p_id_asociacion
            )
        )
        AND (
            p_certificacion_vigente IS NULL
            OR b.vigente = p_certificacion_vigente
        )
        AND (
            p_id_provincia IS NULL
            OR b.id_provincia = p_id_provincia
        )
        AND (
            v_lugar IS NULL
            OR EXISTS (
                SELECT 1
                FROM lugar_trabajo l
                WHERE l.id_medico = b.id_medico
                  AND LOWER(COALESCE(l.empresa_institucion, ''))
                      LIKE '%' || LOWER(v_lugar) || '%'
            )
        )
    )
    SELECT
        f.id_medico,
        f.nombre_completo,
        f.numero_idoneidad,
        f.especialidades,
        f.asociaciones,
        f.vigente,
        f.provincia,
        f.lugares,
        COUNT(*) OVER () AS total_resultados
    FROM filtrados f
    ORDER BY
        f.apellido_paterno ASC NULLS LAST,
        f.apellido_materno ASC NULLS LAST,
        f.primer_nombre ASC NULLS LAST,
        f.id_medico ASC
    LIMIT p_tamano_pagina
    OFFSET (p_pagina - 1) * p_tamano_pagina;

END;
$$;
