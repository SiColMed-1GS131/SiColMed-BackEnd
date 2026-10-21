CREATE OR REPLACE FUNCTION filtrar_medicos(
    p_apellido              text    DEFAULT NULL,
    p_id_especialidad       integer DEFAULT NULL,
    p_id_subespecialidad    integer DEFAULT NULL,
    p_id_asociacion         integer DEFAULT NULL,
    p_certificacion_vigente boolean DEFAULT NULL,
    p_id_provincia          integer DEFAULT NULL,
    p_lugar_trabajo         text    DEFAULT NULL
)
RETURNS TABLE (
    id_medico             integer,
    nombre_completo       text,
    numero_idoneidad      text,
    especialidades        text,
    asociaciones          text,
    certificacion_vigente boolean,
    provincia             text,
    lugar_trabajo         text
)
LANGUAGE plpgsql
STABLE
AS $$
#variable_conflict use_column
DECLARE
    v_apellido text := nullif(btrim(p_apellido), '');
    v_lugar    text := nullif(btrim(p_lugar_trabajo), '');
    v_filtros  integer;
BEGIN
    v_filtros := (v_apellido IS NOT NULL)::integer
               + (p_id_especialidad IS NOT NULL)::integer
               + (p_id_subespecialidad IS NOT NULL)::integer
               + (p_id_asociacion IS NOT NULL)::integer
               + (p_certificacion_vigente IS NOT NULL)::integer
               + (p_id_provincia IS NOT NULL)::integer
               + (v_lugar IS NOT NULL)::integer;
    IF v_filtros > 1 THEN
        RAISE EXCEPTION 'Debe enviar solo un filtro a la vez';
    END IF;

    RETURN QUERY
    SELECT b.id_medico, b.nombre_completo, b.numero_idoneidad, b.especialidades,
           b.asociaciones, b.vigente, b.provincia, b.lugares
      FROM (
            SELECT m.id_medico,
                   m.apellido_paterno, m.apellido_materno, m.primer_nombre,
                   btrim(concat_ws(' ', m.primer_nombre, m.segundo_nombre,
                                        m.apellido_paterno, m.apellido_materno)) AS nombre_completo,
                   m.numero_idoneidad,
                   (SELECT string_agg(e.nombre, ', ' ORDER BY e.nombre)
                      FROM medico_especialidad me
                      JOIN especialidad e ON e.id_especialidad = me.id_especialidad
                     WHERE me.id_medico = m.id_medico) AS especialidades,
                   (SELECT string_agg(a.nombre, ', ' ORDER BY a.nombre)
                      FROM medico_asociacion ma
                      JOIN asociacion a ON a.id_asociacion = ma.id_asociacion
                     WHERE ma.id_medico = m.id_medico) AS asociaciones,
                   EXISTS (SELECT 1 FROM certificacion c
                            WHERE c.id_medico = m.id_medico
                              AND c.fecha_expiracion >= CURRENT_DATE) AS vigente,
                   pr.nombre AS provincia,
                   d.id_provincia,
                   (SELECT string_agg(lt.empresa_institucion, ', ' ORDER BY lt.empresa_institucion)
                      FROM lugar_trabajo lt
                     WHERE lt.id_medico = m.id_medico) AS lugares
              FROM medico m
              LEFT JOIN direccion d  ON d.id_direccion = m.id_direccion
              LEFT JOIN provincia pr ON pr.id_provincia = d.id_provincia
           ) b
     WHERE (v_apellido IS NULL
            OR strpos(lower(coalesce(b.apellido_paterno, '')), lower(v_apellido)) > 0
            OR strpos(lower(coalesce(b.apellido_materno, '')), lower(v_apellido)) > 0)
       AND (p_id_especialidad IS NULL OR EXISTS (
                SELECT 1 FROM medico_especialidad x
                 WHERE x.id_medico = b.id_medico AND x.id_especialidad = p_id_especialidad))
       AND (p_id_subespecialidad IS NULL OR EXISTS (
                SELECT 1 FROM medico_subespecialidad x
                 WHERE x.id_medico = b.id_medico AND x.id_subespecialidad = p_id_subespecialidad))
       AND (p_id_asociacion IS NULL OR EXISTS (
                SELECT 1 FROM medico_asociacion x
                 WHERE x.id_medico = b.id_medico AND x.id_asociacion = p_id_asociacion))
       AND (p_certificacion_vigente IS NULL OR b.vigente = p_certificacion_vigente)
       AND (p_id_provincia IS NULL OR b.id_provincia = p_id_provincia)
       AND (v_lugar IS NULL OR EXISTS (
                SELECT 1 FROM lugar_trabajo l
                 WHERE l.id_medico = b.id_medico
                   AND strpos(lower(coalesce(l.empresa_institucion, '')), lower(v_lugar)) > 0))
     ORDER BY b.apellido_paterno, b.apellido_materno, b.primer_nombre, b.id_medico;
END;
$$;