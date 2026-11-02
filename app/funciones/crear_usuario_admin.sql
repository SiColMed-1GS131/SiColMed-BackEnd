CREATE OR REPLACE FUNCTION crear_usuario_admin(
    p_correo           text,
    p_password_hash    text,
    p_id_administrador integer DEFAULT NULL
)
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    v_correo     text := lower(btrim(p_correo));
    v_id_rol     integer;
    v_hay_admin  boolean;
    v_id_usuario integer;
BEGIN
    IF v_correo IS NULL OR v_correo !~ '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$' THEN
        RAISE EXCEPTION 'El correo no es valido';
    END IF;
    IF coalesce(p_password_hash, '') = '' THEN
        RAISE EXCEPTION 'El hash de la contraseña es obligatorio';
    END IF;

    SELECT r.id_rol
      INTO v_id_rol
      FROM rol r
     WHERE lower(btrim(r.nombre)) = 'admin_cmp'
     ORDER BY r.id_rol
     LIMIT 1;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'No existe el rol admin_cmp';
    END IF;

    SELECT EXISTS (
               SELECT 1
                 FROM usuario u
                 JOIN rol r ON r.id_rol = u.id_rol
                WHERE lower(btrim(r.nombre)) = 'admin_cmp'
                  AND u.activo)
      INTO v_hay_admin;

    -- Quien crea la cuenta debe ser un administrador activo.
    -- Solo el primer administrador del sistema se puede crear sin indicarlo.
    IF p_id_administrador IS NOT NULL THEN
        IF NOT EXISTS (
               SELECT 1
                 FROM usuario u
                 JOIN rol r ON r.id_rol = u.id_rol
                WHERE u.id_usuario = p_id_administrador
                  AND u.activo
                  AND lower(btrim(r.nombre)) = 'admin_cmp') THEN
            RAISE EXCEPTION 'El usuario % no existe, está inactivo o no es administrador', p_id_administrador;
        END IF;
    ELSIF v_hay_admin THEN
        RAISE EXCEPTION 'Ya existe un administrador: debe indicar quién crea la cuenta';
    END IF;

    IF EXISTS (SELECT 1 FROM usuario WHERE lower(correo) = v_correo) THEN
        RAISE EXCEPTION 'El correo % ya está registrado', v_correo;
    END IF;

    INSERT INTO usuario (id_rol, correo, password_hash, activo, fecha_creacion)
    VALUES (v_id_rol, v_correo, p_password_hash, true, now())
    RETURNING id_usuario INTO v_id_usuario;

    INSERT INTO auditoria (id_usuario, id_rol, accion, entidad, id_registro, fecha_hora, descripcion)
    VALUES (coalesce(p_id_administrador, v_id_usuario), v_id_rol, 'CREAR_USUARIO_ADMIN', 'USUARIO',
            v_id_usuario, now(), 'Usuario administrador ' || v_correo || ' creado');

    RETURN v_id_usuario;
END;
$$;