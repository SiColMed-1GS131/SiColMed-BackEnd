CREATE OR REPLACE FUNCTION crear_cuenta_medico(
    p_numero_idoneidad text,
    p_cedula           text,
    p_correo           text,
    p_password_hash    text
)
RETURNS integer
LANGUAGE plpgsql
AS $$
-- DEF-004: la idoneidad es pública (directorio), así que además se exige la cédula
-- del médico. Las dos se comparan sin espacios y en mayúsculas (8-123-456, PE-1-234).
-- Si no coinciden, el error es el mismo que cuando la idoneidad no existe, para no
-- revelar cuál de los dos datos falló.
DECLARE
    v_correo         text := lower(btrim(p_correo));
    v_id_medico      integer;
    v_usuario_actual integer;
    v_id_rol         integer;
    v_id_usuario     integer;
BEGIN
    IF coalesce(btrim(p_numero_idoneidad), '') = '' THEN
        RAISE EXCEPTION 'El número de idoneidad es obligatorio';
    END IF;
    IF coalesce(btrim(p_cedula), '') = '' THEN
        RAISE EXCEPTION 'La cédula es obligatoria';
    END IF;
    IF v_correo IS NULL OR v_correo !~ '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$' THEN
        RAISE EXCEPTION 'El correo no es válido';
    END IF;
    IF coalesce(p_password_hash, '') = '' THEN
        RAISE EXCEPTION 'El hash de la contraseña es obligatorio';
    END IF;

    SELECT m.id_medico, m.id_usuario
      INTO v_id_medico, v_usuario_actual
      FROM medico m
     WHERE m.numero_idoneidad = btrim(p_numero_idoneidad)
       AND upper(regexp_replace(m.cedula, '\s', '', 'g'))
         = upper(regexp_replace(p_cedula, '\s', '', 'g'))
       FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'No existe un médico registrado con el número de idoneidad %', btrim(p_numero_idoneidad);
    END IF;
    IF v_usuario_actual IS NOT NULL THEN
        RAISE EXCEPTION 'El médico ya tiene una cuenta de usuario';
    END IF;
    IF EXISTS (SELECT 1 FROM usuario WHERE lower(correo) = v_correo) THEN
        RAISE EXCEPTION 'El correo % ya está registrado', v_correo;
    END IF;

    SELECT r.id_rol INTO v_id_rol FROM rol r WHERE LOWER(BTRIM(r.nombre)) = 'medico';
    IF NOT FOUND THEN
        RAISE EXCEPTION 'No existe el rol medico';
    END IF;

    INSERT INTO usuario (id_rol, correo, password_hash, activo, fecha_creacion)
    VALUES (v_id_rol, v_correo, p_password_hash, true, now())
    RETURNING id_usuario INTO v_id_usuario;

    UPDATE medico SET id_usuario = v_id_usuario WHERE id_medico = v_id_medico;

    RETURN v_id_usuario;
END;
$$;