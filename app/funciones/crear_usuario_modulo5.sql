CREATE OR REPLACE FUNCTION crear_usuario_modulo5(
    p_correo           text,
    p_password_hash    text,
    p_rol              text,
    p_id_administrador integer
)
RETURNS integer
LANGUAGE plpgsql
AS $$
-- DEF-009: alta de los usuarios del Módulo 5 (tesorero y admin_asociacion), que ninguna
-- función creaba. Mismas reglas que crear_usuario_admin: la cuenta la crea un
-- administrador activo (admin_cmp), el correo es único y el alta queda en auditoria.
-- Limitación: usuario no tiene relación con asociacion, así que un admin_asociacion no
-- indica qué asociación administra (además, el catálogo de asociaciones está vacío).
DECLARE
    v_correo     text := lower(btrim(p_correo));
    v_rol        text := lower(btrim(p_rol));
    v_id_rol       integer;
    v_id_rol_admin integer;
    v_id_usuario   integer;
BEGIN
    IF v_correo IS NULL OR v_correo !~ '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$' THEN
        RAISE EXCEPTION 'El correo no es valido';
    END IF;
    IF coalesce(p_password_hash, '') = '' THEN
        RAISE EXCEPTION 'El hash de la contraseña es obligatorio';
    END IF;
    IF v_rol IS NULL OR v_rol NOT IN ('tesorero', 'admin_asociacion') THEN
        RAISE EXCEPTION 'El rol debe ser tesorero o admin_asociacion';
    END IF;

    SELECT r.id_rol
      INTO v_id_rol
      FROM rol r
     WHERE lower(btrim(r.nombre)) = v_rol
     ORDER BY r.id_rol
     LIMIT 1;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'No existe el rol %', v_rol;
    END IF;

    SELECT u.id_rol
      INTO v_id_rol_admin
      FROM usuario u
      JOIN rol r ON r.id_rol = u.id_rol
     WHERE u.id_usuario = p_id_administrador
       AND u.activo
       AND lower(btrim(r.nombre)) = 'admin_cmp';
    IF NOT FOUND THEN
        RAISE EXCEPTION 'El usuario % no existe, está inactivo o no es administrador', p_id_administrador;
    END IF;

    IF EXISTS (SELECT 1 FROM usuario WHERE lower(correo) = v_correo) THEN
        RAISE EXCEPTION 'El correo % ya está registrado', v_correo;
    END IF;

    INSERT INTO usuario (id_rol, correo, password_hash, activo, fecha_creacion)
    VALUES (v_id_rol, v_correo, p_password_hash, true, now())
    RETURNING id_usuario INTO v_id_usuario;

    INSERT INTO auditoria (id_usuario, id_rol, accion, entidad, id_registro, fecha_hora, descripcion)
    VALUES (p_id_administrador, v_id_rol_admin, 'CREAR_USUARIO_MODULO5', 'USUARIO',
            v_id_usuario, now(), 'Usuario ' || v_rol || ' ' || v_correo || ' creado');

    RETURN v_id_usuario;
END;
$$;
