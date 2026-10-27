CREATE OR REPLACE FUNCTION listar_solicitudes_cambio(p_estado text DEFAULT NULL)
RETURNS TABLE (
    id_solicitud_cambio integer,
    id_medico           integer,
    nombre_completo     text,
    estado              text,
    fecha_solicitud     timestamp,
    cambios             jsonb
)
LANGUAGE plpgsql
STABLE
AS $$
#variable_conflict use_column
DECLARE
    v_estado text := upper(nullif(btrim(p_estado), ''));
BEGIN
    IF v_estado IS NOT NULL AND v_estado NOT IN ('PENDIENTE', 'PROCESADO') THEN
        RAISE EXCEPTION 'Estado inválido: use PENDIENTE o PROCESADO';
    END IF;

    RETURN QUERY
    SELECT s.id_solicitud_cambio,
           s.id_medico,
           btrim(concat_ws(' ', m.primer_nombre, m.segundo_nombre,
                                m.apellido_paterno, m.apellido_materno)),
           s.estado,
           s.fecha_solicitud,
           s.cambios
      FROM solicitud_cambio s
      JOIN medico m ON m.id_medico = s.id_medico
     WHERE v_estado IS NULL OR s.estado = v_estado
     ORDER BY s.fecha_solicitud, s.id_solicitud_cambio;
END;
$$;