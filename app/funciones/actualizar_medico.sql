CREATE OR REPLACE FUNCTION actualizar_medico(
    p_id_medico        integer,
    p_id_administrador integer,
    p_datos            jsonb
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
DECLARE
    v_permitidos_medico text[] := ARRAY[
        'numero_idoneidad', 'numero_registro_medico', 'cedula', 'primer_nombre',
        'segundo_nombre', 'apellido_paterno', 'apellido_materno', 'foto',
        'fecha_nacimiento', 'telefono_residencial', 'celular', 'email_personal'];
    v_obligatorios      text[] := ARRAY[
        'numero_idoneidad', 'numero_registro_medico', 'cedula', 'primer_nombre',
        'apellido_paterno', 'fecha_nacimiento'];
    v_permitidos_dir    text[] := ARRAY[
        'apartado_postal', 'calle', 'edificio', 'numero_direccion', 'id_corregimiento'];
    v_medico            medico%ROWTYPE;
    v_rec               medico;
    v_dir               direccion;
    v_datos_medico      jsonb;
    v_datos_dir         jsonb;
    v_id_direccion      integer;
    v_campo             text;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM usuario WHERE id_usuario = p_id_administrador AND activo) THEN
        RAISE EXCEPTION 'El administrador % no existe o está inactivo', p_id_administrador;
    END IF;

    SELECT * INTO v_medico FROM medico WHERE id_medico = p_id_medico FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'El médico % no existe', p_id_medico;
    END IF;

    IF p_datos IS NULL OR jsonb_typeof(p_datos) <> 'object' OR p_datos = '{}'::jsonb THEN
        RAISE EXCEPTION 'Los datos deben ser un objeto JSON con al menos un campo';
    END IF;

    v_datos_medico := p_datos - 'direccion';

    FOR v_campo IN SELECT jsonb_object_keys(v_datos_medico) LOOP
        IF NOT (v_campo = ANY (v_permitidos_medico)) THEN
            RAISE EXCEPTION 'El campo % no puede actualizarse', v_campo;
        END IF;
    END LOOP;

    -- Convierte el JSON a los tipos reales de la tabla (date, text, ...).
    v_rec := jsonb_populate_record(NULL::medico, v_datos_medico);

    FOREACH v_campo IN ARRAY v_obligatorios LOOP
        IF v_datos_medico ? v_campo
           AND coalesce(btrim(to_jsonb(v_rec) ->> v_campo), '') = '' THEN
            RAISE EXCEPTION 'El campo % no puede quedar vacío', v_campo;
        END IF;
    END LOOP;

    IF v_datos_medico ? 'numero_idoneidad' AND EXISTS (
           SELECT 1 FROM medico WHERE numero_idoneidad = btrim(v_rec.numero_idoneidad) AND id_medico <> p_id_medico) THEN
        RAISE EXCEPTION 'Ya existe un médico con el número de idoneidad %', v_rec.numero_idoneidad;
    END IF;
    IF v_datos_medico ? 'numero_registro_medico' AND EXISTS (
           SELECT 1 FROM medico WHERE numero_registro_medico = btrim(v_rec.numero_registro_medico) AND id_medico <> p_id_medico) THEN
        RAISE EXCEPTION 'Ya existe un médico con el número de registro médico %', v_rec.numero_registro_medico;
    END IF;
    IF v_datos_medico ? 'cedula' AND EXISTS (
           SELECT 1 FROM medico WHERE cedula = btrim(v_rec.cedula) AND id_medico <> p_id_medico) THEN
        RAISE EXCEPTION 'Ya existe un médico con la cédula %', v_rec.cedula;
    END IF;
    IF v_datos_medico ? 'fecha_nacimiento' AND v_rec.fecha_nacimiento > CURRENT_DATE THEN
        RAISE EXCEPTION 'La fecha de nacimiento no puede ser futura';
    END IF;

    FOR v_campo IN SELECT jsonb_object_keys(v_datos_medico) LOOP
        EXECUTE format('UPDATE medico SET %I = ($1).%I WHERE id_medico = $2', v_campo, v_campo)
          USING v_rec, p_id_medico;
    END LOOP;

    -- Dirección residencial (opcional): {"direccion": {"calle": "...", "id_corregimiento": 5}}
    IF p_datos ? 'direccion' THEN
        v_datos_dir := p_datos -> 'direccion';
        IF jsonb_typeof(v_datos_dir) <> 'object' THEN
            RAISE EXCEPTION 'La dirección debe ser un objeto JSON';
        END IF;
        FOR v_campo IN SELECT jsonb_object_keys(v_datos_dir) LOOP
            IF NOT (v_campo = ANY (v_permitidos_dir)) THEN
                RAISE EXCEPTION 'El campo de dirección % no puede actualizarse', v_campo;
            END IF;
        END LOOP;

        v_dir := jsonb_populate_record(NULL::direccion, v_datos_dir);
        IF v_dir.id_corregimiento IS NOT NULL
           AND NOT EXISTS (SELECT 1 FROM corregimiento WHERE id_corregimiento = v_dir.id_corregimiento) THEN
            RAISE EXCEPTION 'El corregimiento % no existe', v_dir.id_corregimiento;
        END IF;

        v_id_direccion := v_medico.id_direccion;
        IF v_id_direccion IS NULL THEN
            INSERT INTO direccion DEFAULT VALUES RETURNING id_direccion INTO v_id_direccion;
            UPDATE medico SET id_direccion = v_id_direccion WHERE id_medico = p_id_medico;
        END IF;

        FOR v_campo IN SELECT jsonb_object_keys(v_datos_dir) LOOP
            EXECUTE format('UPDATE direccion SET %I = ($1).%I WHERE id_direccion = $2', v_campo, v_campo)
              USING v_dir, v_id_direccion;
        END LOOP;

        -- Provincia y distrito se derivan del corregimiento.
        IF v_datos_dir ? 'id_corregimiento' THEN
            UPDATE direccion di
               SET id_distrito  = d.id_distrito,
                   id_provincia = d.id_provincia
              FROM corregimiento c
              JOIN distrito d ON d.id_distrito = c.id_distrito
             WHERE c.id_corregimiento = di.id_corregimiento
               AND di.id_direccion = v_id_direccion;
            IF v_dir.id_corregimiento IS NULL THEN
                UPDATE direccion SET id_distrito = NULL, id_provincia = NULL
                 WHERE id_direccion = v_id_direccion;
            END IF;
        END IF;
    END IF;

    INSERT INTO auditoria (id_usuario, id_rol, accion, entidad, id_registro, fecha_hora, descripcion)
    SELECT u.id_usuario, u.id_rol, 'ACTUALIZAR_MEDICO', 'MEDICO', p_id_medico, now(),
           'Campos actualizados: ' || (SELECT string_agg(k, ', ' ORDER BY k) FROM jsonb_object_keys(p_datos) AS k)
      FROM usuario u
     WHERE u.id_usuario = p_id_administrador;

    RETURN true;
END;
$$;