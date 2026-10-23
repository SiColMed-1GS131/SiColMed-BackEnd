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
    v_campo TEXT;
    v_decision JSONB;
    v_resultado TEXT;
    v_pendientes BOOLEAN;

    v_partes TEXT[];
    v_tabla TEXT;
    v_nombre_campo TEXT;
    v_id_registro INTEGER;
    v_id_columna TEXT;
    v_tipo_columna TEXT;

    v_actual JSONB;
    v_anterior JSONB;
    v_nuevo JSONB;

    v_agregar JSONB;
    v_quitar JSONB;
    v_elemento JSONB;
    v_id_relacion INTEGER;
    v_tabla_relacion TEXT;
    v_tabla_catalogo TEXT;
    v_columna_relacion TEXT;
    v_id_catalogo TEXT;
    v_existe BOOLEAN;
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
     * 2. Bloquear la solicitud para evitar procesamiento concurrente.
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
       OR jsonb_typeof(p_decisiones) <> 'object'
       OR p_decisiones = '{}'::JSONB THEN
        RAISE EXCEPTION
            'Las decisiones deben ser un objeto JSON no vacio';
    END IF;

    v_cambios := v_sol.cambios;

    IF v_cambios IS NULL OR jsonb_typeof(v_cambios) <> 'object' THEN
        RAISE EXCEPTION
            'La solicitud contiene cambios con formato invalido';
    END IF;

    /*
     * 3. Procesar cada decisión.
     */
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

        IF jsonb_typeof(v_decision) <> 'object'
           OR (v_decision - 'estado') <> '{}'::JSONB THEN
            RAISE EXCEPTION
                'La decision para % debe contener solamente estado',
                v_campo;
        END IF;

        v_resultado := v_decision ->> 'estado';

        IF v_resultado NOT IN ('APROBADO', 'RECHAZADO')
           OR v_resultado IS NULL THEN
            RAISE EXCEPTION
                'La decision para % debe ser APROBADO o RECHAZADO',
                v_campo;
        END IF;

        /*
         * 4. Si se aprueba, aplicar el cambio.
         * Si se rechaza, no se modifica el registro original.
         */
        IF v_resultado = 'APROBADO' THEN

            /*
             * 4A. Relaciones: especialidades, subespecialidades
             * y asociaciones.
             */
            IF v_campo IN (
                'especialidades',
                'subespecialidades',
                'asociaciones'
            ) THEN
                v_agregar := v_cambios -> v_campo -> 'agregar';
                v_quitar := v_cambios -> v_campo -> 'quitar';

                IF jsonb_typeof(v_agregar) <> 'array'
                   OR jsonb_typeof(v_quitar) <> 'array' THEN
                    RAISE EXCEPTION
                        'Las operaciones de % no tienen un formato valido',
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
                            v_campo;
                    END IF;

                    v_id_relacion := (v_elemento #>> '{}')::INTEGER;

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
                             SELECT 1
                               FROM %I
                              WHERE id_medico = $1
                                AND %I = $2
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
                            v_campo;
                    END IF;

                    v_id_relacion := (v_elemento #>> '{}')::INTEGER;

                    EXECUTE format(
                        'DELETE FROM %I
                          WHERE id_medico = $1
                            AND %I = $2',
                        v_tabla_relacion,
                        v_columna_relacion
                    )
                    USING v_sol.id_medico, v_id_relacion;

                    GET DIAGNOSTICS v_filas_afectadas = ROW_COUNT;

                    IF v_filas_afectadas = 0 THEN
                        RAISE EXCEPTION
                            'La relacion % con identificador % ya no existe',
                            v_campo,
                            v_id_relacion;
                    END IF;
                END LOOP;

            /*
             * 4B. Cambios individuales:
             * tabla:id_registro:campo
             */
            ELSE
                v_partes := string_to_array(v_campo, ':');

                IF array_length(v_partes, 1) <> 3
                   OR v_partes[2] !~ '^[1-9][0-9]*$'
                   OR v_partes[3] = '' THEN
                    RAISE EXCEPTION
                        'Formato incorrecto para %',
                        v_campo;
                END IF;

                v_tabla := v_partes[1];
                v_id_registro := v_partes[2]::INTEGER;
                v_nombre_campo := v_partes[3];

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

                /*
                 * Identificar la clave primaria de la tabla.
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
                        'No se encontro la clave primaria de %',
                        v_tabla;
                END IF;

                /*
                 * Verificar que el campo exista.
                 */
                SELECT format_type(a.atttypid, a.atttypmod)
                  INTO v_tipo_columna
                  FROM pg_attribute a
                 WHERE a.attrelid = to_regclass(v_tabla)
                   AND a.attname = v_nombre_campo
                   AND a.attnum > 0
                   AND NOT a.attisdropped;

                IF v_tipo_columna IS NULL THEN
                    RAISE EXCEPTION
                        'El campo % no existe en %',
                        v_nombre_campo,
                        v_tabla;
                END IF;

                /*
                 * No permitir modificar claves primarias, campos unicos
                 * ni identificadores de propietario.
                 *
                 * Se permiten las claves foraneas geograficas de direccion
                 * para solicitar correcciones de provincia, distrito
                 * y corregimiento. Las restricciones de la base de datos
                 * siguen validando que los identificadores existan.
                 */
                IF EXISTS (
                    SELECT 1
                      FROM pg_constraint c
                      JOIN pg_attribute a
                        ON a.attrelid = c.conrelid
                       AND a.attnum = ANY(c.conkey)
                     WHERE c.conrelid = to_regclass(v_tabla)
                       AND c.contype IN ('p', 'u')
                       AND a.attname = v_nombre_campo
                ) OR EXISTS (
                    SELECT 1
                      FROM pg_constraint c
                      JOIN pg_attribute a
                        ON a.attrelid = c.conrelid
                       AND a.attnum = ANY(c.conkey)
                     WHERE c.conrelid = to_regclass(v_tabla)
                       AND c.contype = 'f'
                       AND a.attname = v_nombre_campo
                       AND NOT (
                           v_tabla = 'direccion'
                           AND v_nombre_campo IN (
                               'id_provincia',
                               'id_distrito',
                               'id_corregimiento'
                           )
                       )
                ) OR v_nombre_campo IN (
                    'id_usuario',
                    'id_medico',
                    'id_direccion'
                ) OR (
                    v_nombre_campo IN (
                        'id_provincia',
                        'id_distrito',
                        'id_corregimiento'
                    )
                    AND v_tabla <> 'direccion'
                ) THEN
                    RAISE EXCEPTION
                        'El campo % no puede modificarse mediante solicitud',
                        v_nombre_campo;
                END IF;


                /*
                 * Los datos personales del médico no pasan por aprobación.
                 */
                IF v_tabla = 'medico'
                   AND v_nombre_campo IN (
                       'primer_nombre',
                       'segundo_nombre',
                       'apellido_paterno',
                       'apellido_materno',
                       'foto',
                       'fecha_nacimiento',
                       'telefono_residencial',
                       'celular',
                       'email_personal'
                   ) THEN
                    RAISE EXCEPTION
                        'El campo personal % debe actualizarse directamente',
                        v_nombre_campo;
                END IF;

                /*
                 * Obtener el registro y comprobar que pertenezca
                 * al médico de la solicitud.
                 */
                IF v_tabla = 'medico' THEN
                    SELECT to_jsonb(m)
                    INTO v_actual
                    FROM medico m
                    WHERE m.id_medico = v_sol.id_medico
                    AND m.id_medico = v_id_registro;

                ELSIF v_tabla = 'direccion' THEN
                    SELECT to_jsonb(d)
                      INTO v_actual
                      FROM direccion d
                     WHERE d.id_direccion = v_id_registro
                       AND (
                           EXISTS (
                               SELECT 1
                                 FROM medico m
                                WHERE m.id_medico = v_sol.id_medico
                                  AND m.id_direccion = d.id_direccion
                           )
                           OR EXISTS (
                               SELECT 1
                                 FROM lugar_trabajo lt
                                WHERE lt.id_medico = v_sol.id_medico
                                  AND lt.id_direccion = d.id_direccion
                           )
                       );

                ELSE
                    EXECUTE format(
                        'SELECT to_jsonb(t)
                           FROM %I t
                          WHERE %I = $1
                            AND id_medico = $2',
                        v_tabla,
                        v_id_columna
                    )
                    INTO v_actual
                    USING v_id_registro, v_sol.id_medico;
                END IF;

                IF v_actual IS NULL THEN
                    RAISE EXCEPTION
                        'El registro % no existe o no pertenece al medico %',
                        v_id_registro,
                        v_sol.id_medico;
                END IF;

                /*
                 * Comprobar que el valor original no haya cambiado
                 * desde la creación de la solicitud.
                 */
                v_anterior :=
                    v_cambios -> v_campo -> 'valor_anterior';

                IF (v_actual -> v_nombre_campo)
                   IS DISTINCT FROM v_anterior THEN
                    RAISE EXCEPTION
                        'El campo % cambio desde que se creo la solicitud',
                        v_campo;
                END IF;

                v_nuevo := v_cambios -> v_campo -> 'valor_nuevo';

                /*
                 * Actualizar usando el tipo real de la columna.
                 * El nombre de la columna y la tabla se validaron antes.
                 */
                IF v_tabla = 'medico' THEN
                    EXECUTE format(
                        'UPDATE %I
                            SET %I = ($1 #>> ''{}'')::%s
                          WHERE %I = $2',
                        v_tabla,
                        v_nombre_campo,
                        v_tipo_columna,
                        v_id_columna
                    )
                    USING v_nuevo, v_sol.id_medico;

                ELSIF v_tabla = 'direccion' THEN
                    EXECUTE format(
                        'UPDATE %I
                            SET %I = ($1 #>> ''{}'')::%s
                          WHERE %I = $2',
                        v_tabla,
                        v_nombre_campo,
                        v_tipo_columna,
                        v_id_columna
                    )
                    USING v_nuevo, v_id_registro;

                ELSE
                    EXECUTE format(
                        'UPDATE %I
                            SET %I = ($1 #>> ''{}'')::%s
                          WHERE %I = $2
                            AND id_medico = $3',
                        v_tabla,
                        v_nombre_campo,
                        v_tipo_columna,
                        v_id_columna
                    )
                    USING v_nuevo, v_id_registro, v_sol.id_medico;
                END IF;
            END IF;
        END IF;

        /*
         * 5. Guardar la decisión individual.
         */
        v_cambios := jsonb_set(
            v_cambios,
            ARRAY[v_campo, 'estado'],
            to_jsonb(v_resultado),
            FALSE
        );
    END LOOP;

    /*
     * 6. Comprobar si quedan decisiones pendientes.
     */
    SELECT EXISTS (
        SELECT 1
          FROM jsonb_each(v_cambios) e
         WHERE e.value ->> 'estado' = 'PENDIENTE'
    )
    INTO v_pendientes;

    /*
     * 7. Actualizar la solicitud.
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
     * 8. Registrar auditoría.
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