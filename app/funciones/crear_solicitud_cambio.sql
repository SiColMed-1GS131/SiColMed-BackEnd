CREATE OR REPLACE FUNCTION crear_solicitud_cambio(
    p_id_medico INTEGER,
    p_cambios JSONB
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_medico medico%ROWTYPE;
    v_usuario usuario%ROWTYPE;

    v_seccion TEXT;
    v_elemento JSONB;
    v_campo TEXT;
    v_id_registro INTEGER;
    v_id_campo TEXT;
    v_tabla TEXT;
    v_campos_permitidos TEXT[];
    v_fila JSONB;
    v_valor_nuevo JSONB;
    v_valor_anterior JSONB;
    v_objeto_normalizado JSONB;
    v_arreglo_normalizado JSONB;
    v_normalizado JSONB := '{}'::JSONB;

    v_agregar JSONB;
    v_quitar JSONB;
    v_valor_id JSONB;
    v_tabla_relacion TEXT;
    v_tabla_catalogo TEXT;
    v_columna_relacion TEXT;
    v_id_catalogo TEXT;
    v_existe BOOLEAN;

    v_id_solicitud INTEGER;
BEGIN
    -- Validar el identificador del medico.
    IF p_id_medico IS NULL OR p_id_medico < 1 THEN
        RAISE EXCEPTION 'El id_medico no es valido';
    END IF;

    -- Obtener el medico.
    SELECT *
      INTO v_medico
      FROM medico
     WHERE id_medico = p_id_medico;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'El medico % no existe', p_id_medico;
    END IF;

    -- Validar el JSON recibido.
    IF p_cambios IS NULL
       OR jsonb_typeof(p_cambios) IS DISTINCT FROM 'object'
       OR p_cambios = '{}'::JSONB THEN
        RAISE EXCEPTION
            'Los cambios deben ser un objeto JSON no vacio';
    END IF;

    -- Esta funcion no recibe cambios de medico ni direccion.
    IF p_cambios ? 'medico'
       OR p_cambios ? 'direccion' THEN
        RAISE EXCEPTION
            'Las secciones medico y direccion no admiten solicitudes de cambio';
    END IF;

    -- Validar las secciones permitidas.
    FOR v_seccion IN
        SELECT jsonb_object_keys(p_cambios)
    LOOP
        IF v_seccion NOT IN (
            'lugar_trabajo',
            'estudio_medico',
            'certificaciones',
            'especialidades',
            'subespecialidades',
            'asociaciones'
        ) THEN
            RAISE EXCEPTION
                'La seccion % no admite solicitudes de cambio',
                v_seccion;
        END IF;
    END LOOP;

    /*
     * Procesar los cambios de registros existentes.
     * El JSON de entrada contiene arreglos de objetos.
     * Cada objeto incluye su identificador y los campos nuevos.
     *
     * El JSON almacenado conserva el identificador y convierte
     * cada campo modificado en:
     * valor_anterior, valor_nuevo y estado.
     */
    FOREACH v_seccion IN ARRAY ARRAY[
        'lugar_trabajo',
        'estudio_medico',
        'certificaciones'
    ]
    LOOP
        IF p_cambios ? v_seccion THEN

            IF jsonb_typeof(p_cambios -> v_seccion)
               IS DISTINCT FROM 'array' THEN
                RAISE EXCEPTION
                    'La seccion % debe ser un arreglo',
                    v_seccion;
            END IF;

            v_arreglo_normalizado := '[]'::JSONB;

            IF v_seccion = 'lugar_trabajo' THEN
                v_tabla := 'lugar_trabajo';
                v_id_campo := 'id_lugar_trabajo';

                v_campos_permitidos := ARRAY[
                    'empresa_institucion',
                    'cargo',
                    'telefono_trabajo',
                    'email_laboral'
                ];

            ELSIF v_seccion = 'estudio_medico' THEN
                v_tabla := 'estudio_medico';
                v_id_campo := 'id_estudio';

                v_campos_permitidos := ARRAY[
                    'tipo_estudio',
                    'titulo',
                    'institucion',
                    'lugar',
                    'fecha'
                ];

            ELSE
                v_tabla := 'certificacion';
                v_id_campo := 'id_certificacion';

                v_campos_permitidos := ARRAY[
                    'vigente',
                    'fecha_obtencion',
                    'puntaje',
                    'fecha_expiracion'
                ];
            END IF;

            -- Procesar cada registro enviado.
            FOR v_elemento IN
                SELECT value
                  FROM jsonb_array_elements(
                      p_cambios -> v_seccion
                  )
            LOOP
                -- Validar el objeto y su identificador.
                IF jsonb_typeof(v_elemento)
                       IS DISTINCT FROM 'object'
                   OR NOT (v_elemento ? v_id_campo)
                   OR jsonb_typeof(v_elemento -> v_id_campo)
                       IS DISTINCT FROM 'number'
                   OR (v_elemento ->> v_id_campo)
                       !~ '^[1-9][0-9]*$' THEN
                    RAISE EXCEPTION
                        'Cada elemento de % debe ser un objeto con identificador entero positivo en %',
                        v_seccion,
                        v_id_campo;
                END IF;

                v_id_registro :=
                    (v_elemento ->> v_id_campo)::INTEGER;

                /*
                 * Obtener el registro y verificar que pertenezca
                 * al medico indicado.
                 */
                EXECUTE format(
                    'SELECT to_jsonb(t)
                       FROM %I t
                      WHERE %I = $1
                        AND id_medico = $2',
                    v_tabla,
                    v_id_campo
                )
                INTO v_fila
                USING v_id_registro, p_id_medico;

                IF v_fila IS NULL THEN
                    RAISE EXCEPTION
                        'El registro % con identificador % no existe o no pertenece al medico %',
                        v_seccion,
                        v_id_registro,
                        p_id_medico;
                END IF;

                -- Conservar el identificador en el JSON resultante.
                v_objeto_normalizado :=
                    jsonb_build_object(
                        v_id_campo,
                        v_id_registro
                    );

                -- Procesar los campos enviados para ese registro.
                FOR v_campo IN
                    SELECT jsonb_object_keys(v_elemento)
                LOOP
                    -- El identificador no es un campo modificable.
                    IF v_campo = v_id_campo THEN
                        CONTINUE;
                    END IF;

                    -- Validar la lista blanca de campos.
                    IF NOT (
                        v_campo = ANY(v_campos_permitidos)
                    ) THEN
                        RAISE EXCEPTION
                            'Campo % no permitido en %',
                            v_campo,
                            v_seccion;
                    END IF;

                    v_valor_nuevo :=
                        v_elemento -> v_campo;

                    v_valor_anterior :=
                        v_fila -> v_campo;

                    -- No permitir solicitar un valor que ya existe.
                    IF v_valor_nuevo IS NOT DISTINCT FROM
                       v_valor_anterior THEN
                        RAISE EXCEPTION
                            'El campo % del registro % ya tiene ese valor',
                            v_campo,
                            v_id_registro;
                    END IF;

                    -- Formatear el cambio para su revisión posterior.
                    v_objeto_normalizado :=
                        v_objeto_normalizado ||
                        jsonb_build_object(
                            v_campo,
                            jsonb_build_object(
                                'valor_anterior',
                                v_valor_anterior,
                                'valor_nuevo',
                                v_valor_nuevo,
                                'estado',
                                'PENDIENTE'
                            )
                        );
                END LOOP;

                -- Rechazar objetos que solo contienen el identificador.
                IF v_objeto_normalizado =
                   jsonb_build_object(
                       v_id_campo,
                       v_id_registro
                   ) THEN
                    RAISE EXCEPTION
                        'El registro % no contiene campos para solicitar cambios',
                        v_id_registro;
                END IF;

                v_arreglo_normalizado :=
                    v_arreglo_normalizado ||
                    jsonb_build_array(v_objeto_normalizado);
            END LOOP;

            IF jsonb_array_length(v_arreglo_normalizado) = 0 THEN
                RAISE EXCEPTION
                    'La seccion % no contiene cambios',
                    v_seccion;
            END IF;

            v_normalizado :=
                v_normalizado ||
                jsonb_build_object(
                    v_seccion,
                    v_arreglo_normalizado
                );
        END IF;
    END LOOP;

    /*
     * Procesar las relaciones:
     * especialidades, subespecialidades y asociaciones.
     *
     * Estas operaciones se guardan como pendientes; no se ejecutan
     * directamente en las tablas de relaciones.
     */
    FOREACH v_seccion IN ARRAY ARRAY[
        'especialidades',
        'subespecialidades',
        'asociaciones'
    ]
    LOOP
        IF p_cambios ? v_seccion THEN

            IF jsonb_typeof(p_cambios -> v_seccion)
                   IS DISTINCT FROM 'object'
               OR NOT (
                   (p_cambios -> v_seccion) ? 'agregar'
               )
               OR NOT (
                   (p_cambios -> v_seccion) ? 'quitar'
               )
               OR jsonb_typeof(
                   p_cambios -> v_seccion -> 'agregar'
               ) IS DISTINCT FROM 'array'
               OR jsonb_typeof(
                   p_cambios -> v_seccion -> 'quitar'
               ) IS DISTINCT FROM 'array'
               OR (
                   (p_cambios -> v_seccion)
                   - 'agregar'
                   - 'quitar'
               ) <> '{}'::JSONB THEN
                RAISE EXCEPTION
                    'La relacion % debe contener solamente arreglos agregar y quitar',
                    v_seccion;
            END IF;

            v_agregar :=
                p_cambios -> v_seccion -> 'agregar';

            v_quitar :=
                p_cambios -> v_seccion -> 'quitar';

            IF jsonb_array_length(v_agregar) = 0
               AND jsonb_array_length(v_quitar) = 0 THEN
                RAISE EXCEPTION
                    'La relacion % no contiene operaciones',
                    v_seccion;
            END IF;

            -- No permitir agregar y quitar el mismo identificador.
            IF EXISTS (
                SELECT 1
                  FROM jsonb_array_elements(v_agregar) a(value)
                  JOIN jsonb_array_elements(v_quitar) q(value)
                    ON a.value = q.value
            ) THEN
                RAISE EXCEPTION
                    'La relacion % no puede agregar y quitar el mismo identificador',
                    v_seccion;
            END IF;

            -- Determinar las tablas y columnas de la relacion.
            IF v_seccion = 'especialidades' THEN
                v_tabla_relacion := 'medico_especialidad';
                v_tabla_catalogo := 'especialidad';
                v_columna_relacion := 'id_especialidad';
                v_id_catalogo := 'id_especialidad';

            ELSIF v_seccion = 'subespecialidades' THEN
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

            -- Validar que los identificadores sean enteros positivos.
            FOR v_valor_id IN
                SELECT value
                  FROM jsonb_array_elements(v_agregar)

                UNION ALL

                SELECT value
                  FROM jsonb_array_elements(v_quitar)
            LOOP
                IF jsonb_typeof(v_valor_id)
                       IS DISTINCT FROM 'number'
                   OR v_valor_id::TEXT
                       !~ '^[1-9][0-9]*$' THEN
                    RAISE EXCEPTION
                        'La relacion % contiene un identificador invalido',
                        v_seccion;
                END IF;
            END LOOP;

            -- Comprobar que los elementos que se agregan existan.
            FOR v_valor_id IN
                SELECT value
                  FROM jsonb_array_elements(v_agregar)
            LOOP
                EXECUTE format(
                    'SELECT EXISTS (
                        SELECT 1
                          FROM %I
                         WHERE %I = $1
                    )',
                    v_tabla_catalogo,
                    v_id_catalogo
                )
                INTO v_existe
                USING (v_valor_id #>> '{}')::INTEGER;

                IF NOT v_existe THEN
                    RAISE EXCEPTION
                        'El identificador % no existe en %',
                        v_valor_id #>> '{}',
                        v_tabla_catalogo;
                END IF;
            END LOOP;

            -- Comprobar que los elementos que se quitan
            -- estén actualmente asignados al medico.
            FOR v_valor_id IN
                SELECT value
                  FROM jsonb_array_elements(v_quitar)
            LOOP
                EXECUTE format(
                    'SELECT EXISTS (
                        SELECT 1
                          FROM %I
                         WHERE id_medico = $1
                           AND %I = $2
                    )',
                    v_tabla_relacion,
                    v_columna_relacion
                )
                INTO v_existe
                USING
                    p_id_medico,
                    (v_valor_id #>> '{}')::INTEGER;

                IF NOT v_existe THEN
                    RAISE EXCEPTION
                        'La relacion % con identificador % no pertenece al medico',
                        v_seccion,
                        v_valor_id #>> '{}';
                END IF;
            END LOOP;

            -- Guardar las operaciones pendientes.
            v_normalizado :=
                v_normalizado ||
                jsonb_build_object(
                    v_seccion,
                    jsonb_build_object(
                        'agregar', v_agregar,
                        'quitar', v_quitar,
                        'estado', 'PENDIENTE'
                    )
                );
        END IF;
    END LOOP;

    IF v_normalizado = '{}'::JSONB THEN
        RAISE EXCEPTION
            'No se encontraron cambios para solicitar';
    END IF;

    /*
     * Crear la solicitud de cambio.
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
     * Auditoria:
     * registrar unicamente la creacion de la solicitud
     * y su identificador.
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
                'SOLICITUD_CAMBIO',
                v_id_solicitud,
                now(),
                'Se creo la solicitud de cambio '
                    || v_id_solicitud
            );
        END IF;
    END IF;

    RETURN v_id_solicitud;
END;
$$;