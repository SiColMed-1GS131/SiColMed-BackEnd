
CREATE OR REPLACE FUNCTION procesar_solicitud_cambio(
    p_id_solicitud_cambio INTEGER,
    p_id_administrador INTEGER,
    p_decisiones JSONB,
    p_comentario TEXT DEFAULT NULL
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_sol solicitud_cambio%ROWTYPE;
    v_usuario usuario%ROWTYPE;
    v_cambios JSONB;

    v_seccion TEXT;
    v_decision JSONB;
    v_resultado TEXT;

    v_elemento JSONB;
    v_campo TEXT;
    v_indice INTEGER;
    v_id_registro INTEGER;
    v_id_campo TEXT;
    v_tabla TEXT;
    v_nombre_campo TEXT;
    v_campos_permitidos TEXT[];

    v_actual JSONB;
    v_anterior JSONB;
    v_nuevo JSONB;
    v_tipo_columna TEXT;
    v_id_columna TEXT;

    v_agregar JSONB;
    v_quitar JSONB;
    v_id_relacion INTEGER;
    v_tabla_relacion TEXT;
    v_tabla_catalogo TEXT;
    v_columna_relacion TEXT;
    v_id_catalogo TEXT;

    v_existe BOOLEAN;
    v_pendientes BOOLEAN;
    v_filas_afectadas INTEGER;
BEGIN
    /*
     * 1. Validar administrador activo.
     */
    SELECT u.*
      INTO v_usuario
      FROM usuario u
      JOIN rol r ON r.id_rol = u.id_rol
     WHERE u.id_usuario = p_id_administrador
       AND u.activo = TRUE
       AND r.nombre = 'admin_cmp';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'El usuario % no existe, esta inactivo o no es administrador',
            p_id_administrador;
    END IF;

    /*
     * 2. Obtener y bloquear la solicitud.
     */
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

    IF v_sol.estado <> 'PENDIENTE' THEN
        RAISE EXCEPTION
            'La solicitud % ya no esta pendiente',
            p_id_solicitud_cambio;
    END IF;

    IF p_decisiones IS NULL
       OR jsonb_typeof(p_decisiones) IS DISTINCT FROM 'object'
       OR p_decisiones = '{}'::JSONB THEN
        RAISE EXCEPTION
            'Las decisiones deben ser un objeto JSON no vacio';
    END IF;

    v_cambios := v_sol.cambios;

    IF v_cambios IS NULL
       OR jsonb_typeof(v_cambios) IS DISTINCT FROM 'object' THEN
        RAISE EXCEPTION
            'La solicitud contiene cambios con formato invalido';
    END IF;

    /*
     * 3. Procesar cada seccion enviada por el administrador.
     */
    FOR v_seccion, v_decision IN
        SELECT key, value
          FROM jsonb_each(p_decisiones)
    LOOP
        IF NOT (v_cambios ? v_seccion) THEN
            RAISE EXCEPTION
                'La seccion % no forma parte de la solicitud',
                v_seccion;
        END IF;

        /*
         * 4. Relaciones: especialidades, subespecialidades
         *    y asociaciones.
         */
        IF v_seccion IN (
            'especialidades',
            'subespecialidades',
            'asociaciones'
        ) THEN

            IF jsonb_typeof(v_decision) IS DISTINCT FROM 'object'
               OR (v_decision - 'estado') <> '{}'::JSONB THEN
                RAISE EXCEPTION
                    'La decision para % debe contener solamente estado',
                    v_seccion;
            END IF;

            v_resultado := v_decision ->> 'estado';

            IF v_resultado NOT IN ('APROBADO', 'RECHAZADO')
               OR v_resultado IS NULL THEN
                RAISE EXCEPTION
                    'La decision para % debe ser APROBADO o RECHAZADO',
                    v_seccion;
            END IF;

            IF v_cambios -> v_seccion ->> 'estado'
               IS DISTINCT FROM 'PENDIENTE' THEN
                RAISE EXCEPTION
                    'La relacion % ya fue resuelta',
                    v_seccion;
            END IF;

            IF v_resultado = 'APROBADO' THEN
                v_agregar := v_cambios -> v_seccion -> 'agregar';
                v_quitar := v_cambios -> v_seccion -> 'quitar';

                IF jsonb_typeof(v_agregar) IS DISTINCT FROM 'array'
                   OR jsonb_typeof(v_quitar) IS DISTINCT FROM 'array' THEN
                    RAISE EXCEPTION
                        'Las operaciones de % tienen un formato invalido',
                        v_seccion;
                END IF;

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

                /*
                 * Agregar relaciones.
                 */
                FOR v_elemento IN
                    SELECT value
                      FROM jsonb_array_elements(v_agregar)
                LOOP
                    IF jsonb_typeof(v_elemento) <> 'number'
                       OR v_elemento::TEXT !~ '^[1-9][0-9]*$' THEN
                        RAISE EXCEPTION
                            'Identificador invalido en %',
                            v_seccion;
                    END IF;

                    v_id_relacion := (v_elemento #>> '{}')::INTEGER;

                    EXECUTE format(
                        'SELECT EXISTS (
                            SELECT 1 FROM %I WHERE %I = $1
                        )',
                        v_tabla_catalogo,
                        v_id_catalogo
                    )
                    INTO v_existe
                    USING v_id_relacion;

                    IF NOT v_existe THEN
                        RAISE EXCEPTION
                            'El identificador % no existe en %',
                            v_id_relacion,
                            v_tabla_catalogo;
                    END IF;

                    EXECUTE format(
                        'INSERT INTO %I (id_medico, %I)
                         SELECT $1, $2
                         WHERE NOT EXISTS (
                             SELECT 1 FROM %I
                              WHERE id_medico = $1 AND %I = $2
                         )',
                        v_tabla_relacion,
                        v_columna_relacion,
                        v_tabla_relacion,
                        v_columna_relacion
                    )
                    USING v_sol.id_medico, v_id_relacion;
                END LOOP;

                /*
                 * Quitar relaciones.
                 */
                FOR v_elemento IN
                    SELECT value
                      FROM jsonb_array_elements(v_quitar)
                LOOP
                    IF jsonb_typeof(v_elemento) <> 'number'
                       OR v_elemento::TEXT !~ '^[1-9][0-9]*$' THEN
                        RAISE EXCEPTION
                            'Identificador invalido en %',
                            v_seccion;
                    END IF;

                    v_id_relacion := (v_elemento #>> '{}')::INTEGER;

                    EXECUTE format(
                        'DELETE FROM %I
                          WHERE id_medico = $1 AND %I = $2',
                        v_tabla_relacion,
                        v_columna_relacion
                    )
                    USING v_sol.id_medico, v_id_relacion;

                    GET DIAGNOSTICS v_filas_afectadas = ROW_COUNT;

                    IF v_filas_afectadas = 0 THEN
                        RAISE EXCEPTION
                            'La relacion % con identificador % ya no existe',
                            v_seccion,
                            v_id_relacion;
                    END IF;
                END LOOP;
            END IF;

            /*
             * Guardar estado de la relacion.
             */
            v_cambios := jsonb_set(
                v_cambios,
                ARRAY[v_seccion, 'estado'],
                to_jsonb(v_resultado),
                FALSE
            );

        /*
         * 5. Registros individuales:
         *    lugar_trabajo, estudio_medico y certificaciones.
         */
        ELSE
            IF v_seccion NOT IN (
                'lugar_trabajo',
                'estudio_medico',
                'certificaciones'
            ) THEN
                RAISE EXCEPTION
                    'La seccion % no admite procesamiento',
                    v_seccion;
            END IF;

            IF jsonb_typeof(v_decision) IS DISTINCT FROM 'array' THEN
                RAISE EXCEPTION
                    'La decision para % debe ser un arreglo',
                    v_seccion;
            END IF;

            IF jsonb_typeof(v_cambios -> v_seccion)
               IS DISTINCT FROM 'array' THEN
                RAISE EXCEPTION
                    'La solicitud contiene un arreglo invalido en %',
                    v_seccion;
            END IF;

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

            /*
             * Recorrer registros de la solicitud.
             */
            FOR v_indice IN 0 ..
                jsonb_array_length(v_cambios -> v_seccion) - 1
            LOOP
                v_elemento :=
                    v_cambios -> v_seccion -> v_indice;

                v_decision :=
                    p_decisiones -> v_seccion -> v_indice;

                IF v_decision IS NULL
                   OR jsonb_typeof(v_decision) IS DISTINCT FROM 'object' THEN
                    RAISE EXCEPTION
                        'Falta la decision para el registro de % en posicion %',
                        v_seccion,
                        v_indice;
                END IF;

                IF (v_elemento -> v_id_campo) IS NULL
                   OR jsonb_typeof(v_elemento -> v_id_campo)
                      IS DISTINCT FROM 'number' THEN
                    RAISE EXCEPTION
                        'El registro de % no contiene un identificador valido',
                        v_seccion;
                END IF;

                v_id_registro :=
                    (v_elemento ->> v_id_campo)::INTEGER;

                /*
                 * Obtener registro y verificar propietario.
                 */
                EXECUTE format(
                    'SELECT to_jsonb(t)
                       FROM %I t
                      WHERE %I = $1
                        AND id_medico = $2',
                    v_tabla,
                    v_id_campo
                )
                INTO v_actual
                USING v_id_registro, v_sol.id_medico;

                IF v_actual IS NULL THEN
                    RAISE EXCEPTION
                        'El registro % no existe o no pertenece al medico %',
                        v_id_registro,
                        v_sol.id_medico;
                END IF;

                /*
                 * Recorrer los campos solicitados.
                 */
                FOR v_campo IN
                    SELECT jsonb_object_keys(v_elemento)
                LOOP
                    IF v_campo = v_id_campo THEN
                        CONTINUE;
                    END IF;

                    IF NOT (v_campo = ANY(v_campos_permitidos)) THEN
                        RAISE EXCEPTION
                            'Campo % no permitido en %',
                            v_campo,
                            v_seccion;
                    END IF;

                    IF NOT (v_decision ? v_campo) THEN
                        RAISE EXCEPTION
                            'Falta la decision para el campo %',
                            v_campo;
                    END IF;

                    v_resultado := v_decision ->> v_campo;

                    IF v_resultado NOT IN ('APROBADO', 'RECHAZADO')
                       OR v_resultado IS NULL THEN
                        RAISE EXCEPTION
                            'La decision para % debe ser APROBADO o RECHAZADO',
                            v_campo;
                    END IF;

                    /*
                     * No permitir resolver dos veces el mismo campo.
                     */
                    IF v_elemento -> v_campo ->> 'estado'
                       IS DISTINCT FROM 'PENDIENTE' THEN
                        RAISE EXCEPTION
                            'El campo % del registro % ya fue resuelto',
                            v_campo,
                            v_id_registro;
                    END IF;

                    /*
                     * Aplicar el cambio solamente si se aprueba.
                     */
                    IF v_resultado = 'APROBADO' THEN
                        v_anterior :=
                            v_elemento -> v_campo -> 'valor_anterior';

                        IF (v_actual -> v_campo)
                           IS DISTINCT FROM v_anterior THEN
                            RAISE EXCEPTION
                                'El campo % del registro % cambio desde que se creo la solicitud',
                                v_campo,
                                v_id_registro;
                        END IF;

                        v_nuevo :=
                            v_elemento -> v_campo -> 'valor_nuevo';

                        SELECT format_type(a.atttypid, a.atttypmod)
                          INTO v_tipo_columna
                          FROM pg_attribute a
                         WHERE a.attrelid = to_regclass(v_tabla)
                           AND a.attname = v_campo
                           AND a.attnum > 0
                           AND NOT a.attisdropped;

                        IF v_tipo_columna IS NULL THEN
                            RAISE EXCEPTION
                                'No se encontro el tipo del campo %',
                                v_campo;
                        END IF;

                        EXECUTE format(
                            'UPDATE %I
                                SET %I = ($1 #>> ''{}'')::%s
                              WHERE %I = $2
                                AND id_medico = $3',
                            v_tabla,
                            v_campo,
                            v_tipo_columna,
                            v_id_campo
                        )
                        USING v_nuevo, v_id_registro, v_sol.id_medico;
                    END IF;

                    /*
                     * Actualizar el estado del campo dentro del JSON.
                     */
                    v_cambios := jsonb_set(
                        v_cambios,
                        ARRAY[
                            v_seccion,
                            v_indice::TEXT,
                            v_campo,
                            'estado'
                        ],
                        to_jsonb(v_resultado),
                        FALSE
                    );
                END LOOP;

                /*
                 * Rechazar decisiones para campos que no fueron solicitados.
                 */
                FOR v_campo IN
                    SELECT jsonb_object_keys(v_decision)
                LOOP
                    IF NOT (v_elemento ? v_campo) THEN
                        RAISE EXCEPTION
                            'El campo % no forma parte del registro solicitado',
                            v_campo;
                    END IF;
                END LOOP;
            END LOOP;

            /*
             * Verificar que las decisiones correspondan a todos
             * los registros incluidos en esta seccion.
             */
            IF jsonb_array_length(p_decisiones -> v_seccion) IS DISTINCT FROM
               jsonb_array_length(v_cambios -> v_seccion) THEN
                RAISE EXCEPTION
                    'La cantidad de decisiones para % no coincide con la solicitud',
                    v_seccion;
            END IF;
        END IF;
    END LOOP;

    /*
     * 6. Comprobar si quedan decisiones pendientes.
     */
    SELECT EXISTS (
        SELECT 1
          FROM jsonb_each(v_cambios) seccion
         WHERE
            (
                jsonb_typeof(seccion.value) = 'object'
                AND seccion.value ->> 'estado' = 'PENDIENTE'
            )
            OR
            (
                jsonb_typeof(seccion.value) = 'array'
                AND EXISTS (
                    SELECT 1
                      FROM jsonb_array_elements(seccion.value) registro
                     WHERE EXISTS (
                         SELECT 1
                           FROM jsonb_each(registro.value) campo
                          WHERE campo.value ->> 'estado' = 'PENDIENTE'
                     )
                )
            )
    )
    INTO v_pendientes;

    /*
     * 7. Actualizar solicitud.
     */
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

    /*
     * 8. Registrar auditoria.
     */
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
    );

    RETURN TRUE;
END;
$$;
