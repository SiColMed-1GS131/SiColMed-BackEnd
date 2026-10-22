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
    v_id_usuario_medico INTEGER;
    v_id_direccion INTEGER;
    v_datos_medico JSONB;
    v_datos_dir JSONB;
    v_campos_permitidos TEXT[];
    v_campos_obligatorios TEXT[] := ARRAY[
        'numero_idoneidad',
        'numero_registro_medico',
        'cedula',
        'primer_nombre',
        'apellido_paterno',
        'fecha_nacimiento'
    ];
    v_campo TEXT;
    v_valor TEXT;
    v_rec medico%ROWTYPE;
    v_dir direccion%ROWTYPE;
    v_corregimiento RECORD;
    v_hay_cambios BOOLEAN := FALSE;
BEGIN
    -- validar los identificadores
    IF p_id_medico IS NULL OR p_id_medico <= 0 THEN
        RAISE EXCEPTION 'El id del medico no es valido';
    END IF;

    IF p_id_administrador IS NULL OR p_id_administrador <= 0 THEN
        RAISE EXCEPTION 'El id del usuario que realiza el cambio no es valido';
    END IF;

    -- validar que los datos sean un objeto json
    IF p_datos IS NULL
       OR jsonb_typeof(p_datos) <> 'object'
       OR p_datos = '{}'::JSONB THEN
        RAISE EXCEPTION 'Debe enviar un objeto json con los datos que desea actualizar';
    END IF;

    -- comprobar que el usuario que realiza el cambio exista y este activo
    SELECT r.nombre
    INTO v_rol
    FROM usuario u
    INNER JOIN rol r
        ON r.id_rol = u.id_rol
    WHERE u.id_usuario = p_id_administrador
      AND u.activo = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'El usuario no existe o esta inactivo';
    END IF;

    -- validar el rol del usuario
    IF v_rol NOT IN ('medico', 'admin_cmp') THEN
        RAISE EXCEPTION 'El usuario no tiene permisos para actualizar medicos';
    END IF;

    -- separar los datos del medico y de la direccion
    v_datos_medico := p_datos - 'direccion';
    v_datos_dir := p_datos -> 'direccion';

    -- validar que direccion sea un objeto json si fue enviada
    IF p_datos ? 'direccion' THEN
        IF v_datos_dir IS NULL
           OR jsonb_typeof(v_datos_dir) <> 'object'
           OR v_datos_dir = '{}'::JSONB THEN
            RAISE EXCEPTION 'Los datos de la direccion deben enviarse como un objeto json no vacio';
        END IF;
    END IF;

    -- bloquear el registro del medico para evitar cambios simultaneos
    SELECT m.id_usuario, m.id_direccion
    INTO v_id_usuario_medico, v_id_direccion
    FROM medico m
    WHERE m.id_medico = p_id_medico
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'El medico no existe';
    END IF;

    -- un medico solamente puede actualizar su propio perfil
    IF v_rol = 'medico'
       AND v_id_usuario_medico IS DISTINCT FROM p_id_administrador THEN
        RAISE EXCEPTION 'Un medico solamente puede actualizar su propio perfil';
    END IF;

    -- definir los campos permitidos segun el rol
    IF v_rol = 'medico' THEN
        v_campos_permitidos := ARRAY[
            'primer_nombre',
            'segundo_nombre',
            'apellido_paterno',
            'apellido_materno',
            'foto',
            'telefono_residencial',
            'celular',
            'email_personal'
        ];
    ELSE
        v_campos_permitidos := ARRAY[
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
    END IF;

    -- validar los campos enviados para el medico
    FOR v_campo IN
        SELECT jsonb_object_keys(v_datos_medico)
    LOOP
        IF NOT (v_campo = ANY(v_campos_permitidos)) THEN
            RAISE EXCEPTION 'El campo "%" no esta permitido para este usuario', v_campo;
        END IF;

        -- validar campos obligatorios cuando se envian
        IF v_campo = ANY(v_campos_obligatorios) THEN
            IF v_datos_medico -> v_campo = 'null'::JSONB
               OR BTRIM(v_datos_medico ->> v_campo) = '' THEN
                RAISE EXCEPTION 'El campo "%" no puede estar vacio', v_campo;
            END IF;
        END IF;

        -- validar que los campos de texto no tengan cadenas vacias
        IF jsonb_typeof(v_datos_medico -> v_campo) = 'string'
           AND BTRIM(v_datos_medico ->> v_campo) = '' THEN
            RAISE EXCEPTION 'El campo "%" no puede estar vacio', v_campo;
        END IF;
    END LOOP;

    -- validar el correo personal si fue enviado
    IF v_datos_medico ? 'email_personal'
       AND v_datos_medico -> 'email_personal' <> 'null'::JSONB THEN

        IF (v_datos_medico ->> 'email_personal')
           !~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$' THEN
            RAISE EXCEPTION 'El correo personal no tiene un formato valido';
        END IF;
    END IF;

    -- validar la fecha de nacimiento si fue enviada
    IF v_datos_medico ? 'fecha_nacimiento'
       AND v_datos_medico -> 'fecha_nacimiento' <> 'null'::JSONB THEN

        BEGIN
            IF (v_datos_medico ->> 'fecha_nacimiento')::DATE > CURRENT_DATE THEN
                RAISE EXCEPTION 'La fecha de nacimiento no puede ser futura';
            END IF;
        EXCEPTION
            WHEN invalid_datetime_format OR datetime_field_overflow THEN
                RAISE EXCEPTION 'La fecha de nacimiento no tiene un formato valido';
        END;
    END IF;

    -- validar que el numero de idoneidad no este repetido
    IF v_datos_medico ? 'numero_idoneidad' THEN
        IF EXISTS (
            SELECT 1
            FROM medico m
            WHERE m.numero_idoneidad = v_datos_medico ->> 'numero_idoneidad'
              AND m.id_medico <> p_id_medico
        ) THEN
            RAISE EXCEPTION 'El numero de idoneidad ya esta registrado';
        END IF;
    END IF;

    -- validar que el numero de registro medico no este repetido
    IF v_datos_medico ? 'numero_registro_medico' THEN
        IF EXISTS (
            SELECT 1
            FROM medico m
            WHERE m.numero_registro_medico = v_datos_medico ->> 'numero_registro_medico'
              AND m.id_medico <> p_id_medico
        ) THEN
            RAISE EXCEPTION 'El numero de registro medico ya esta registrado';
        END IF;
    END IF;

    -- validar que la cedula no este repetida
    IF v_datos_medico ? 'cedula' THEN
        IF EXISTS (
            SELECT 1
            FROM medico m
            WHERE m.cedula = v_datos_medico ->> 'cedula'
              AND m.id_medico <> p_id_medico
        ) THEN
            RAISE EXCEPTION 'La cedula ya esta registrada para otro medico';
        END IF;
    END IF;

    -- actualizar solamente los campos del medico que fueron enviados
    FOR v_campo IN
        SELECT jsonb_object_keys(v_datos_medico)
    LOOP
        v_hay_cambios := TRUE;

        EXECUTE format(
            'UPDATE medico SET %I = ($1).%I WHERE id_medico = $2',
            v_campo,
            v_campo
        )
        USING jsonb_populate_record(NULL::medico, v_datos_medico), p_id_medico;
    END LOOP;

    -- actualizar la direccion si fue enviada
    IF p_datos ? 'direccion' THEN

        -- validar los campos permitidos para la direccion
        FOR v_campo IN
            SELECT jsonb_object_keys(v_datos_dir)
        LOOP
            IF NOT (
                v_campo = ANY(
                    ARRAY[
                        'apartado_postal',
                        'calle',
                        'edificio',
                        'numero_direccion',
                        'id_corregimiento'
                    ]
                )
            ) THEN
                RAISE EXCEPTION 'El campo "%" no esta permitido para la direccion', v_campo;
            END IF;
        END LOOP;

        -- bloquear la direccion actual
        SELECT *
        INTO v_dir
        FROM direccion
        WHERE id_direccion = v_id_direccion
        FOR UPDATE;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'No se encontro la direccion del medico';
        END IF;

        -- combinar la direccion actual con los campos nuevos
        v_dir := jsonb_populate_record(
            v_dir,
            v_datos_dir
        );

        -- validar los campos obligatorios de la direccion
        IF v_dir.apartado_postal IS NULL
           OR BTRIM(v_dir.apartado_postal) = ''
           OR v_dir.calle IS NULL
           OR BTRIM(v_dir.calle) = ''
           OR v_dir.numero_direccion IS NULL
           OR BTRIM(v_dir.numero_direccion) = ''
           OR v_dir.id_corregimiento IS NULL THEN

            RAISE EXCEPTION
                'La direccion debe tener apartado postal, calle, numero de direccion y corregimiento';
        END IF;

        -- validar que el corregimiento exista y obtener su distrito y provincia
        SELECT
            c.id_corregimiento,
            c.id_distrito,
            d.id_provincia
        INTO v_corregimiento
        FROM corregimiento c
        INNER JOIN distrito d
            ON d.id_distrito = c.id_distrito
        WHERE c.id_corregimiento = v_dir.id_corregimiento;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'El corregimiento indicado no existe';
        END IF;

        -- actualizar distrito y provincia segun el corregimiento seleccionado
        v_dir.id_distrito := v_corregimiento.id_distrito;
        v_dir.id_provincia := v_corregimiento.id_provincia;

        -- comprobar que la direccion final cumpla las restricciones de la tabla
        IF v_dir.id_distrito IS NULL
           OR v_dir.id_provincia IS NULL THEN
            RAISE EXCEPTION
                'No se pudo determinar el distrito y la provincia de la direccion';
        END IF;

        -- actualizar los campos enviados y los datos derivados de ubicacion
        UPDATE direccion
        SET
            apartado_postal = v_dir.apartado_postal,
            calle = v_dir.calle,
            edificio = v_dir.edificio,
            numero_direccion = v_dir.numero_direccion,
            id_corregimiento = v_dir.id_corregimiento,
            id_distrito = v_dir.id_distrito,
            id_provincia = v_dir.id_provincia
        WHERE id_direccion = v_id_direccion;

        v_hay_cambios := TRUE;
    END IF;

    -- registrar la operacion en auditoria
    IF v_hay_cambios THEN
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
            p_id_administrador,
            u.id_rol,
            'ACTUALIZAR',
            'medico',
            p_id_medico,
            CURRENT_TIMESTAMP,
            'Actualizacion de datos del medico'
        FROM usuario u
        WHERE u.id_usuario = p_id_administrador;
    END IF;

    RETURN TRUE;
END;
$$;