
CREATE OR REPLACE FUNCTION crear_solicitud_cambio(
    p_id_medico integer,
    p_cambios   jsonb
)
RETURNS integer
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

    v_medico        medico%ROWTYPE;
    v_estudio       estudio_medico%ROWTYPE;
    v_actual        jsonb;
    v_normalizado   jsonb := '{}'::jsonb;
    v_campo         text;
    v_cambio        jsonb;
    v_id_estudio    integer;
    v_campo_estudio text;
    v_id            integer;
BEGIN
    SELECT *
      INTO v_medico
      FROM medico
     WHERE id_medico = p_id_medico;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'El medico % no existe', p_id_medico;
    END IF;

    IF p_cambios IS NULL
       OR jsonb_typeof(p_cambios) <> 'object'
       OR p_cambios = '{}'::jsonb THEN
        RAISE EXCEPTION
            'Los cambios deben ser un objeto JSON con al menos un campo';
    END IF;

    FOR v_campo, v_cambio IN
        SELECT key, value
          FROM jsonb_each(p_cambios)
    LOOP
        IF jsonb_typeof(v_cambio) <> 'object'
           OR jsonb_typeof(v_cambio -> 'valor_nuevo')
              IS DISTINCT FROM 'string' THEN
            RAISE EXCEPTION
                'El campo % debe incluir valor_nuevo como texto',
                v_campo;
        END IF;

        -- Cambios en los datos personales del medico.
        IF v_campo = ANY(v_permitidos) THEN
            v_actual := to_jsonb(v_medico);

            IF (v_cambio -> 'valor_nuevo')
               IS NOT DISTINCT FROM (v_actual -> v_campo) THEN
                RAISE EXCEPTION
                    'El campo % ya tiene ese valor', v_campo;
            END IF;

            v_normalizado := v_normalizado ||
                jsonb_build_object(
                    v_campo,
                    jsonb_build_object(
                        'valor_anterior', v_actual -> v_campo,
                        'valor_nuevo', v_cambio -> 'valor_nuevo',
                        'estado', 'PENDIENTE'
                    )
                );

        -- Cambios en un estudio academico existente.
        ELSIF split_part(v_campo, ':', 1) = 'estudio_medico' THEN
            IF split_part(v_campo, ':', 2) !~ '^[0-9]+$'
               OR split_part(v_campo, ':', 3) = ''
               OR split_part(v_campo, ':', 4) <> '' THEN
                RAISE EXCEPTION
                    'Formato incorrecto para el campo %', v_campo;
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

            SELECT *
              INTO v_estudio
              FROM estudio_medico
             WHERE id_estudio = v_id_estudio
               AND id_medico = p_id_medico;

            IF NOT FOUND THEN
                RAISE EXCEPTION
                    'El estudio % no existe o no pertenece al medico %',
                    v_id_estudio, p_id_medico;
            END IF;

            v_actual := to_jsonb(v_estudio);

            IF (v_cambio -> 'valor_nuevo')
               IS NOT DISTINCT FROM (v_actual -> v_campo_estudio) THEN
                RAISE EXCEPTION
                    'El campo academico % ya tiene ese valor',
                    v_campo_estudio;
            END IF;

            v_normalizado := v_normalizado ||
                jsonb_build_object(
                    v_campo,
                    jsonb_build_object(
                        'valor_anterior', v_actual -> v_campo_estudio,
                        'valor_nuevo', v_cambio -> 'valor_nuevo',
                        'estado', 'PENDIENTE'
                    )
                );

        ELSE
            RAISE EXCEPTION
                'El campo % no se puede modificar mediante solicitud',
                v_campo;
        END IF;
    END LOOP;

    INSERT INTO solicitud_cambio (
        id_medico,
        estado,
        fecha_solicitud,
        cambios
    )
    VALUES (
        p_id_medico,
        'PENDIENTE',
        now(),
        v_normalizado
    )
    RETURNING id_solicitud_cambio INTO v_id;

    -- Auditoria de la solicitud, si el medico tiene una cuenta.
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
        'CREAR_SOLICITUD_CAMBIO',
        'MEDICO',
        p_id_medico,
        now(),
        'Solicitud de cambio ' || v_id || ' creada'
    FROM usuario u
    WHERE u.id_usuario = v_medico.id_usuario;

    RETURN v_id;
END;
$$;
