CREATE OR REPLACE FUNCTION registrar_medico(
    p_numero_idoneidad       text,
    p_numero_registro_medico text,
    p_cedula                 text,
    p_primer_nombre          text,
    p_apellido_paterno       text,
    p_fecha_nacimiento       date,
    p_segundo_nombre         text DEFAULT NULL,
    p_apellido_materno       text DEFAULT NULL,
    p_telefono_residencial   text DEFAULT NULL,
    p_celular                text DEFAULT NULL,
    p_email_personal         text DEFAULT NULL,
    p_foto                   text DEFAULT NULL,
    p_apartado_postal        text DEFAULT NULL,
    p_calle                  text DEFAULT NULL,
    p_edificio               text DEFAULT NULL,
    p_numero_direccion       text DEFAULT NULL,
    p_id_corregimiento       integer DEFAULT NULL
)
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    v_idoneidad    text := btrim(p_numero_idoneidad);
    v_registro     text := btrim(p_numero_registro_medico);
    v_cedula       text := btrim(p_cedula);
    v_id_provincia integer;
    v_id_distrito  integer;
    v_id_direccion integer;
    v_id_medico    integer;
BEGIN
    IF coalesce(v_idoneidad, '') = '' THEN
        RAISE EXCEPTION 'El número de idoneidad es obligatorio';
    END IF;
    IF coalesce(v_registro, '') = '' THEN
        RAISE EXCEPTION 'El número de registro médico es obligatorio';
    END IF;
    IF coalesce(v_cedula, '') = '' THEN
        RAISE EXCEPTION 'La cédula es obligatoria';
    END IF;
    IF coalesce(btrim(p_primer_nombre), '') = '' OR coalesce(btrim(p_apellido_paterno), '') = '' THEN
        RAISE EXCEPTION 'El primer nombre y el apellido paterno son obligatorios';
    END IF;
    IF p_fecha_nacimiento IS NULL OR p_fecha_nacimiento > CURRENT_DATE THEN
        RAISE EXCEPTION 'La fecha de nacimiento es obligatoria y no puede ser futura';
    END IF;

    IF EXISTS (SELECT 1 FROM medico WHERE numero_idoneidad = v_idoneidad) THEN
        RAISE EXCEPTION 'Ya existe un médico con el número de idoneidad %', v_idoneidad;
    END IF;
    IF EXISTS (SELECT 1 FROM medico WHERE numero_registro_medico = v_registro) THEN
        RAISE EXCEPTION 'Ya existe un médico con el número de registro médico %', v_registro;
    END IF;
    IF EXISTS (SELECT 1 FROM medico WHERE cedula = v_cedula) THEN
        RAISE EXCEPTION 'Ya existe un médico con la cédula %', v_cedula;
    END IF;

    -- Provincia y distrito se derivan del corregimiento.
    IF p_id_corregimiento IS NOT NULL THEN
        SELECT d.id_provincia, c.id_distrito
          INTO v_id_provincia, v_id_distrito
          FROM corregimiento c
          JOIN distrito d ON d.id_distrito = c.id_distrito
         WHERE c.id_corregimiento = p_id_corregimiento;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'El corregimiento % no existe', p_id_corregimiento;
        END IF;
    END IF;

    -- La dirección es opcional: solo se crea si llega algún dato.
    IF p_apartado_postal IS NOT NULL OR p_calle IS NOT NULL OR p_edificio IS NOT NULL
       OR p_numero_direccion IS NOT NULL OR p_id_corregimiento IS NOT NULL THEN
        INSERT INTO direccion (apartado_postal, calle, edificio, numero_direccion,
                               id_provincia, id_distrito, id_corregimiento)
        VALUES (p_apartado_postal, p_calle, p_edificio, p_numero_direccion,
                v_id_provincia, v_id_distrito, p_id_corregimiento)
        RETURNING id_direccion INTO v_id_direccion;
    END IF;

    INSERT INTO medico (numero_idoneidad, numero_registro_medico, cedula,
                        primer_nombre, segundo_nombre, apellido_paterno, apellido_materno,
                        foto, fecha_nacimiento, telefono_residencial, celular,
                        email_personal, id_direccion)
    VALUES (v_idoneidad, v_registro, v_cedula,
            btrim(p_primer_nombre), btrim(p_segundo_nombre), btrim(p_apellido_paterno), btrim(p_apellido_materno),
            p_foto, p_fecha_nacimiento, p_telefono_residencial, p_celular,
            p_email_personal, v_id_direccion)
    RETURNING id_medico INTO v_id_medico;

    RETURN v_id_medico;
END;
$$;