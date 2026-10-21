CREATE OR REPLACE FUNCTION crear_solicitud_cambio(
    p_id_medico integer,
    p_cambios   jsonb
)
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    -- Campos que el médico puede pedir cambiar (CONFIRMAR con el equipo y la sección 2.3).
    v_permitidos  text[] := ARRAY['telefono_residencial', 'celular', 'email_personal', 'foto'];
    v_medico      medico%ROWTYPE;
    v_actual      jsonb;
    v_normalizado jsonb := '{}'::jsonb;
    v_campo       text;
    v_cambio      jsonb;
    v_id          integer;
BEGIN
    SELECT * INTO v_medico FROM medico WHERE id_medico = p_id_medico;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'El médico % no existe', p_id_medico;
    END IF;

    IF p_cambios IS NULL OR jsonb_typeof(p_cambios) <> 'object' OR p_cambios = '{}'::jsonb THEN
        RAISE EXCEPTION 'Los cambios deben ser un objeto JSON con al menos un campo';
    END IF;

    v_actual := to_jsonb(v_medico);

    -- Entrada: {"celular": {"valor_nuevo": "6000-2222"}, ...}
    -- Se guarda: {"celular": {"valor_anterior": ..., "valor_nuevo": ..., "estado": "PENDIENTE"}}
    FOR v_campo, v_cambio IN SELECT key, value FROM jsonb_each(p_cambios) LOOP
        IF NOT (v_campo = ANY (v_permitidos)) THEN
            RAISE EXCEPTION 'El campo % no puede modificarse mediante solicitud', v_campo;
        END IF;
        IF jsonb_typeof(v_cambio) <> 'object'
           OR jsonb_typeof(v_cambio -> 'valor_nuevo') IS DISTINCT FROM 'string' THEN
            RAISE EXCEPTION 'El campo % debe incluir valor_nuevo como texto', v_campo;
        END IF;
        IF (v_cambio -> 'valor_nuevo') = (v_actual -> v_campo) THEN
            RAISE EXCEPTION 'El campo % ya tiene ese valor', v_campo;
        END IF;

        v_normalizado := v_normalizado || jsonb_build_object(
            v_campo, jsonb_build_object(
                'valor_anterior', v_actual -> v_campo,
                'valor_nuevo',    v_cambio -> 'valor_nuevo',
                'estado',         'PENDIENTE'));
    END LOOP;

    INSERT INTO solicitud_cambio (id_medico, estado, fecha_solicitud, cambios)
    VALUES (p_id_medico, 'PENDIENTE', now(), v_normalizado)
    RETURNING id_solicitud_cambio INTO v_id;

    -- Auditoría: solo si el médico ya tiene cuenta.
    INSERT INTO auditoria (id_usuario, id_rol, accion, entidad, id_registro, fecha_hora, descripcion)
    SELECT u.id_usuario, u.id_rol, 'CREAR_SOLICITUD_CAMBIO', 'MEDICO', p_id_medico, now(),
           'Solicitud de cambio ' || v_id || ' creada'
      FROM usuario u
     WHERE u.id_usuario = v_medico.id_usuario;

    RETURN v_id;
END;
$$;