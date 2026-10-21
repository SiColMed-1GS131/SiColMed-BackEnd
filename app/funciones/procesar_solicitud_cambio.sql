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
    -- Debe coincidir con crear_solicitud_cambio (CONFIRMAR con el equipo).
    v_permitidos text[] := ARRAY['telefono_residencial', 'celular', 'email_personal', 'foto'];
    v_sol        solicitud_cambio%ROWTYPE;
    v_cambios    jsonb;
    v_campo      text;
    v_decision   jsonb;
    v_resultado  text;
    v_pendientes boolean;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM usuario WHERE id_usuario = p_id_administrador AND activo) THEN
        RAISE EXCEPTION 'El administrador % no existe o está inactivo', p_id_administrador;
    END IF;

    SELECT * INTO v_sol
      FROM solicitud_cambio
     WHERE id_solicitud_cambio = p_id_solicitud_cambio
       FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'La solicitud % no existe', p_id_solicitud_cambio;
    END IF;
    IF v_sol.estado = 'PROCESADO' THEN
        RAISE EXCEPTION 'La solicitud % ya fue procesada', p_id_solicitud_cambio;
    END IF;

    IF p_decisiones IS NULL OR jsonb_typeof(p_decisiones) <> 'object' OR p_decisiones = '{}'::jsonb THEN
        RAISE EXCEPTION 'Las decisiones deben ser un objeto JSON con al menos un campo';
    END IF;

    v_cambios := v_sol.cambios;

    -- Entrada: {"celular": {"estado": "APROBADO"}, "foto": {"estado": "RECHAZADO"}}
    FOR v_campo, v_decision IN SELECT key, value FROM jsonb_each(p_decisiones) LOOP
        IF NOT (v_cambios ? v_campo) THEN
            RAISE EXCEPTION 'El campo % no forma parte de la solicitud', v_campo;
        END IF;
        IF (v_cambios -> v_campo ->> 'estado') <> 'PENDIENTE' THEN
            RAISE EXCEPTION 'El campo % ya fue resuelto', v_campo;
        END IF;

        v_resultado := CASE WHEN jsonb_typeof(v_decision) = 'object'
                            THEN v_decision ->> 'estado' END;
        IF v_resultado IS NULL OR v_resultado NOT IN ('APROBADO', 'RECHAZADO') THEN
            RAISE EXCEPTION 'La decisión para % debe ser APROBADO o RECHAZADO', v_campo;
        END IF;

        IF v_resultado = 'APROBADO' THEN
            IF NOT (v_campo = ANY (v_permitidos)) THEN
                RAISE EXCEPTION 'El campo % no es editable por el médico', v_campo;
            END IF;
            EXECUTE format('UPDATE medico SET %I = $1 WHERE id_medico = $2', v_campo)
              USING (v_cambios -> v_campo ->> 'valor_nuevo'), v_sol.id_medico;
        END IF;

        v_cambios := jsonb_set(v_cambios, ARRAY[v_campo, 'estado'], to_jsonb(v_resultado));
    END LOOP;

    SELECT EXISTS (SELECT 1 FROM jsonb_each(v_cambios) e WHERE e.value ->> 'estado' = 'PENDIENTE')
      INTO v_pendientes;

    UPDATE solicitud_cambio
       SET cambios         = v_cambios,
           id_usuario      = p_id_administrador,
           comentario      = coalesce(p_comentario, comentario),
           estado          = CASE WHEN v_pendientes THEN 'PENDIENTE' ELSE 'PROCESADO' END,
           fecha_respuesta = CASE WHEN v_pendientes THEN NULL ELSE now() END
     WHERE id_solicitud_cambio = p_id_solicitud_cambio;

    INSERT INTO auditoria (id_usuario, id_rol, accion, entidad, id_registro, fecha_hora, descripcion)
    SELECT u.id_usuario, u.id_rol, 'PROCESAR_SOLICITUD_CAMBIO', 'MEDICO', v_sol.id_medico, now(),
           'Solicitud de cambio ' || p_id_solicitud_cambio || ' revisada'
      FROM usuario u
     WHERE u.id_usuario = p_id_administrador;

    RETURN true;
END;
$$;