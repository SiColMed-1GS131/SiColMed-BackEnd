CREATE OR REPLACE FUNCTION registrar_carga_medicos(
    p_id_administrador integer,
    p_archivo          text,
    p_procesados       integer,
    p_registrados      integer,
    p_errores          jsonb
)
RETURNS integer
LANGUAGE plpgsql
AS $$
-- Auditoría de una carga masiva de médicos por CSV (POST /medicos/importar).
-- Una fila en auditoria por cada carga, con el resumen en descripcion (JSON):
-- {"archivo", "procesados", "registrados", "rechazados", "errores": [{"fila", "error"}]}.
-- id_registro = 0: la carga no corresponde a un único registro; los médicos creados
-- quedan en la tabla medico.
DECLARE
    v_id_rol       integer;
    v_id_auditoria integer;
BEGIN
    SELECT u.id_rol
      INTO v_id_rol
      FROM usuario u
      JOIN rol r ON r.id_rol = u.id_rol
     WHERE u.id_usuario = p_id_administrador
       AND u.activo
       AND r.nombre = 'admin_cmp';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'El usuario % no existe, esta inactivo o no es administrador', p_id_administrador;
    END IF;

    IF p_procesados IS NULL OR p_procesados < 0
       OR p_registrados IS NULL OR p_registrados < 0 OR p_registrados > p_procesados THEN
        RAISE EXCEPTION 'Los conteos de la carga no son validos';
    END IF;

    IF p_errores IS NULL OR jsonb_typeof(p_errores) <> 'array' THEN
        RAISE EXCEPTION 'Los errores de la carga deben ser un arreglo JSON';
    END IF;

    INSERT INTO auditoria (id_usuario, id_rol, accion, entidad, id_registro, fecha_hora, descripcion)
    VALUES (
        p_id_administrador,
        v_id_rol,
        'CARGA_MASIVA_MEDICOS',
        'MEDICO',
        0,
        now(),
        jsonb_build_object(
            'archivo', coalesce(nullif(btrim(p_archivo), ''), 'sin_nombre.csv'),
            'procesados', p_procesados,
            'registrados', p_registrados,
            'rechazados', p_procesados - p_registrados,
            'errores', p_errores
        )::text
    )
    RETURNING id_auditoria INTO v_id_auditoria;

    RETURN v_id_auditoria;
END;
$$;
