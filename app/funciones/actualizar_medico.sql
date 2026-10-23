CREATE OR REPLACE FUNCTION actualizar_medico(
    p_id_medico INTEGER,
    p_id_administrador INTEGER,
    p_datos JSONB
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_rol TEXT;
    v_medico medico%ROWTYPE;
    v_datos_medico JSONB;
    v_datos_dir JSONB;
    v_elemento JSONB;
    v_campo TEXT;
    v_id INTEGER;
    v_id_direccion INTEGER;
    v_id_corregimiento INTEGER;
    v_id_distrito INTEGER;
    v_id_provincia INTEGER;
    v_hay_cambios BOOLEAN := FALSE;
    v_campos_personales TEXT[] := ARRAY[
        'primer_nombre',
        'segundo_nombre',
        'apellido_paterno',
        'apellido_materno',
        'foto',
        'fecha_nacimiento',
        'telefono_residencial',
        'celular',
        'email_personal'
    ];
    v_campos_medico_admin TEXT[] := ARRAY[
        'numero_idoneidad',
        'numero_registro_medico',
        'cedula',
        'primer_nombre',
        'segundo_nombre',
        'apellido_paterno',
        'apellido_materno',
        'foto',
        'fecha_nacimiento',
        'telefono_residencial',
        'celular',
        'email_personal'
    ];
    v_campos_direccion TEXT[] := ARRAY[
        'apartado_postal',
        'calle',
        'edificio',
        'numero_direccion',
        'id_corregimiento'
    ];
    v_campos_trabajo TEXT[] := ARRAY[
        'empresa_institucion',
        'cargo',
        'telefono_trabajo',
        'email_laboral'
    ];
    v_campos_estudio TEXT[] := ARRAY[
        'tipo_estudio',
        'titulo',
        'institucion',
        'lugar',
        'fecha'
    ];
    v_campos_certificacion TEXT[] := ARRAY[
        'vigente',
        'fecha_obtencion',
        'puntaje',
        'fecha_expiracion'
    ];
BEGIN
    -- 1. Validaciones generales.
    IF p_id_medico IS NULL OR p_id_medico < 1 THEN
        RAISE EXCEPTION 'El id_medico no es valido';
    END IF;

    IF p_id_administrador IS NULL OR p_id_administrador < 1 THEN
        RAISE EXCEPTION 'El id del usuario actor no es valido';
    END IF;

    IF p_datos IS NULL
       OR jsonb_typeof(p_datos) IS DISTINCT FROM 'object'
       OR p_datos = '{}'::JSONB THEN
        RAISE EXCEPTION 'p_datos debe ser un objeto JSON no vacio';
    END IF;

    -- 2. El actor debe existir, estar activo y tener un rol permitido.
    SELECT LOWER(BTRIM(r.nombre))
    INTO v_rol
    FROM usuario u
    JOIN rol r ON r.id_rol = u.id_rol
    WHERE u.id_usuario = p_id_administrador
      AND u.activo = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'El usuario actor no existe o esta inactivo';
    END IF;

    IF v_rol NOT IN ('medico', 'admin_cmp') THEN
        RAISE EXCEPTION 'El usuario no tiene permisos para actualizar medicos';
    END IF;

    -- 3. Validar la estructura superior del JSON.
    FOR v_campo IN
        SELECT jsonb_object_keys(p_datos)
    LOOP
        IF NOT (v_campo = ANY(ARRAY[
            'medico',
            'direccion',
            'lugar_trabajo',
            'estudio_medico',
            'especialidades',
            'subespecialidades',
            'asociaciones',
            'certificaciones'
        ])) THEN
            RAISE EXCEPTION 'Seccion JSON desconocida: %', v_campo;
        END IF;
    END LOOP;

    IF v_rol = 'medico'
       AND (
           p_datos ?| ARRAY[
               'direccion',
               'lugar_trabajo',
               'estudio_medico',
               'especialidades',
               'subespecialidades',
               'asociaciones',
               'certificaciones'
           ]
       ) THEN
        RAISE EXCEPTION
            'El medico solo puede modificar sus nueve campos personales';
    END IF;

    IF NOT (p_datos ? 'medico')
       AND v_rol = 'medico' THEN
        RAISE EXCEPTION 'Debe enviar la seccion medico';
    END IF;

    -- 4. Bloquear y obtener el médico.
    SELECT *
    INTO v_medico
    FROM medico
    WHERE id_medico = p_id_medico
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'El medico % no existe', p_id_medico;
    END IF;

    -- Un médico solo puede modificar su propio perfil.
    IF v_rol = 'medico' THEN
        IF v_medico.id_usuario IS DISTINCT FROM p_id_administrador THEN
            RAISE EXCEPTION
                'Un medico solo puede modificar su propio perfil';
        END IF;

        -- Comprobar también que la cuenta asociada al perfil esté activa.
        IF NOT EXISTS (
            SELECT 1
            FROM usuario u
            WHERE u.id_usuario = v_medico.id_usuario
              AND u.activo = TRUE
        ) THEN
            RAISE EXCEPTION 'La cuenta del medico esta inactiva';
        END IF;
    END IF;

    -- 5. Validar y actualizar los campos de MEDICO.
    IF p_datos ? 'medico' THEN
        v_datos_medico := p_datos -> 'medico';

        IF jsonb_typeof(v_datos_medico) IS DISTINCT FROM 'object'
           OR v_datos_medico = '{}'::JSONB THEN
            RAISE EXCEPTION '"medico" debe ser un objeto JSON no vacio';
        END IF;

        FOR v_campo IN
            SELECT jsonb_object_keys(v_datos_medico)
        LOOP
            IF v_rol = 'medico'
               AND NOT (v_campo = ANY(v_campos_personales)) THEN
                RAISE EXCEPTION
                    'El campo "%" no esta permitido para el medico',
                    v_campo;
            END IF;

            IF v_rol = 'admin_cmp'
               AND NOT (v_campo = ANY(v_campos_medico_admin)) THEN
                RAISE EXCEPTION
                    'Campo de MEDICO no reconocido o no editable: %',
                    v_campo;
            END IF;

            IF jsonb_typeof(v_datos_medico -> v_campo) = 'string'
               AND BTRIM(v_datos_medico ->> v_campo) = '' THEN
                RAISE EXCEPTION 'El campo "%" no puede estar vacio', v_campo;
            END IF;
        END LOOP;

        -- Campos críticos: si se envían, no pueden quedar vacíos.
        IF v_rol = 'admin_cmp' THEN
            FOREACH v_campo IN ARRAY ARRAY[
                'numero_idoneidad',
                'numero_registro_medico',
                'cedula',
                'primer_nombre',
                'apellido_paterno',
                'fecha_nacimiento'
            ]
            LOOP
                IF v_datos_medico ? v_campo
                   AND (
                       v_datos_medico -> v_campo = 'null'::JSONB
                       OR BTRIM(COALESCE(
                           v_datos_medico ->> v_campo, ''
                       )) = ''
                   ) THEN
                    RAISE EXCEPTION
                        'El campo "%" no puede ser nulo ni vacio',
                        v_campo;
                END IF;
            END LOOP;
        END IF;

        -- Validar correo personal.
        IF v_datos_medico ? 'email_personal'
           AND v_datos_medico -> 'email_personal' <> 'null'::JSONB
           AND (v_datos_medico ->> 'email_personal')
               !~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$' THEN
            RAISE EXCEPTION 'El correo personal no tiene un formato valido';
        END IF;

        -- Validar fecha de nacimiento.
        IF v_datos_medico ? 'fecha_nacimiento'
           AND v_datos_medico -> 'fecha_nacimiento' <> 'null'::JSONB THEN
            BEGIN
                IF (v_datos_medico ->> 'fecha_nacimiento')::DATE
                   > CURRENT_DATE THEN
                    RAISE EXCEPTION
                        'La fecha de nacimiento no puede ser futura';
                END IF;
            EXCEPTION
                WHEN invalid_datetime_format OR datetime_field_overflow THEN
                    RAISE EXCEPTION
                        'La fecha de nacimiento no tiene formato valido';
            END;
        END IF;

        -- Validar unicidad de identificadores administrativos.
        IF v_rol = 'admin_cmp' THEN
            IF v_datos_medico ? 'numero_idoneidad'
               AND EXISTS (
                   SELECT 1 FROM medico m
                   WHERE m.numero_idoneidad =
                         v_datos_medico ->> 'numero_idoneidad'
                     AND m.id_medico <> p_id_medico
               ) THEN
                RAISE EXCEPTION 'El numero de idoneidad ya esta registrado';
            END IF;

            IF v_datos_medico ? 'numero_registro_medico'
               AND EXISTS (
                   SELECT 1 FROM medico m
                   WHERE m.numero_registro_medico =
                         v_datos_medico ->> 'numero_registro_medico'
                     AND m.id_medico <> p_id_medico
               ) THEN
                RAISE EXCEPTION
                    'El numero de registro medico ya esta registrado';
            END IF;

            IF v_datos_medico ? 'cedula'
               AND EXISTS (
                   SELECT 1 FROM medico m
                   WHERE m.cedula = v_datos_medico ->> 'cedula'
                     AND m.id_medico <> p_id_medico
               ) THEN
                RAISE EXCEPTION 'La cedula ya esta registrada';
            END IF;
        END IF;

        -- Aplicar solo las columnas enviadas.
        FOR v_campo IN
            SELECT jsonb_object_keys(v_datos_medico)
        LOOP
            EXECUTE FORMAT(
                'UPDATE medico SET %I = ($1).%I
                 WHERE id_medico = $2',
                v_campo, v_campo
            )
            USING
                jsonb_populate_record(NULL::medico, v_datos_medico),
                p_id_medico;

            v_hay_cambios := TRUE;
        END LOOP;
    END IF;

    -- Desde este punto, solo admin_cmp puede modificar relaciones.
    IF v_rol = 'admin_cmp' THEN

        -- 6. DIRECCION: modificar la dirección residencial existente.
        IF p_datos ? 'direccion' THEN
            v_datos_dir := p_datos -> 'direccion';

            IF jsonb_typeof(v_datos_dir) IS DISTINCT FROM 'object'
               OR v_datos_dir = '{}'::JSONB THEN
                RAISE EXCEPTION
                    '"direccion" debe ser un objeto JSON no vacio';
            END IF;

            FOR v_campo IN
                SELECT jsonb_object_keys(v_datos_dir)
            LOOP
                IF NOT (v_campo = ANY(v_campos_direccion)) THEN
                    RAISE EXCEPTION
                        'Campo de direccion desconocido: %', v_campo;
                END IF;
            END LOOP;

            v_id_direccion := v_medico.id_direccion;

            PERFORM 1
            FROM direccion
            WHERE id_direccion = v_id_direccion
            FOR UPDATE;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'No se encontro la direccion del medico';
            END IF;

            IF v_datos_dir ? 'id_corregimiento' THEN
                IF v_datos_dir -> 'id_corregimiento' = 'null'::JSONB THEN
                    RAISE EXCEPTION 'El corregimiento no puede ser nulo';
                END IF;

                v_id_corregimiento :=
                    (v_datos_dir ->> 'id_corregimiento')::INTEGER;

                SELECT c.id_distrito, d.id_provincia
                INTO v_id_distrito, v_id_provincia
                FROM corregimiento c
                JOIN distrito d ON d.id_distrito = c.id_distrito
                WHERE c.id_corregimiento = v_id_corregimiento;

                IF NOT FOUND THEN
                    RAISE EXCEPTION 'El corregimiento no existe';
                END IF;
            END IF;

            FOREACH v_campo IN ARRAY ARRAY[
                'apartado_postal', 'calle', 'edificio', 'numero_direccion'
            ]
            LOOP
                IF v_datos_dir ? v_campo
                   AND v_datos_dir -> v_campo <> 'null'::JSONB
                   AND BTRIM(v_datos_dir ->> v_campo) = '' THEN
                    RAISE EXCEPTION
                        'El campo de direccion "%" no puede estar vacio',
                        v_campo;
                END IF;
            END LOOP;

            UPDATE direccion
            SET
                apartado_postal = CASE
                    WHEN v_datos_dir ? 'apartado_postal'
                    THEN v_datos_dir ->> 'apartado_postal'
                    ELSE apartado_postal END,
                calle = CASE
                    WHEN v_datos_dir ? 'calle'
                    THEN v_datos_dir ->> 'calle'
                    ELSE calle END,
                edificio = CASE
                    WHEN v_datos_dir ? 'edificio'
                    THEN v_datos_dir ->> 'edificio'
                    ELSE edificio END,
                numero_direccion = CASE
                    WHEN v_datos_dir ? 'numero_direccion'
                    THEN v_datos_dir ->> 'numero_direccion'
                    ELSE numero_direccion END,
                id_corregimiento = CASE
                    WHEN v_datos_dir ? 'id_corregimiento'
                    THEN v_id_corregimiento
                    ELSE id_corregimiento END,
                id_distrito = CASE
                    WHEN v_datos_dir ? 'id_corregimiento'
                    THEN v_id_distrito ELSE id_distrito END,
                id_provincia = CASE
                    WHEN v_datos_dir ? 'id_corregimiento'
                    THEN v_id_provincia ELSE id_provincia END
            WHERE id_direccion = v_id_direccion;

            v_hay_cambios := TRUE;
        END IF;

        -- 7. LUGAR_TRABAJO: actualizar registros existentes.
        IF p_datos ? 'lugar_trabajo' THEN
            IF jsonb_typeof(p_datos -> 'lugar_trabajo')
               IS DISTINCT FROM 'array' THEN
                RAISE EXCEPTION '"lugar_trabajo" debe ser un arreglo';
            END IF;

            FOR v_elemento IN
                SELECT value
                FROM jsonb_array_elements(p_datos -> 'lugar_trabajo')
            LOOP
                IF jsonb_typeof(v_elemento) IS DISTINCT FROM 'object'
                   OR NOT (v_elemento ? 'id_lugar_trabajo') THEN
                    RAISE EXCEPTION
                        'Cada lugar de trabajo debe incluir id_lugar_trabajo';
                END IF;

                v_id := (v_elemento ->> 'id_lugar_trabajo')::INTEGER;

                FOR v_campo IN SELECT jsonb_object_keys(v_elemento)
                LOOP
                    IF v_campo <> 'id_lugar_trabajo'
                       AND NOT (v_campo = ANY(v_campos_trabajo)) THEN
                        RAISE EXCEPTION
                            'Campo de lugar_trabajo no permitido: %', v_campo;
                    END IF;
                END LOOP;

                UPDATE lugar_trabajo
                SET
                    empresa_institucion = CASE
                        WHEN v_elemento ? 'empresa_institucion'
                        THEN v_elemento ->> 'empresa_institucion'
                        ELSE empresa_institucion END,
                    cargo = CASE
                        WHEN v_elemento ? 'cargo'
                        THEN v_elemento ->> 'cargo'
                        ELSE cargo END,
                    telefono_trabajo = CASE
                        WHEN v_elemento ? 'telefono_trabajo'
                        THEN v_elemento ->> 'telefono_trabajo'
                        ELSE telefono_trabajo END,
                    email_laboral = CASE
                        WHEN v_elemento ? 'email_laboral'
                        THEN v_elemento ->> 'email_laboral'
                        ELSE email_laboral END
                WHERE id_lugar_trabajo = v_id
                  AND id_medico = p_id_medico;

                IF NOT FOUND THEN
                    RAISE EXCEPTION
                        'El lugar de trabajo % no pertenece al medico %',
                        v_id, p_id_medico;
                END IF;

                v_hay_cambios := TRUE;
            END LOOP;
        END IF;

        -- 8. ESTUDIO_MEDICO: actualizar estudios existentes.
        IF p_datos ? 'estudio_medico' THEN
            IF jsonb_typeof(p_datos -> 'estudio_medico')
               IS DISTINCT FROM 'array' THEN
                RAISE EXCEPTION '"estudio_medico" debe ser un arreglo';
            END IF;

            FOR v_elemento IN
                SELECT value
                FROM jsonb_array_elements(p_datos -> 'estudio_medico')
            LOOP
                IF jsonb_typeof(v_elemento) IS DISTINCT FROM 'object'
                   OR NOT (v_elemento ? 'id_estudio') THEN
                    RAISE EXCEPTION 'Cada estudio debe incluir id_estudio';
                END IF;

                v_id := (v_elemento ->> 'id_estudio')::INTEGER;

                FOR v_campo IN SELECT jsonb_object_keys(v_elemento)
                LOOP
                    IF v_campo <> 'id_estudio'
                       AND NOT (v_campo = ANY(v_campos_estudio)) THEN
                        RAISE EXCEPTION
                            'Campo de estudio_medico no permitido: %',
                            v_campo;
                    END IF;
                END LOOP;

                UPDATE estudio_medico
                SET
                    tipo_estudio = CASE WHEN v_elemento ? 'tipo_estudio'
                        THEN v_elemento ->> 'tipo_estudio'
                        ELSE tipo_estudio END,
                    titulo = CASE WHEN v_elemento ? 'titulo'
                        THEN v_elemento ->> 'titulo' ELSE titulo END,
                    institucion = CASE WHEN v_elemento ? 'institucion'
                        THEN v_elemento ->> 'institucion' ELSE institucion END,
                    lugar = CASE WHEN v_elemento ? 'lugar'
                        THEN v_elemento ->> 'lugar' ELSE lugar END,
                    fecha = CASE WHEN v_elemento ? 'fecha'
                        THEN (v_elemento ->> 'fecha')::DATE ELSE fecha END
                WHERE id_estudio = v_id
                  AND id_medico = p_id_medico;

                IF NOT FOUND THEN
                    RAISE EXCEPTION
                        'El estudio % no pertenece al medico %',
                        v_id, p_id_medico;
                END IF;

                v_hay_cambios := TRUE;
            END LOOP;
        END IF;

        -- 9. CERTIFICACIONES: actualizar registros existentes.
        IF p_datos ? 'certificaciones' THEN
            IF jsonb_typeof(p_datos -> 'certificaciones')
               IS DISTINCT FROM 'array' THEN
                RAISE EXCEPTION '"certificaciones" debe ser un arreglo';
            END IF;

            FOR v_elemento IN
                SELECT value
                FROM jsonb_array_elements(p_datos -> 'certificaciones')
            LOOP
                IF jsonb_typeof(v_elemento) IS DISTINCT FROM 'object'
                   OR NOT (v_elemento ? 'id_certificacion') THEN
                    RAISE EXCEPTION
                        'Cada certificacion debe incluir id_certificacion';
                END IF;

                v_id := (v_elemento ->> 'id_certificacion')::INTEGER;

                FOR v_campo IN SELECT jsonb_object_keys(v_elemento)
                LOOP
                    IF v_campo <> 'id_certificacion'
                       AND NOT (v_campo = ANY(v_campos_certificacion)) THEN
                        RAISE EXCEPTION
                            'Campo de certificacion no permitido: %', v_campo;
                    END IF;
                END LOOP;

                UPDATE certificacion
                SET
                    vigente = CASE WHEN v_elemento ? 'vigente'
                        THEN (v_elemento ->> 'vigente')::BOOLEAN
                        ELSE vigente END,
                    fecha_obtencion = CASE
                        WHEN v_elemento ? 'fecha_obtencion'
                        THEN (v_elemento ->> 'fecha_obtencion')::DATE
                        ELSE fecha_obtencion END,
                    puntaje = CASE WHEN v_elemento ? 'puntaje'
                        THEN (v_elemento ->> 'puntaje')::INTEGER
                        ELSE puntaje END,
                    fecha_expiracion = CASE
                        WHEN v_elemento ? 'fecha_expiracion'
                        THEN (v_elemento ->> 'fecha_expiracion')::DATE
                        ELSE fecha_expiracion END
                WHERE id_certificacion = v_id
                  AND id_medico = p_id_medico;

                IF NOT FOUND THEN
                    RAISE EXCEPTION
                        'La certificacion % no pertenece al medico %',
                        v_id, p_id_medico;
                END IF;

                v_hay_cambios := TRUE;
            END LOOP;
        END IF;

        -- 10. ESPECIALIDADES: agregar y quitar relaciones.
        IF p_datos ? 'especialidades' THEN
            IF jsonb_typeof(p_datos -> 'especialidades') IS DISTINCT FROM 'object'
               OR NOT (p_datos -> 'especialidades' ? 'agregar')
               OR NOT (p_datos -> 'especialidades' ? 'quitar')
               OR (p_datos -> 'especialidades') - 'agregar' - 'quitar' <> '{}'::JSONB THEN
                RAISE EXCEPTION
                    '"especialidades" debe contener solamente "agregar" y "quitar"';
            END IF;

            IF jsonb_typeof(p_datos -> 'especialidades' -> 'agregar')
                   IS DISTINCT FROM 'array'
               OR jsonb_typeof(p_datos -> 'especialidades' -> 'quitar')
                   IS DISTINCT FROM 'array' THEN
                RAISE EXCEPTION
                    '"agregar" y "quitar" en "especialidades" deben ser arreglos';
            END IF;

            -- Agregar relaciones.
            FOR v_elemento IN
                SELECT value
                FROM jsonb_array_elements(p_datos -> 'especialidades' -> 'agregar')
            LOOP
                IF jsonb_typeof(v_elemento) IS DISTINCT FROM 'number'
                   OR (v_elemento #>> '{}') !~ '^[0-9]+$' THEN
                    RAISE EXCEPTION 'Cada especialidad debe ser un ID entero positivo';
                END IF;

                v_id := (v_elemento #>> '{}')::INTEGER;

                IF v_id < 1 OR NOT EXISTS (
                    SELECT 1 FROM especialidad
                    WHERE id_especialidad = v_id
                ) THEN
                    RAISE EXCEPTION 'La especialidad % no existe o no es valida', v_id;
                END IF;

                INSERT INTO medico_especialidad (id_medico, id_especialidad)
                SELECT p_id_medico, v_id
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM medico_especialidad
                    WHERE id_medico = p_id_medico
                      AND id_especialidad = v_id
                );

                IF FOUND THEN
                    v_hay_cambios := TRUE;
                END IF;
            END LOOP;

            -- Quitar relaciones existentes de este médico.
            FOR v_elemento IN
                SELECT value
                FROM jsonb_array_elements(p_datos -> 'especialidades' -> 'quitar')
            LOOP
                IF jsonb_typeof(v_elemento) IS DISTINCT FROM 'number'
                   OR (v_elemento #>> '{}') !~ '^[0-9]+$' THEN
                    RAISE EXCEPTION 'Cada especialidad a quitar debe ser un ID entero positivo';
                END IF;

                v_id := (v_elemento #>> '{}')::INTEGER;

                DELETE FROM medico_especialidad
                WHERE id_medico = p_id_medico
                  AND id_especialidad = v_id;

                IF FOUND THEN
                    v_hay_cambios := TRUE;
                ELSE
                    RAISE EXCEPTION
                        'La especialidad % no está asignada al médico %',
                        v_id, p_id_medico;
                END IF;
            END LOOP;
        END IF;

        -- 11. SUBESPECIALIDADES: agregar y quitar relaciones.
        IF p_datos ? 'subespecialidades' THEN
            IF jsonb_typeof(p_datos -> 'subespecialidades') IS DISTINCT FROM 'object'
               OR NOT (p_datos -> 'subespecialidades' ? 'agregar')
               OR NOT (p_datos -> 'subespecialidades' ? 'quitar')
               OR (p_datos -> 'subespecialidades') - 'agregar' - 'quitar' <> '{}'::JSONB THEN
                RAISE EXCEPTION
                    '"subespecialidades" debe contener solamente "agregar" y "quitar"';
            END IF;

            IF jsonb_typeof(p_datos -> 'subespecialidades' -> 'agregar')
                   IS DISTINCT FROM 'array'
               OR jsonb_typeof(p_datos -> 'subespecialidades' -> 'quitar')
                   IS DISTINCT FROM 'array' THEN
                RAISE EXCEPTION
                    '"agregar" y "quitar" en "subespecialidades" deben ser arreglos';
            END IF;

            FOR v_elemento IN
                SELECT value
                FROM jsonb_array_elements(p_datos -> 'subespecialidades' -> 'agregar')
            LOOP
                IF jsonb_typeof(v_elemento) IS DISTINCT FROM 'number'
                   OR (v_elemento #>> '{}') !~ '^[0-9]+$' THEN
                    RAISE EXCEPTION 'Cada subespecialidad debe ser un ID entero positivo';
                END IF;

                v_id := (v_elemento #>> '{}')::INTEGER;

                IF v_id < 1 OR NOT EXISTS (
                    SELECT 1 FROM subespecialidad
                    WHERE id_subespecialidad = v_id
                ) THEN
                    RAISE EXCEPTION 'La subespecialidad % no existe o no es valida', v_id;
                END IF;

                INSERT INTO medico_subespecialidad (id_medico, id_subespecialidad)
                SELECT p_id_medico, v_id
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM medico_subespecialidad
                    WHERE id_medico = p_id_medico
                      AND id_subespecialidad = v_id
                );

                IF FOUND THEN
                    v_hay_cambios := TRUE;
                END IF;
            END LOOP;

            FOR v_elemento IN
                SELECT value
                FROM jsonb_array_elements(p_datos -> 'subespecialidades' -> 'quitar')
            LOOP
                IF jsonb_typeof(v_elemento) IS DISTINCT FROM 'number'
                   OR (v_elemento #>> '{}') !~ '^[0-9]+$' THEN
                    RAISE EXCEPTION 'Cada subespecialidad a quitar debe ser un ID entero positivo';
                END IF;

                v_id := (v_elemento #>> '{}')::INTEGER;

                DELETE FROM medico_subespecialidad
                WHERE id_medico = p_id_medico
                  AND id_subespecialidad = v_id;

                IF FOUND THEN
                    v_hay_cambios := TRUE;
                ELSE
                    RAISE EXCEPTION
                        'La subespecialidad % no está asignada al médico %',
                        v_id, p_id_medico;
                END IF;
            END LOOP;
        END IF;

        -- 12. ASOCIACIONES: agregar y quitar relaciones.
        IF p_datos ? 'asociaciones' THEN
            IF jsonb_typeof(p_datos -> 'asociaciones') IS DISTINCT FROM 'object'
               OR NOT (p_datos -> 'asociaciones' ? 'agregar')
               OR NOT (p_datos -> 'asociaciones' ? 'quitar')
               OR (p_datos -> 'asociaciones') - 'agregar' - 'quitar' <> '{}'::JSONB THEN
                RAISE EXCEPTION
                    '"asociaciones" debe contener solamente "agregar" y "quitar"';
            END IF;

            IF jsonb_typeof(p_datos -> 'asociaciones' -> 'agregar')
                   IS DISTINCT FROM 'array'
               OR jsonb_typeof(p_datos -> 'asociaciones' -> 'quitar')
                   IS DISTINCT FROM 'array' THEN
                RAISE EXCEPTION
                    '"agregar" y "quitar" en "asociaciones" deben ser arreglos';
            END IF;

            FOR v_elemento IN
                SELECT value
                FROM jsonb_array_elements(p_datos -> 'asociaciones' -> 'agregar')
            LOOP
                IF jsonb_typeof(v_elemento) IS DISTINCT FROM 'number'
                   OR (v_elemento #>> '{}') !~ '^[0-9]+$' THEN
                    RAISE EXCEPTION 'Cada asociación debe ser un ID entero positivo';
                END IF;

                v_id := (v_elemento #>> '{}')::INTEGER;

                IF v_id < 1 OR NOT EXISTS (
                    SELECT 1 FROM asociacion
                    WHERE id_asociacion = v_id
                ) THEN
                    RAISE EXCEPTION 'La asociación % no existe o no es válida', v_id;
                END IF;

                INSERT INTO medico_asociacion (id_medico, id_asociacion)
                SELECT p_id_medico, v_id
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM medico_asociacion
                    WHERE id_medico = p_id_medico
                      AND id_asociacion = v_id
                );

                IF FOUND THEN
                    v_hay_cambios := TRUE;
                END IF;
            END LOOP;

            FOR v_elemento IN
                SELECT value
                FROM jsonb_array_elements(p_datos -> 'asociaciones' -> 'quitar')
            LOOP
                IF jsonb_typeof(v_elemento) IS DISTINCT FROM 'number'
                   OR (v_elemento #>> '{}') !~ '^[0-9]+$' THEN
                    RAISE EXCEPTION 'Cada asociación a quitar debe ser un ID entero positivo';
                END IF;

                v_id := (v_elemento #>> '{}')::INTEGER;

                DELETE FROM medico_asociacion
                WHERE id_medico = p_id_medico
                  AND id_asociacion = v_id;

                IF FOUND THEN
                    v_hay_cambios := TRUE;
                ELSE
                    RAISE EXCEPTION
                        'La asociación % no está asignada al médico %',
                        v_id, p_id_medico;
                END IF;
            END LOOP;
        END IF;
    END IF;

    -- 13. No aceptar una operación que no haya producido cambios.
    IF NOT v_hay_cambios THEN
        RAISE EXCEPTION 'No se aplico ningun cambio';
    END IF;

    -- 14. Registrar auditoría.
    INSERT INTO auditoria (
        id_usuario,
        id_rol,
        accion,
        entidad,
        id_registro,
        fecha_hora,
        descripcion
    )
    SELECT
        u.id_usuario,
        u.id_rol,
        'ACTUALIZAR_MEDICO',
        'MEDICO',
        p_id_medico,
        CURRENT_TIMESTAMP,
        'Actualizacion de datos del medico'
    FROM usuario u
    WHERE u.id_usuario = p_id_administrador;

    RETURN TRUE;
END;
$$;
