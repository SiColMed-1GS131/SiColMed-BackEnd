
CREATE OR REPLACE FUNCTION procesar_solicitud_cambio(
    p_id_solicitud_cambio integer,
    p_id_administrador    integer,
    p_decisiones          jsonb,
    p_comentario          text DEFAULT NULL
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
DECLARE
    v_permitidos text[] := ARRAY[
        'primer_nombre',
        'segundo_nombre',
        'apellido_paterno',
        'apellido_materno',
        'telefono_residencial',
        'celular',
        'email_personal',
        'foto'
    ];

    v_permitidos_estudio text[] := ARRAY[
        'tipo_estudio',
        'titulo',
        'institucion',
        'lugar',
        'fecha'
    ];

    v_sol           solicitud_cambio%ROWTYPE;
    v_cambios       jsonb;
    v_campo         text;
    v_decision      jsonb;
    v_resultado     text;
    v_pendientes    boolean;
    v_id_estudio    integer;
    v_campo_estudio text;
    v_actual        jsonb;
BEGIN
    -- Validar que el usuario sea un administrador activo.
    IF NOT EXISTS (
        SELECT 1
          FROM usuario u
          JOIN rol r ON r.id_rol = u.id_rol
         WHERE u.id_usuario = p_id_administrador
           AND u.activo = true
           AND r.nombre = 'admin_cmp'
    ) THEN
        RAISE EXCEPTION
            'El usuario % no existe, esta inactivo o no es administrador',
            p_id_administrador;
    END IF;

    -- Bloquear la solicitud mientras se procesa.
    SELECT *
      INTO v_sol
      FROM solicitud_cambio
     WHERE id_solicitud_cambio = p_id_solicitud_cambio
       FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'La solicitud % no existe',
            p_id_solicitud_cambio;
    END IF;

    IF v_sol.estado = 'PROCESADO' THEN
        RAISE EXCEPTION
            'La solicitud % ya fue procesada',
            p_id_solicitud_cambio;
    END IF;

    IF p_decisiones IS NULL
       OR jsonb_typeof(p_decisiones) <> 'object'
       OR p_decisiones = '{}'::jsonb THEN
        RAISE EXCEPTION
            'Las decisiones deben ser un objeto JSON con al menos un campo';
    END IF;

    v_cambios := v_sol.cambios;

    FOR v_campo, v_decision IN
        SELECT key, value
          FROM jsonb_each(p_decisiones)
    LOOP
        IF NOT (v_cambios ? v_campo) THEN
            RAISE EXCEPTION
                'El campo % no forma parte de la solicitud',
                v_campo;
        END IF;

        IF v_cambios -> v_campo ->> 'estado'
           IS DISTINCT FROM 'PENDIENTE' THEN
            RAISE EXCEPTION
                'El campo % ya fue resuelto',
                v_campo;
        END IF;

        IF jsonb_typeof(v_decision) <> 'object' THEN
            RAISE EXCEPTION
                'La decision para % debe ser un objeto JSON',
                v_campo;
        END IF;

        v_resultado := v_decision ->> 'estado';

        IF v_resultado NOT IN ('APROBADO', 'RECHAZADO')
           OR v_resultado IS NULL THEN
            RAISE EXCEPTION
                'La decision para % debe ser APROBADO o RECHAZADO',
                v_campo;
        END IF;

        IF v_resultado = 'APROBADO' THEN

            -- Actualizar datos personales en medico.
            IF v_campo = ANY(v_permitidos) THEN

                SELECT to_jsonb(m)
                  INTO v_actual
                  FROM medico m
                 WHERE m.id_medico = v_sol.id_medico;

                IF NOT FOUND THEN
                    RAISE EXCEPTION
                        'El medico % ya no existe',
                        v_sol.id_medico;
                END IF;

                -- Evitar sobrescribir cambios realizados desde la solicitud.
                IF (v_actual -> v_campo)
                   IS DISTINCT FROM
                   (v_cambios -> v_campo -> 'valor_anterior') THEN
                    RAISE EXCEPTION
                        'El campo % cambio desde que se creo la solicitud',
                        v_campo;
                END IF;

                EXECUTE format(
                    'UPDATE medico SET %I = $1 WHERE id_medico = $2',
                    v_campo
                )
                USING
                    v_cambios -> v_campo ->> 'valor_nuevo',
                    v_sol.id_medico;

            -- Actualizar un campo de estudio_medico.
            ELSIF split_part(v_campo, ':', 1) = 'estudio_medico' THEN

                IF split_part(v_campo, ':', 2) !~ '^[0-9]+$'
                   OR split_part(v_campo, ':', 3) = ''
                   OR split_part(v_campo, ':', 4) <> '' THEN
                    RAISE EXCEPTION
                        'Formato incorrecto para el campo %',
                        v_campo;
                END IF;

                v_id_estudio :=
                    split_part(v_campo, ':', 2)::integer;

                v_campo_estudio :=
                    split_part(v_campo, ':', 3);

                IF NOT (
                    v_campo_estudio = ANY(v_permitidos_estudio)
                ) THEN
                    RAISE EXCEPTION
                        'El campo academico % no se puede modificar',
                        v_campo_estudio;
                END IF;

                SELECT to_jsonb(e)
                  INTO v_actual
                  FROM estudio_medico e
                 WHERE e.id_estudio = v_id_estudio
                   AND e.id_medico = v_sol.id_medico;

                IF NOT FOUND THEN
                    RAISE EXCEPTION
                        'El estudio % no existe o no pertenece al medico %',
                        v_id_estudio, v_sol.id_medico;
                END IF;

                IF (v_actual -> v_campo_estudio)
                   IS DISTINCT FROM
                   (v_cambios -> v_campo -> 'valor_anterior') THEN
                    RAISE EXCEPTION
                        'El campo academico % cambio desde que se creo la solicitud',
                        v_campo_estudio;
                END IF;

                -- La fecha requiere conversion al tipo DATE.
                IF v_campo_estudio = 'fecha' THEN
                    EXECUTE
                        'UPDATE estudio_medico
                            SET fecha = $1::date
                          WHERE id_estudio = $2
                            AND id_medico = $3'
                    USING
                        v_cambios -> v_campo ->> 'valor_nuevo',
                        v_id_estudio,
                        v_sol.id_medico;
                ELSE
                    EXECUTE format(
                        'UPDATE estudio_medico SET %I = $1
                          WHERE id_estudio = $2
                            AND id_medico = $3',
                        v_campo_estudio
                    )
                    USING
                        v_cambios -> v_campo ->> 'valor_nuevo',
                        v_id_estudio,
                        v_sol.id_medico;
                END IF;

            ELSE
                RAISE EXCEPTION
                    'El campo % no esta permitido',
                    v_campo;
            END IF;
        END IF;

        -- Registrar la decision individual.
        v_cambios := jsonb_set(
            v_cambios,
            ARRAY[v_campo, 'estado'],
            to_jsonb(v_resultado)
        );
    END LOOP;

    -- La solicitud sigue pendiente si queda algun campo sin resolver.
    SELECT EXISTS (
        SELECT 1
          FROM jsonb_each(v_cambios) e
         WHERE e.value ->> 'estado' = 'PENDIENTE'
    )
    INTO v_pendientes;

    UPDATE solicitud_cambio
       SET cambios = v_cambios,
           id_usuario = p_id_administrador,
           comentario = COALESCE(p_comentario, comentario),
           estado = CASE
               WHEN v_pendientes THEN 'PENDIENTE'
               ELSE 'PROCESADO'
           END,
           fecha_respuesta = CASE
               WHEN v_pendientes THEN NULL
               ELSE now()
           END
     WHERE id_solicitud_cambio = p_id_solicitud_cambio;

    -- Registrar la operacion en auditoria.
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
        'PROCESAR_SOLICITUD_CAMBIO',
        'MEDICO',
        v_sol.id_medico,
        now(),
        'Solicitud ' || p_id_solicitud_cambio ||
        ' revisada. Estado: ' ||
        CASE
            WHEN v_pendientes THEN 'PENDIENTE'
            ELSE 'PROCESADO'
        END
    FROM usuario u
    WHERE u.id_usuario = p_id_administrador;

    RETURN true;
END;
$$;
