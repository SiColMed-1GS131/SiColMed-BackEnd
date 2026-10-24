CREATE OR REPLACE FUNCTION obtener_perfil_medico(p_id_medico integer)
RETURNS jsonb
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_perfil jsonb;
BEGIN
    SELECT jsonb_build_object(
        'datos_personales', jsonb_build_object(
            'id_medico', m.id_medico,
            'id_usuario', m.id_usuario,
            'numero_idoneidad', m.numero_idoneidad,
            'numero_registro_medico', m.numero_registro_medico,
            'cedula', m.cedula,
            'primer_nombre', m.primer_nombre,
            'segundo_nombre', m.segundo_nombre,
            'apellido_paterno', m.apellido_paterno,
            'apellido_materno', m.apellido_materno,
            'foto', m.foto,
            'fecha_nacimiento', m.fecha_nacimiento,
            'edad', EXTRACT(YEAR FROM age(CURRENT_DATE, m.fecha_nacimiento))::integer,
            'telefono_residencial', m.telefono_residencial,
            'celular', m.celular,
            'email_personal', m.email_personal
        ),
        'direccion_residencial', (
            SELECT jsonb_build_object(
                       'apartado_postal', d.apartado_postal, 'calle', d.calle,
                       'edificio', d.edificio, 'numero_direccion', d.numero_direccion,
                       'provincia', pr.nombre, 'distrito', di.nombre, 'corregimiento', co.nombre)
              FROM direccion d
              LEFT JOIN provincia pr     ON pr.id_provincia = d.id_provincia
              LEFT JOIN distrito di      ON di.id_distrito = d.id_distrito
              LEFT JOIN corregimiento co ON co.id_corregimiento = d.id_corregimiento
             WHERE d.id_direccion = m.id_direccion),
        'lugares_trabajo', COALESCE((
            SELECT jsonb_agg(jsonb_build_object(
                       'id_lugar_trabajo', lt.id_lugar_trabajo,
                       'empresa_institucion', lt.empresa_institucion,
                       'cargo', lt.cargo,
                       'telefono_trabajo', lt.telefono_trabajo,
                       'email_laboral', lt.email_laboral,
                       'direccion', (
                           SELECT jsonb_build_object(
                                      'apartado_postal', d2.apartado_postal, 'calle', d2.calle,
                                      'edificio', d2.edificio, 'numero_direccion', d2.numero_direccion,
                                      'provincia', pr2.nombre, 'distrito', di2.nombre,
                                      'corregimiento', co2.nombre)
                             FROM direccion d2
                             LEFT JOIN provincia pr2     ON pr2.id_provincia = d2.id_provincia
                             LEFT JOIN distrito di2      ON di2.id_distrito = d2.id_distrito
                             LEFT JOIN corregimiento co2 ON co2.id_corregimiento = d2.id_corregimiento
                            WHERE d2.id_direccion = lt.id_direccion))
                       ORDER BY lt.id_lugar_trabajo)
              FROM lugar_trabajo lt WHERE lt.id_medico = m.id_medico), '[]'::jsonb),
        'estudios', COALESCE((
            SELECT jsonb_agg(jsonb_build_object(
                       'id_estudio', e.id_estudio, 'tipo_estudio', e.tipo_estudio,
                       'titulo', e.titulo, 'institucion', e.institucion,
                       'lugar', e.lugar, 'fecha', e.fecha)
                       ORDER BY e.fecha, e.id_estudio)
              FROM estudio_medico e WHERE e.id_medico = m.id_medico), '[]'::jsonb),
        'especialidades', COALESCE((
            SELECT jsonb_agg(jsonb_build_object(
                       'id_especialidad', es.id_especialidad, 'nombre', es.nombre)
                       ORDER BY es.nombre)
              FROM medico_especialidad me
              JOIN especialidad es ON es.id_especialidad = me.id_especialidad
             WHERE me.id_medico = m.id_medico), '[]'::jsonb),
        'subespecialidades', COALESCE((
            SELECT jsonb_agg(jsonb_build_object(
                       'id_subespecialidad', su.id_subespecialidad, 'nombre', su.nombre,
                       'id_especialidad', su.id_especialidad)
                       ORDER BY su.nombre)
              FROM medico_subespecialidad ms
              JOIN subespecialidad su ON su.id_subespecialidad = ms.id_subespecialidad
             WHERE ms.id_medico = m.id_medico), '[]'::jsonb),
        'asociaciones', COALESCE((
            SELECT jsonb_agg(jsonb_build_object(
                       'id_asociacion', a.id_asociacion, 'nombre', a.nombre)
                       ORDER BY a.nombre)
              FROM medico_asociacion ma
              JOIN asociacion a ON a.id_asociacion = ma.id_asociacion
             WHERE ma.id_medico = m.id_medico), '[]'::jsonb),
        'certificaciones', COALESCE((
            SELECT jsonb_agg(jsonb_build_object(
                       'id_certificacion', c.id_certificacion,
                       'fecha_obtencion', c.fecha_obtencion,
                       'puntaje', c.puntaje,
                       'fecha_expiracion', c.fecha_expiracion,
                       'vigente', COALESCE(c.fecha_expiracion >= CURRENT_DATE, false))
                       ORDER BY c.fecha_obtencion DESC, c.id_certificacion DESC)
              FROM certificacion c WHERE c.id_medico = m.id_medico), '[]'::jsonb)
    )
      INTO v_perfil
      FROM medico m
     WHERE m.id_medico = p_id_medico;

    IF v_perfil IS NULL THEN
        RAISE EXCEPTION 'El médico % no existe', p_id_medico;
    END IF;

    RETURN v_perfil;
END;
$$;