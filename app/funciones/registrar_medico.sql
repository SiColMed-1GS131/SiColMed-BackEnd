
CREATE OR REPLACE FUNCTION registrar_medico(
    p_datos JSONB
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_medico             JSONB;
    v_direccion          JSONB;
    v_lugar_trabajo      JSONB;
    v_direccion_trabajo JSONB;
    v_estudio            JSONB;
    v_certificacion      JSONB;

    v_especialidades     JSONB;
    v_subespecialidades  JSONB;
    v_asociaciones       JSONB;

    v_idoneidad          TEXT;
    v_registro           TEXT;
    v_cedula             TEXT;

    v_id_provincia       INTEGER;
    v_id_distrito        INTEGER;
    v_id_corregimiento   INTEGER;

    v_id_direccion       INTEGER;
    v_id_direccion_trabajo INTEGER;
    v_id_medico          INTEGER;

    v_ids_especialidad   INTEGER[] := '{}';
    v_ids_subespecialidad INTEGER[] := '{}';
    v_ids_asociacion     INTEGER[] := '{}';

    v_id                 INTEGER;
BEGIN
    ----------------------------------------------------------------
    -- 1. Validar JSON principal
    ----------------------------------------------------------------

    IF p_datos IS NULL OR jsonb_typeof(p_datos) <> 'object' THEN
        RAISE EXCEPTION 'Los datos deben enviarse como un objeto JSON';
    END IF;

    v_medico := p_datos->'medico';
    v_direccion := p_datos->'direccion';
    v_lugar_trabajo := p_datos->'lugar_trabajo';
    v_direccion_trabajo := p_datos->'direccion_trabajo';
    v_estudio := p_datos->'estudio_medico';
    v_certificacion := p_datos->'certificacion';

    IF jsonb_typeof(v_medico) IS DISTINCT FROM 'object' THEN
        RAISE EXCEPTION 'La sección medico es obligatoria';
    END IF;

    IF jsonb_typeof(v_direccion) IS DISTINCT FROM 'object' THEN
        RAISE EXCEPTION 'La sección direccion es obligatoria';
    END IF;

    IF jsonb_typeof(v_lugar_trabajo) IS DISTINCT FROM 'object' THEN
        RAISE EXCEPTION 'La sección lugar_trabajo es obligatoria';
    END IF;

    IF jsonb_typeof(v_direccion_trabajo) IS DISTINCT FROM 'object' THEN
        RAISE EXCEPTION 'La sección direccion_trabajo es obligatoria';
    END IF;

    IF jsonb_typeof(v_estudio) IS DISTINCT FROM 'object' THEN
        RAISE EXCEPTION 'La sección estudio_medico es obligatoria';
    END IF;

    IF jsonb_typeof(v_certificacion) IS DISTINCT FROM 'object' THEN
        RAISE EXCEPTION 'La sección certificacion es obligatoria';
    END IF;

    ----------------------------------------------------------------
    -- 2. Validar datos obligatorios del médico
    ----------------------------------------------------------------

    v_idoneidad := NULLIF(BTRIM(v_medico->>'numero_idoneidad'), '');
    v_registro := NULLIF(BTRIM(v_medico->>'numero_registro_medico'), '');
    v_cedula := NULLIF(BTRIM(v_medico->>'cedula'), '');

    IF v_idoneidad IS NULL THEN
        RAISE EXCEPTION 'El número de idoneidad es obligatorio';
    END IF;

    IF v_registro IS NULL THEN
        RAISE EXCEPTION 'El número de registro médico es obligatorio';
    END IF;

    IF v_cedula IS NULL THEN
        RAISE EXCEPTION 'La cédula es obligatoria';
    END IF;

    IF NULLIF(BTRIM(v_medico->>'primer_nombre'), '') IS NULL
       OR NULLIF(BTRIM(v_medico->>'apellido_paterno'), '') IS NULL THEN
        RAISE EXCEPTION 'El primer nombre y el apellido paterno son obligatorios';
    END IF;

    IF NULLIF(BTRIM(v_medico->>'fecha_nacimiento'), '') IS NULL THEN
        RAISE EXCEPTION 'La fecha de nacimiento es obligatoria';
    END IF;

    IF (v_medico->>'fecha_nacimiento')::DATE > CURRENT_DATE THEN
        RAISE EXCEPTION 'La fecha de nacimiento no puede ser futura';
    END IF;

    IF EXISTS (
        SELECT 1 FROM medico
        WHERE numero_idoneidad = v_idoneidad
    ) THEN
        RAISE EXCEPTION 'Ya existe un médico con el número de idoneidad %',
            v_idoneidad;
    END IF;

    IF EXISTS (
        SELECT 1 FROM medico
        WHERE numero_registro_medico = v_registro
    ) THEN
        RAISE EXCEPTION 'Ya existe un médico con el número de registro médico %',
            v_registro;
    END IF;

    IF EXISTS (
        SELECT 1 FROM medico
        WHERE cedula = v_cedula
    ) THEN
        RAISE EXCEPTION 'Ya existe un médico con la cédula %',
            v_cedula;
    END IF;

    ----------------------------------------------------------------
    -- 3. Validar dirección del médico
    ----------------------------------------------------------------

    IF NULLIF(BTRIM(v_direccion->>'id_corregimiento'), '') IS NULL THEN
        RAISE EXCEPTION 'El corregimiento de la dirección del médico es obligatorio';
    END IF;

    v_id_corregimiento := (v_direccion->>'id_corregimiento')::INTEGER;

    SELECT d.id_provincia, c.id_distrito
      INTO v_id_provincia, v_id_distrito
      FROM corregimiento c
      JOIN distrito d ON d.id_distrito = c.id_distrito
     WHERE c.id_corregimiento = v_id_corregimiento;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'El corregimiento % no existe',
            v_id_corregimiento;
    END IF;

    ----------------------------------------------------------------
    -- 4. Crear dirección del médico
    ----------------------------------------------------------------

    INSERT INTO direccion (
        apartado_postal,
        calle,
        edificio,
        numero_direccion,
        id_provincia,
        id_distrito,
        id_corregimiento
    )
    VALUES (
        NULLIF(BTRIM(v_direccion->>'apartado_postal'), ''),
        NULLIF(BTRIM(v_direccion->>'calle'), ''),
        NULLIF(BTRIM(v_direccion->>'edificio'), ''),
        NULLIF(BTRIM(v_direccion->>'numero_direccion'), ''),
        v_id_provincia,
        v_id_distrito,
        v_id_corregimiento
    )
    RETURNING id_direccion INTO v_id_direccion;

    ----------------------------------------------------------------
    -- 5. Crear médico
    ----------------------------------------------------------------

    INSERT INTO medico (
        numero_idoneidad,
        numero_registro_medico,
        cedula,
        primer_nombre,
        segundo_nombre,
        apellido_paterno,
        apellido_materno,
        foto,
        fecha_nacimiento,
        telefono_residencial,
        celular,
        email_personal,
        id_direccion
    )
    VALUES (
        v_idoneidad,
        v_registro,
        v_cedula,
        BTRIM(v_medico->>'primer_nombre'),
        NULLIF(BTRIM(v_medico->>'segundo_nombre'), ''),
        BTRIM(v_medico->>'apellido_paterno'),
        NULLIF(BTRIM(v_medico->>'apellido_materno'), ''),
        v_medico->>'foto',
        (v_medico->>'fecha_nacimiento')::DATE,
        NULLIF(BTRIM(v_medico->>'telefono_residencial'), ''),
        NULLIF(BTRIM(v_medico->>'celular'), ''),
        NULLIF(BTRIM(v_medico->>'email_personal'), ''),
        v_id_direccion
    )
    RETURNING id_medico INTO v_id_medico;

    ----------------------------------------------------------------
    -- 6. Validar y crear dirección del lugar de trabajo
    ----------------------------------------------------------------

    IF NULLIF(BTRIM(v_direccion_trabajo->>'id_corregimiento'), '') IS NULL THEN
        RAISE EXCEPTION 'El corregimiento de la dirección laboral es obligatorio';
    END IF;

    v_id_corregimiento := (v_direccion_trabajo->>'id_corregimiento')::INTEGER;

    SELECT d.id_provincia, c.id_distrito
      INTO v_id_provincia, v_id_distrito
      FROM corregimiento c
      JOIN distrito d ON d.id_distrito = c.id_distrito
     WHERE c.id_corregimiento = v_id_corregimiento;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'El corregimiento laboral % no existe',
            v_id_corregimiento;
    END IF;

    INSERT INTO direccion (
        apartado_postal,
        calle,
        edificio,
        numero_direccion,
        id_provincia,
        id_distrito,
        id_corregimiento
    )
    VALUES (
        NULLIF(BTRIM(v_direccion_trabajo->>'apartado_postal'), ''),
        NULLIF(BTRIM(v_direccion_trabajo->>'calle'), ''),
        NULLIF(BTRIM(v_direccion_trabajo->>'edificio'), ''),
        NULLIF(BTRIM(v_direccion_trabajo->>'numero_direccion'), ''),
        v_id_provincia,
        v_id_distrito,
        v_id_corregimiento
    )
    RETURNING id_direccion INTO v_id_direccion_trabajo;

    ----------------------------------------------------------------
    -- 7. Crear lugar de trabajo
    ----------------------------------------------------------------

    IF NULLIF(BTRIM(v_lugar_trabajo->>'empresa_institucion'), '') IS NULL
       OR NULLIF(BTRIM(v_lugar_trabajo->>'cargo'), '') IS NULL
       OR NULLIF(BTRIM(v_lugar_trabajo->>'telefono_trabajo'), '') IS NULL
       OR NULLIF(BTRIM(v_lugar_trabajo->>'email_laboral'), '') IS NULL THEN
        RAISE EXCEPTION 'Todos los campos del lugar de trabajo son obligatorios';
    END IF;

    INSERT INTO lugar_trabajo (
        id_medico,
        empresa_institucion,
        cargo,
        telefono_trabajo,
        email_laboral,
        id_direccion
    )
    VALUES (
        v_id_medico,
        BTRIM(v_lugar_trabajo->>'empresa_institucion'),
        BTRIM(v_lugar_trabajo->>'cargo'),
        BTRIM(v_lugar_trabajo->>'telefono_trabajo'),
        BTRIM(v_lugar_trabajo->>'email_laboral'),
        v_id_direccion_trabajo
    );

    ----------------------------------------------------------------
    -- 8. Crear estudio médico
    ----------------------------------------------------------------

    IF NULLIF(BTRIM(v_estudio->>'tipo_estudio'), '') IS NULL
       OR NULLIF(BTRIM(v_estudio->>'titulo'), '') IS NULL
       OR NULLIF(BTRIM(v_estudio->>'institucion'), '') IS NULL
       OR NULLIF(BTRIM(v_estudio->>'lugar'), '') IS NULL
       OR NULLIF(BTRIM(v_estudio->>'fecha'), '') IS NULL THEN
        RAISE EXCEPTION 'Todos los campos del estudio médico son obligatorios';
    END IF;

    INSERT INTO estudio_medico (
        id_medico,
        tipo_estudio,
        titulo,
        institucion,
        lugar,
        fecha
    )
    VALUES (
        v_id_medico,
        BTRIM(v_estudio->>'tipo_estudio'),
        BTRIM(v_estudio->>'titulo'),
        BTRIM(v_estudio->>'institucion'),
        BTRIM(v_estudio->>'lugar'),
        (v_estudio->>'fecha')::DATE
    );

    ----------------------------------------------------------------
    -- 9. Crear certificación
    ----------------------------------------------------------------

    IF v_certificacion->>'vigente' IS NULL
       OR NULLIF(BTRIM(v_certificacion->>'fecha_obtencion'), '') IS NULL
       OR NULLIF(BTRIM(v_certificacion->>'puntaje'), '') IS NULL
       OR NULLIF(BTRIM(v_certificacion->>'fecha_expiracion'), '') IS NULL THEN
        RAISE EXCEPTION 'Todos los campos de la certificación son obligatorios';
    END IF;

    IF jsonb_typeof(v_certificacion->'vigente') <> 'boolean' THEN
        RAISE EXCEPTION 'El campo vigente debe ser booleano';
    END IF;

    INSERT INTO certificacion (
        id_medico,
        vigente,
        fecha_obtencion,
        puntaje,
        fecha_expiracion
    )
    VALUES (
        v_id_medico,
        (v_certificacion->>'vigente')::BOOLEAN,
        (v_certificacion->>'fecha_obtencion')::DATE,
        (v_certificacion->>'puntaje')::INTEGER,
        (v_certificacion->>'fecha_expiracion')::DATE
    );

    ----------------------------------------------------------------
    -- 10. Validar secciones opcionales
    ----------------------------------------------------------------

    v_especialidades := COALESCE(
        NULLIF(p_datos->'especialidades', 'null'::JSONB),
        '[]'::JSONB
    );

    v_subespecialidades := COALESCE(
        NULLIF(p_datos->'subespecialidades', 'null'::JSONB),
        '[]'::JSONB
    );

    v_asociaciones := COALESCE(
        NULLIF(p_datos->'asociaciones', 'null'::JSONB),
        '[]'::JSONB
    );

    IF jsonb_typeof(v_especialidades) <> 'array'
       OR jsonb_typeof(v_subespecialidades) <> 'array'
       OR jsonb_typeof(v_asociaciones) <> 'array' THEN
        RAISE EXCEPTION 'Las especialidades, subespecialidades y asociaciones deben ser arrays';
    END IF;

    -- Validar que todos los elementos sean IDs enteros.
    FOR v_id IN
        SELECT value::INTEGER
        FROM jsonb_array_elements_text(v_especialidades)
    LOOP
        NULL;
    END LOOP;

    FOR v_id IN
        SELECT value::INTEGER
        FROM jsonb_array_elements_text(v_subespecialidades)
    LOOP
        NULL;
    END LOOP;

    FOR v_id IN
        SELECT value::INTEGER
        FROM jsonb_array_elements_text(v_asociaciones)
    LOOP
        NULL;
    END LOOP;

    SELECT COALESCE(array_agg(DISTINCT value::INTEGER), '{}')
      INTO v_ids_especialidad
      FROM jsonb_array_elements_text(v_especialidades);

    SELECT COALESCE(array_agg(DISTINCT value::INTEGER), '{}')
      INTO v_ids_subespecialidad
      FROM jsonb_array_elements_text(v_subespecialidades);

    SELECT COALESCE(array_agg(DISTINCT value::INTEGER), '{}')
      INTO v_ids_asociacion
      FROM jsonb_array_elements_text(v_asociaciones);

    ----------------------------------------------------------------
    -- 11. Validar especialidades existentes
    ----------------------------------------------------------------

    IF EXISTS (
        SELECT 1
        FROM unnest(v_ids_especialidad) AS x(id)
        WHERE NOT EXISTS (
            SELECT 1
            FROM especialidad e
            WHERE e.id_especialidad = x.id
        )
    ) THEN
        RAISE EXCEPTION 'Una o más especialidades no existen';
    END IF;

    ----------------------------------------------------------------
    -- 12. Validar subespecialidades y su especialidad
    ----------------------------------------------------------------

    IF cardinality(v_ids_subespecialidad) > 0
       AND cardinality(v_ids_especialidad) = 0 THEN
        RAISE EXCEPTION 'No se pueden registrar subespecialidades sin especialidades';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM unnest(v_ids_subespecialidad) AS x(id)
        WHERE NOT EXISTS (
            SELECT 1
            FROM subespecialidad s
            WHERE s.id_subespecialidad = x.id
              AND s.id_especialidad = ANY(v_ids_especialidad)
        )
    ) THEN
        RAISE EXCEPTION 'Una o más subespecialidades no existen o no corresponden a las especialidades seleccionadas';
    END IF;

    ----------------------------------------------------------------
    -- 13. Validar asociaciones existentes
    ----------------------------------------------------------------

    IF EXISTS (
        SELECT 1
        FROM unnest(v_ids_asociacion) AS x(id)
        WHERE NOT EXISTS (
            SELECT 1
            FROM asociacion a
            WHERE a.id_asociacion = x.id
        )
    ) THEN
        RAISE EXCEPTION 'Una o más asociaciones no existen';
    END IF;

    ----------------------------------------------------------------
    -- 14. Crear relaciones opcionales
    ----------------------------------------------------------------

    INSERT INTO medico_especialidad (
        id_medico,
        id_especialidad
    )
    SELECT v_id_medico, x.id
    FROM unnest(v_ids_especialidad) AS x(id);

    INSERT INTO medico_subespecialidad (
        id_medico,
        id_subespecialidad
    )
    SELECT v_id_medico, x.id
    FROM unnest(v_ids_subespecialidad) AS x(id);

    INSERT INTO medico_asociacion (
        id_medico,
        id_asociacion
    )
    SELECT v_id_medico, x.id
    FROM unnest(v_ids_asociacion) AS x(id);

    ----------------------------------------------------------------
    -- 15. Devolver ID del médico
    ----------------------------------------------------------------

    RETURN v_id_medico;

END;
$$;
