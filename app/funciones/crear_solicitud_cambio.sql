CREATE OR REPLACE FUNCTION crear_solicitud_cambio(
    p_id_medico INTEGER,
    p_cambios JSONB
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    -- Campos que nunca deben modificarse mediante una solicitud.
    v_no_permitidos TEXT[] := ARRAY[]::TEXT[];

    -- Los datos personales se actualizan directamente.
    v_personales TEXT[] := ARRAY[
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

    v_medico medico%ROWTYPE;
    v_usuario usuario%ROWTYPE;

    v_campo TEXT;
    v_cambio JSONB;
    v_partes TEXT[];
    v_tabla TEXT;
    v_id_registro INTEGER;
    v_nombre_campo TEXT;
    v_id_columna TEXT;
    v_fila JSONB;
    v_valor_nuevo JSONB;
    v_valor_anterior JSONB;
    v_normalizado JSONB := '{}'::JSONB;
    v_agregar JSONB;
    v_quitar JSONB;
    v_id INTEGER;
    v_id_catalogo TEXT;
    v_tabla_relacion TEXT;
    v_tabla_catalogo TEXT;
    v_columna_relacion TEXT;
    v_id_relacion INTEGER;
    v_hay_operacion BOOLEAN;
    v_id_solicitud INTEGER;
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
       OR p_cambios = '{}'::JSONB THEN
        RAISE EXCEPTION
            'Los cambios deben ser un objeto JSON no vacio';
    END IF;

    /*
     * Procesar cada cambio solicitado.
     */
    FOR v_campo, v_cambio IN
        SELECT key, value
          FROM jsonb_each(p_cambios)
    LOOP
        /*
         * Relaciones: especialidades, subespecialidades
         * y asociaciones.
         */
        IF v_campo IN (
            'especialidades',
            'subespecialidades',
            'asociaciones'
        ) THEN
            IF jsonb_typeof(v_cambio) <> 'object'
               OR NOT (v_cambio ? 'agregar')
               OR NOT (v_cambio ? 'quitar')
               OR jsonb_typeof(v_cambio -> 'agregar')
                    <> 'array'
               OR jsonb_typeof(v_cambio -> 'quitar')
                    <> 'array'
               OR (v_cambio - 'agregar' - 'quitar')
                    <> '{}'::JSONB THEN
                RAISE EXCEPTION
                    'La relacion % debe contener arreglos agregar y quitar',
                    v_campo;
            END IF;

            v_agregar := v_cambio -> 'agregar';
            v_quitar := v_cambio -> 'quitar';

            IF jsonb_array_length(v_agregar) = 0
               AND jsonb_array_length(v_quitar) = 0 THEN
                RAISE EXCEPTION
                    'La relacion % no contiene operaciones',
                    v_campo;
            END IF;

            IF EXISTS (
                SELECT 1
                  FROM jsonb_array_elements(v_agregar) a(value)
                  JOIN jsonb_array_elements(v_quitar) q(value)
                    ON a.value = q.value
            ) THEN
                RAISE EXCEPTION
                    'La relacion % no puede agregar y quitar el mismo identificador',
                    v_campo;
            END IF;

            IF v_campo = 'especialidades' THEN
                v_tabla_relacion := 'medico_especialidad';
                v_tabla_catalogo := 'especialidad';
                v_columna_relacion := 'id_especialidad';
                v_id_catalogo := 'id_especialidad';
            ELSIF v_campo = 'subespecialidades' THEN
                v_tabla_relacion := 'medico_subespecialidad';
                v_tabla_catalogo := 'subespecialidad';
                v_columna_relacion := 'id_subespecialidad';
                v_id_catalogo := 'id_subespecialidad';
            ELSE
                v_tabla_relacion := 'medico_asociacion';
                v_tabla_catalogo := 'asociacion';
                v_columna_relacion := 'id_asociacion';
                v_id_catalogo := 'id_asociacion';
            END IF;

            -- Validar que todos los identificadores sean enteros positivos.
            FOR v_valor_nuevo IN
                SELECT value
                  FROM jsonb_array_elements(v_agregar)
                UNION ALL
                SELECT value
                  FROM jsonb_array_elements(v_quitar)
            LOOP
                IF jsonb_typeof(v_valor_nuevo) <> 'number'
                   OR v_valor_nuevo::TEXT !~ '^[1-9][0-9]*$' THEN
                    RAISE EXCEPTION
                        'La relacion % contiene un identificador invalido',
                        v_campo;
                END IF;
            END LOOP;

            -- Comprobar que los elementos que se agregan existan.
            FOR v_valor_nuevo IN
                SELECT value
                  FROM jsonb_array_elements(v_agregar)
            LOOP
                EXECUTE format(
                    'SELECT EXISTS (
                        SELECT 1 FROM %I WHERE %I = $1
                    )',
                    v_tabla_catalogo,
                    v_id_catalogo
                )
                INTO v_hay_operacion
                USING (v_valor_nuevo #>> '{}')::INTEGER;

                IF NOT v_hay_operacion THEN
                    RAISE EXCEPTION
                        'El identificador % no existe en %',
                        v_valor_nuevo #>> '{}',
                        v_tabla_catalogo;
                END IF;
            END LOOP;

            -- Comprobar que las relaciones que se quitan estén asignadas.
            FOR v_valor_nuevo IN
                SELECT value
                  FROM jsonb_array_elements(v_quitar)
            LOOP
                EXECUTE format(
                    'SELECT EXISTS (
                        SELECT 1 FROM %I
                         WHERE id_medico = $1
                           AND %I = $2
                    )',
                    v_tabla_relacion,
                    v_columna_relacion
                )
                INTO v_hay_operacion
                USING p_id_medico,
                      (v_valor_nuevo #>> '{}')::INTEGER;

                IF NOT v_hay_operacion THEN
                    RAISE EXCEPTION
                        'La relacion % con identificador % no pertenece al medico',
                        v_campo,
                        v_valor_nuevo #>> '{}';
                END IF;
            END LOOP;

            -- Guardar las operaciones sin ejecutarlas.
            v_normalizado := v_normalizado ||
                jsonb_build_object(
                    v_campo,
                    jsonb_build_object(
                        'agregar', v_agregar,
                        'quitar', v_quitar,
                        'estado', 'PENDIENTE'
                    )
                );

        ELSE
            /*
             * Cambios individuales:
             * tabla:id_registro:campo
             */
            IF array_length(string_to_array(v_campo, ':'), 1) <> 3 THEN
                RAISE EXCEPTION
                    'Formato invalido para %. Use tabla:id_registro:campo',
                    v_campo;
            END IF;

            v_partes := string_to_array(v_campo, ':');
            v_tabla := v_partes[1];
            v_nombre_campo := v_partes[3];

            IF v_partes[2] !~ '^[1-9][0-9]*$' THEN
                RAISE EXCEPTION
                    'Identificador invalido en %',
                    v_campo;
            END IF;

            v_id_registro := v_partes[2]::INTEGER;

            IF v_tabla NOT IN (
                'medico',
                'direccion',
                'lugar_trabajo',
                'estudio_medico',
                'certificacion'
            ) THEN
                RAISE EXCEPTION
                    'La tabla % no admite solicitudes',
                    v_tabla;
            END IF;

            IF v_nombre_campo = ANY(v_no_permitidos) THEN
                RAISE EXCEPTION
                    'El campo % esta prohibido',
                    v_nombre_campo;
            END IF;

            IF v_tabla = 'medico'
               AND v_nombre_campo = ANY(v_personales) THEN
                RAISE EXCEPTION
                    'El campo personal % debe actualizarse directamente',
                    v_nombre_campo;
            END IF;

            /*
             * Identificar la clave primaria y comprobar que
             * el campo exista y no sea una clave o FK.
             */
            SELECT a.attname
              INTO v_id_columna
              FROM pg_index i
              JOIN pg_attribute a
                ON a.attrelid = i.indrelid
               AND a.attnum = ANY(i.indkey)
             WHERE i.indrelid = to_regclass(v_tabla)
               AND i.indisprimary
             LIMIT 1;

            IF v_id_columna IS NULL THEN
                RAISE EXCEPTION
                    'No se pudo identificar la clave primaria de %',
                    v_tabla;
            END IF;

            IF NOT EXISTS (
                SELECT 1
                  FROM pg_attribute a
                 WHERE a.attrelid = to_regclass(v_tabla)
                   AND a.attname = v_nombre_campo
                   AND a.attnum > 0
                   AND NOT a.attisdropped
            ) THEN
                RAISE EXCEPTION
                    'El campo % no existe en %',
                    v_nombre_campo,
                    v_tabla;
            END IF;

            IF EXISTS (
                SELECT 1
                  FROM pg_constraint c
                  JOIN pg_attribute a
                    ON a.attrelid = c.conrelid
                   AND a.attnum = ANY(c.conkey)
                 WHERE c.conrelid = to_regclass(v_tabla)
                   AND c.contype IN ('p', 'f', 'u')
                   AND a.attname = v_nombre_campo
                   -- Permitir las FK geograficas solo en direccion.
                   AND NOT (
                       v_tabla = 'direccion'
                       AND a.attname IN (
                           'id_provincia',
                           'id_distrito',
                           'id_corregimiento'
                       )
                   )
            ) THEN
                RAISE EXCEPTION
                    'El campo % es una clave y no admite solicitudes',
                    v_nombre_campo;
            END IF;

            -- Bloquear identificadores del registro y propietario.
            IF v_nombre_campo IN (
                'id_usuario',
                'id_medico',
                'id_direccion'
            ) THEN
                RAISE EXCEPTION
                    'El campo % no puede cambiarse mediante solicitud',
                    v_nombre_campo;
            END IF;

            IF v_tabla <> 'direccion'
               AND v_nombre_campo IN (
                   'id_provincia',
                   'id_distrito',
                   'id_corregimiento'
               ) THEN
                RAISE EXCEPTION
                    'El campo % no puede cambiarse mediante solicitud en la tabla %',
                    v_nombre_campo,
                    v_tabla;
            END IF;

            /*
             * Verificar que el registro pertenezca al médico.
             */
            IF v_tabla = 'medico' THEN
                IF v_id_registro <> p_id_medico THEN
                    RAISE EXCEPTION
                        'No puede solicitar cambios para otro medico';
                END IF;

                SELECT to_jsonb(m)
                  INTO v_fila
                  FROM medico m
                 WHERE m.id_medico = p_id_medico;

            ELSIF v_tabla = 'direccion' THEN
                SELECT to_jsonb(d)
                  INTO v_fila
                  FROM direccion d
                 WHERE d.id_direccion = v_id_registro
                   AND (
                       d.id_direccion = v_medico.id_direccion
                       OR EXISTS (
                           SELECT 1
                             FROM lugar_trabajo lt
                            WHERE lt.id_direccion = d.id_direccion
                              AND lt.id_medico = p_id_medico
                       )
                   );

            ELSIF v_tabla = 'lugar_trabajo' THEN
                SELECT to_jsonb(lt)
                  INTO v_fila
                  FROM lugar_trabajo lt
                 WHERE lt.id_lugar_trabajo = v_id_registro
                   AND lt.id_medico = p_id_medico;

            ELSIF v_tabla = 'estudio_medico' THEN
                SELECT to_jsonb(e)
                  INTO v_fila
                  FROM estudio_medico e
                 WHERE e.id_estudio = v_id_registro
                   AND e.id_medico = p_id_medico;

            ELSE
                SELECT to_jsonb(c)
                  INTO v_fila
                  FROM certificacion c
                 WHERE c.id_certificacion = v_id_registro
                   AND c.id_medico = p_id_medico;
            END IF;

            IF v_fila IS NULL THEN
                RAISE EXCEPTION
                    'El registro % no existe o no pertenece al medico %',
                    v_id_registro,
                    p_id_medico;
            END IF;

            v_valor_nuevo := v_cambio -> 'valor_nuevo';

            IF v_valor_nuevo IS NULL
               OR jsonb_typeof(v_cambio) <> 'object'
               OR (v_cambio - 'valor_nuevo') <> '{}'::JSONB THEN
                RAISE EXCEPTION
                    'El campo % debe contener solamente valor_nuevo',
                    v_campo;
            END IF;

            v_valor_anterior := v_fila -> v_nombre_campo;

            IF v_valor_nuevo IS NOT DISTINCT FROM v_valor_anterior THEN
                RAISE EXCEPTION
                    'El campo % ya tiene ese valor',
                    v_campo;
            END IF;

            v_normalizado := v_normalizado ||
                jsonb_build_object(
                    v_campo,
                    jsonb_build_object(
                        'valor_anterior', v_valor_anterior,
                        'valor_nuevo', v_valor_nuevo,
                        'estado', 'PENDIENTE'
                    )
                );
        END IF;
    END LOOP;

    /*
     * Crear la solicitud.
     */
    INSERT INTO solicitud_cambio (
        id_usuario,
        id_medico,
        estado,
        fecha_solicitud,
        cambios
    )
    VALUES (
        v_medico.id_usuario,
        p_id_medico,
        'PENDIENTE',
        now(),
        v_normalizado
    )
    RETURNING id_solicitud_cambio
         INTO v_id_solicitud;

    /*
     * Registrar auditoría si el médico tiene usuario asociado.
     */
    IF v_medico.id_usuario IS NOT NULL THEN
        SELECT *
          INTO v_usuario
          FROM usuario
         WHERE id_usuario = v_medico.id_usuario;

        IF FOUND THEN
            INSERT INTO auditoria (
                id_usuario,
                id_rol,
                accion,
                entidad,
                id_registro,
                fecha_hora,
                descripcion
            )
            VALUES (
                v_usuario.id_usuario,
                v_usuario.id_rol,
                'CREAR_SOLICITUD_CAMBIO',
                'MEDICO',
                p_id_medico,
                now(),
                'Solicitud de cambio '
                    || v_id_solicitud
                    || ' creada'
            );
        END IF;
    END IF;

    RETURN v_id_solicitud;
END;
$$;