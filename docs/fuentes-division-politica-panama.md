# Fuentes de la división política de Panamá

Este documento explica de dónde salen las provincias, distritos y corregimientos que carga
`app/scripts/seed_catalogos.py` y qué decisiones se tomaron. Los datos alimentan los tres
desplegables de dirección (Provincia, Distrito, Corregimiento) del formulario de registro.

## 1. Fuente oficial principal

Instituto Geográfico Nacional Tommy Guardia (IGNTG), de ANATI: *Conjunto de Datos de
Límites Político-Administrativos de la República de Panamá, escala 1:25,000, año 2025*.

- Página actual: <https://ignpanama.anati.gob.pa/division-politica-administrativa/>
- La dirección que indicaba la tarea
  (`ignpanama.anati.gob.pa/index.php/25-cdepartamento/cdepartamentocartografia/268-division-politica-administrativa`)
  ya no existe: el sitio pasó a WordPress y esa ruta redirige a la portada.
- Los archivos están en el SharePoint público de ANATI, carpeta
  `DatosPub/DatosPublicos/Datos-públicos/DPA_2025_CSV`, enlazada desde el ícono «CSV» de esa página.

## 2. Fecha de consulta

3 de noviembre de 2026.

## 3. Versión del conjunto de datos

Según la página: «delimitaciones oficiales de provincias, distritos y corregimientos,
levantados a escala 1:25,000 y actualizados al año 2024, en su versión número 4». Producto
2025, versión 4. La misma página indica: «Se integra la nueva Comarca Naso Tjër Di».

## 4. Archivos descargados

Copias sin cambios en `app/scripts/datos/dpa_2025/`:

| Archivo | Contenido | Filas | SHA-256 |
|---|---|---|---|
| `limi_prov_a.csv` | Polígonos de provincias | 20 | `2ad7b55e59bf6ae9a6eaaa05328b956b9a11e8a397538f85c8d420fd03725e85` |
| `limi_dist_a.csv` | Polígonos de distritos | 94 | `b4fe96a439743d785e9f89d3f0bb632125524b2628c839d9915891cf9199d47e` |
| `limi_corr_a.csv` | Polígonos de corregimientos | 730 | `6b6c15a1f5014cabe42de36061bd23773cdff02d86ed8e139103c7a772d7aeb5` |

Documentos de ANATI que explican esos archivos (carpetas `DPA_2025_METADATOS` y
`DPA_2025_ESPECIFICACIONES` del mismo SharePoint):

| Documento | Dónde | SHA-256 |
|---|---|---|
| Metadatos ISO de la capa de distritos | `dpa_2025/metadatos/Distrito.xml` (copia) | `cb033fe3599477036d267008b5fed67b8fabb4cd54c44124af2b189685b31e17` |
| Metadatos ISO de la capa de corregimientos | `dpa_2025/metadatos/Corregimiento.xml` (copia) | `81e163e2e0e99da8fcab4bf9d97c43c70d3d5363eb20701a6e2b258fb33a30c2` |
| *Metodología para la extracción de un límite político administrativo en una Geodatabase a escala 1:25 000, año 2025* (IGNTG, 2025/07/11) | `DPA_2025_ESPECIFICACIONES/Metodología representacion_DPA2025.pdf` (1,7 MB, no copiado) | `f02205bfd00f817dc21ba15cce57eb2390149dda3b7888c1a77b5cca7f949fef` |

Columnas útiles: `cod_prov`, `nomb_prov`, `cod_dist`, `nomb_dist`, `cod_corr`, `nomb_corr`,
`ley`, `ley_modi`, `gace`, `gace_modi` y `uso`. Las columnas `Shape_Length` y `Shape_Area`
están en el archivo, pero no se cargan. La carpeta también trae los archivos `limi_*_l.csv`
(límites en forma de línea), que no se usan.

**Una unidad aparece en varias filas**: hay una fila por polígono, según la columna `uso`
(«Tierra», «Masa de Agua - Lago», «Masa de Agua - Río»). Por eso hay más filas que
unidades. El seed toma cada código una sola vez y comprueba que su nombre y su unidad
superior no cambien entre filas.

## 5. Cantidades reportadas por la fuente y cantidades en los archivos

| | Página de ANATI | Códigos distintos en el CSV | Cargados en la BD |
|---|---|---|---|
| Primer nivel | «10 provincias» | 13 (10 provincias y 3 comarcas de nivel provincial) | 13 |
| Distritos | «82 distritos» | 83 | 83 |
| Corregimientos | «699 corregimientos» | 699 | 698 |

- **Primer nivel:** la página aclara que «se incluyen las comarcas en sus respectivas
  unidades administrativas». Los códigos 10, 11 y 12 son las comarcas de nivel provincial.
  Por eso hay 13 códigos y no 10.
- **Distritos (resuelto con la fuente):** hay 82 distritos oficiales y un polígono ficticio.
  La Metodología DPA 2025, sección 5.2.2.1, lo dice así: «Cabe destacar que son 82
  distritos oficiales; no obstante, se creó un polígono distrital ficticio en la Comarca
  Kuna Yala para completar el conjunto de datos a nivel del país». Los metadatos lo
  confirman: «existen 83 distritos de los cuales 1 es considerado comarca indígena, y 1 es
  ficticio». El ficticio es `1001 Comarca Kuna Yala`. Naso Tjër Di (`0105`) sí es un
  distrito oficial: es «la comarca indígena» de esa frase. La misma sección explica que
  el listado del INEC de 2022 tenía 81 distritos, y que en 2025 se agregó Naso Tjër Di.
  Por eso son 82 oficiales y 83 registros. Se cargan los 83 (ver 12 sobre el `1001`).
- **Corregimientos (resuelto con la fuente):** la capa numera 699 registros, del
  `010101` (n.º 1) al `130909` (n.º 699), según la Metodología, sección 5.2.1.2. Uno de
  esos 699 es `010501` «Área de la Comarca Naso Tjër Di». La misma sección aclara: «En
  esta actualización, no se agrega la división de corregimientos de la Comarca Naso Tjër
  Di; porque aún no se termina la delimitación en campo, ni se refleja en las gacetas
  oficiales». Por tanto, los corregimientos legales son 698 más los de Naso Tjër Di, que
  aún no están delimitados. Se cargan esos 698.

## 6. Provincias identificadas

| Código | Provincia |
|---|---|
| 01 | Bocas del Toro |
| 02 | Coclé |
| 03 | Colón |
| 04 | Chiriquí |
| 05 | Darién |
| 06 | Herrera |
| 07 | Los Santos |
| 08 | Panamá |
| 09 | Veraguas |
| 13 | Panamá Oeste |

## 7. Comarcas identificadas

| Comarca | Nombre en la fuente | Código | Dónde queda en la BD |
|---|---|---|---|
| Guna Yala | Comarca Kuna Yala | 10 | `provincia` |
| Emberá-Wounaan | Comarca Emberá-Wounaán | 11 | `provincia` |
| Ngäbe-Buglé | Comarca Ngäbe-Buglé | 12 | `provincia` |
| Naso Tjër Di | Comarca Naso Tjër Di | 0105 | `distrito`, dentro de Bocas del Toro (01) |
| Kuna de Madungandí | Comarca Kuna de Madungandi | 080507 | `corregimiento`, dentro de Chepo (0805), Panamá |
| Kuna de Wargandí | Comarca Kuna de Wargandi | 050209 | `corregimiento`, dentro de Pinogana (0502), Darién |

Se conservan los nombres tal como los escribe la fuente: «Kuna Yala» y no «Guna Yala»;
«Madungandi» y «Wargandi» sin tilde. Si el equipo prefiere otra denominación oficial, debe
cambiarla con una decisión documentada. El seed no vuelve a tocar el nombre de una fila que
ya tiene código.

## 8. Clasificación administrativa y cómo se representa

La BD tiene tres tablas encadenadas: `provincia`, luego `distrito` (con `id_provincia`) y
luego `corregimiento` (con `id_distrito`). No tiene columna de categoría. Cada comarca se
guarda en la tabla del nivel que le asigna la fuente oficial, con el código oficial de ese
nivel. No se convirtió ninguna comarca en otra categoría. La palabra «Comarca» del nombre
permite distinguirlas en el formulario.

- **Categoría provincial** (Guna Yala, Emberá-Wounaan, Ngäbe-Buglé): son filas de
  `provincia`, con sus distritos y corregimientos como cualquier provincia.
- **Categoría de distrito** (Naso Tjër Di): es una fila de `distrito` dentro de Bocas del Toro.
  La Ley 188 de 2020 la separó del distrito de Changuinola.
- **Categoría de corregimiento** (Madungandí, Wargandí): son filas de `corregimiento` dentro
  de sus distritos.

Con esto no hizo falta crear tablas nuevas ni cambiar relaciones. El único cambio de
estructura es la columna `codigo` (ver 11).

## 9. Distritos identificados

83 distritos. Sus corregimientos están en `limi_corr_a.csv` (columnas `cod_corr`, `nomb_corr`).

| Código | Provincia o comarca | Distritos | Corregimientos |
|---|---|---|---|
| 01 | Bocas del Toro | 5 | 40 |
| 02 | Coclé | 6 | 53 |
| 03 | Colón | 6 | 43 |
| 04 | Chiriquí | 14 | 105 |
| 05 | Darién | 3 | 26 |
| 06 | Herrera | 7 | 49 |
| 07 | Los Santos | 7 | 81 |
| 08 | Panamá | 6 | 57 |
| 09 | Veraguas | 12 | 105 |
| 10 | Comarca Kuna Yala | 1 | 4 |
| 11 | Comarca Emberá-Wounaán | 2 | 5 |
| 12 | Comarca Ngäbe-Buglé | 9 | 70 |
| 13 | Panamá Oeste | 5 | 60 |
| | **Total** | **83** | **698** |

| Código | Distrito | Provincia o comarca | Corregimientos |
|---|---|---|---|
| 0101 | Bocas del Toro | Bocas del Toro | 6 |
| 0102 | Changuinola | Bocas del Toro | 18 |
| 0103 | Chiriquí Grande | Bocas del Toro | 6 |
| 0104 | Almirante | Bocas del Toro | 10 |
| 0105 | Comarca Naso Tjër Di | Bocas del Toro | 0 |
| 0201 | Aguadulce | Coclé | 8 |
| 0202 | Antón | Coclé | 10 |
| 0203 | La Pintada | Coclé | 7 |
| 0204 | Natá | Coclé | 7 |
| 0205 | Olá | Coclé | 5 |
| 0206 | Penonomé | Coclé | 16 |
| 0301 | Colón | Colón | 15 |
| 0302 | Chagres | Colón | 7 |
| 0303 | Donoso | Colón | 5 |
| 0304 | Portobelo | Colón | 5 |
| 0305 | Santa Isabel | Colón | 8 |
| 0306 | Omar Torrijos Herrera | Colón | 3 |
| 0401 | Alanje | Chiriquí | 9 |
| 0402 | Barú | Chiriquí | 7 |
| 0403 | Boquerón | Chiriquí | 8 |
| 0404 | Boquete | Chiriquí | 6 |
| 0405 | Bugaba | Chiriquí | 13 |
| 0406 | David | Chiriquí | 12 |
| 0407 | Dolega | Chiriquí | 8 |
| 0408 | Gualaca | Chiriquí | 5 |
| 0409 | Remedios | Chiriquí | 5 |
| 0410 | Renacimiento | Chiriquí | 8 |
| 0411 | San Félix | Chiriquí | 5 |
| 0412 | San Lorenzo | Chiriquí | 5 |
| 0413 | Tolé | Chiriquí | 9 |
| 0414 | Tierras Altas | Chiriquí | 5 |
| 0501 | Chepigana | Darién | 10 |
| 0502 | Pinogana | Darién | 9 |
| 0503 | Santa Fe | Darién | 7 |
| 0601 | Chitré | Herrera | 5 |
| 0602 | Las Minas | Herrera | 7 |
| 0603 | Los Pozos | Herrera | 9 |
| 0604 | Ocú | Herrera | 8 |
| 0605 | Parita | Herrera | 7 |
| 0606 | Pesé | Herrera | 8 |
| 0607 | Santa María | Herrera | 5 |
| 0701 | Guararé | Los Santos | 10 |
| 0702 | Las Tablas | Los Santos | 24 |
| 0703 | Los Santos | Los Santos | 15 |
| 0704 | Macaracas | Los Santos | 11 |
| 0705 | Pedasí | Los Santos | 5 |
| 0706 | Pocrí | Los Santos | 5 |
| 0707 | Tonosí | Los Santos | 11 |
| 0802 | Balboa | Panamá | 6 |
| 0805 | Chepo | Panamá | 8 |
| 0806 | Chimán | Panamá | 5 |
| 0808 | Panamá | Panamá | 26 |
| 0810 | San Miguelito | Panamá | 9 |
| 0811 | Taboga | Panamá | 3 |
| 0901 | Atalaya | Veraguas | 5 |
| 0902 | Calobre | Veraguas | 12 |
| 0903 | Cañazas | Veraguas | 8 |
| 0904 | La Mesa | Veraguas | 7 |
| 0905 | Las Palmas | Veraguas | 13 |
| 0906 | Montijo | Veraguas | 8 |
| 0907 | Río de Jesús | Veraguas | 5 |
| 0908 | San Francisco | Veraguas | 6 |
| 0909 | Santa Fe | Veraguas | 8 |
| 0910 | Santiago | Veraguas | 16 |
| 0911 | Soná | Veraguas | 12 |
| 0912 | Mariato | Veraguas | 5 |
| 1001 | Comarca Kuna Yala | Comarca Kuna Yala | 4 |
| 1101 | Cémaco | Comarca Emberá-Wounaán | 3 |
| 1102 | Sambú | Comarca Emberá-Wounaán | 2 |
| 1201 | Besiko | Comarca Ngäbe-Buglé | 8 |
| 1202 | Mironó | Comarca Ngäbe-Buglé | 8 |
| 1203 | Müna | Comarca Ngäbe-Buglé | 16 |
| 1204 | Nole Duima | Comarca Ngäbe-Buglé | 5 |
| 1205 | Ñürüm | Comarca Ngäbe-Buglé | 11 |
| 1206 | Kankintú | Comarca Ngäbe-Buglé | 7 |
| 1207 | Kusapín | Comarca Ngäbe-Buglé | 5 |
| 1208 | Jirondai | Comarca Ngäbe-Buglé | 5 |
| 1209 | Santa Catalina o Calovébora (Bledeshia) | Comarca Ngäbe-Buglé | 5 |
| 1301 | Arraiján | Panamá Oeste | 9 |
| 1303 | Capira | Panamá Oeste | 13 |
| 1304 | Chame | Panamá Oeste | 11 |
| 1307 | La Chorrera | Panamá Oeste | 18 |
| 1309 | San Carlos | Panamá Oeste | 9 |

## 10. Corregimientos identificados

Se cargan 698 corregimientos. La lista completa, con nombres y códigos oficiales, es
`limi_corr_a.csv`, sin el código `010501`. Los nombres se guardan como los escribe la
fuente (tildes, mayúsculas, «ñ», «ä», «ë»). Solo se quitan los espacios repetidos o
sobrantes: por ejemplo, «La Palma» (050101) aparece con dos y con un espacio final
según la fila.

## 11. Códigos oficiales utilizados

Son los de los CSV: `cod_prov` (2 dígitos), `cod_dist` (4) y `cod_corr` (6). Cada código
contiene el de su unidad superior: `080807` es Bella Vista, en el distrito `0808` Panamá,
en la provincia `08` Panamá.

Las tablas no tenían dónde guardarlos. La migración `5d1f0c7a9e42` agrega `codigo` (texto,
opcional, único) a `provincia`, `distrito` y `corregimiento`. **Es un fix de emergencia
hecho por Desarrollo y Base de Datos debe revisarlo.** Hace falta por dos razones:

- **Los nombres se repiten:** hay 59 nombres de corregimiento usados en más de un lugar
  del país. «Bella Vista», por ejemplo, existe en Panamá (`080807`) y en Tolé, Chiriquí
  (`041302`).
- **El código no se puede deducir:** sin él no hay forma estable de saber si una fila ya
  se cargó, ni de conservar el código oficial.

Se guarda como texto para no perder los ceros a la izquierda. Los identificadores internos
(`id_provincia`, etc.) siguen siendo los seriales de siempre y no coinciden con los
códigos.

## 12. Diferencias entre datos legales y cartográficos

### Naso Tjër Di: sus corregimientos siguen pendientes

**Texto de la ley.** Se leyó la Ley 188 de 4 de diciembre de 2020 en la copia digitalizada de
la Asamblea Nacional (Legispan), que reproduce la Gaceta Oficial Digital 29170-A de 7 de
diciembre de 2020:

- URL: <https://s3-legispan.asamblea.gob.pa/legispan/NORMAS/2020/2020/LEY/Administrador%20Legispan_29170-A_2020_12_7_ASAMBLEA%20NACIONAL_188.pdf>
- SHA-256: `79cce8c6138d6ddb5ef5ce44de55710c9209382071cf9d9d724362b132531fea`
- El PDF es un escaneo. El texto se obtuvo por OCR y se cotejó con la imagen de la página 7
  de la Gaceta.

Artículos que definen la división (transcripción literal):

> **Artículo 2.** La comarca Naso Tjër Di tendrá como cabecera a la comunidad de Sieyic en
> la ribera del río Teribe, donde es la sede del rey naso y de su pueblo.
>
> **Artículo 3.** Se crea el corregimiento de San San Drui, que comprende las comunidades de
> San San Drui, Tigra, Alto Solón, Peña Blanca, Loma Bandera y San San; y el corregimiento
> Bonyik, que comprende las comunidades de Rancho Quemado, Bonquin, Sodi, Santa Rosa,
> Tres Piedras, Bonyik y Dos Concejales.
>
> **Artículo 4.** Se crea el distrito especial Naso Tjër Di, que comprende los corregimientos de
> Teribe, San San Drui, Bonyik y Dos Concejales.
>
> **Artículo 32 (transitorio).** Se ordena convocar a la Comisión Nacional sobre Límites
> Político-Administrativos, para que se verifiquen los límites y coordenadas de la comarca
> Naso Tjër Di establecidos en el artículo 1, a fin de determinar los que corresponderán al
> distrito y a los corregimientos creados en los artículos 3 y 4 […]

**Lo que se concluye:**

- **El número de corregimientos no está claro en la propia ley.**
  - El artículo 3 crea **dos**: San San Drui y Bonyik.
  - El artículo 4 dice que el distrito comprende **cuatro**: Teribe, San San Drui, Bonyik y
    Dos Concejales. Sin embargo, según el artículo 3, Dos Concejales es una *comunidad* del
    corregimiento Bonyik. Teribe es el corregimiento de Changuinola del que se segregó la
    comarca, y ya no aparece en la capa de 2025.
  - Los metadatos de ANATI dicen que la comarca «se divide en tres corregimientos, que aún no
    se cargan a la DPA debido a que tiene inconsistencia en sus límites».
  - El perfil de salud de los pueblos originarios del MINSA (2024) habla de tres: Teribe,
    Bonyic y San San Druy.
- **No existen límites ni códigos oficiales.** El artículo 32 encarga la delimitación a la
  Comisión Nacional de Límites. La Metodología de ANATI (sección 5.2.1.2) confirma que
  todavía no se termina. El INEC no le asignó código a ningún corregimiento de la comarca:
  según el informe técnico del Banco Mundial sobre el mapa de pobreza, la comarca no figura
  como unidad aparte en el Censo 2023.

**Decisión: no se cargan.** No hay una lista oficial única de nombres (2, 3 o 4 según la
fuente) ni códigos oficiales.

- **Qué se cargó:** el distrito `0105 Comarca Naso Tjër Di`. No se cargan sus corregimientos
  ni el polígono auxiliar `010501`.
- **Consecuencia en el formulario:** se puede elegir Bocas del Toro → Comarca Naso Tjër Di,
  pero el desplegable de corregimiento queda vacío y deshabilitado. Como el corregimiento es
  obligatorio, **no se puede registrar una dirección dentro de la comarca**. Un médico que
  vive ahí tendría que registrar el corregimiento de Changuinola más cercano, lo que es
  incorrecto.
- **Cómo se resuelve:** cuando ANATI o el INEC publiquen los corregimientos con su código,
  se agregan los CSV nuevos y se vuelve a ejecutar `seed_catalogos`. Si el equipo necesita
  la opción antes, debe decidir explícitamente cargar los nombres de la ley sin código
  oficial (la columna `codigo` admite NULL). Esa decisión debe documentarse aquí.

### Comarca Kuna Yala (distrito `1001`): distrito ficticio, se mantiene como contenedor

**Lo que dice ANATI.** El registro es ficticio. Metodología, sección 5.2.2: «En el caso de la
Comarca Kuna Yala se creó un polígono distrital ficticio en la Comarca Kuna Yala para
completar el conjunto de datos a nivel del país; para no crear un hueco en la representación
de los datos; no obstante, esta comarca no tiene distritos». Los metadatos de la capa de
distritos dicen lo mismo.

**Por qué se mantiene:** contiene los cuatro corregimientos reales de Guna Yala: Narganá
(100101), Ailigandí (100102), Puerto Obaldía (100103) y Tubualá (100104).

- La BD exige un distrito para cada corregimiento (`corregimiento.id_distrito` y
  `direccion.id_distrito` son NOT NULL).
- Sin el `1001` esos cuatro corregimientos no podrían existir ni elegirse.
- Quitarlo también obligaría a borrar un registro ya cargado.

En `seed_catalogos.py` queda identificado en `DISTRITOS_FICTICIOS_CARGADOS`.

**Consecuencia en el formulario:** con la provincia «Comarca Kuna Yala», el desplegable de
distrito ofrece una sola opción con el mismo nombre, y no es un distrito legal.

**Decisión pendiente del equipo.** Las dos alternativas que lo eliminan del formulario
implican cambiar la estructura:

1. Una columna que marque el distrito como contenedor técnico, para que el formulario lo
   seleccione solo y lo oculte. Cambia la BD, el contrato de `/provincias/{id}/distritos`
   y el frontend.
2. Permitir corregimientos sin distrito. Cambia FK NOT NULL, `registrar_medico`,
   `actualizar_medico`, `obtener_perfil_medico` y los filtros.

Mientras no se decida, queda como está.

## 13. Registros que requirieron verificación adicional

| Código | Registro | Resultado |
|---|---|---|
| 010501 | Área de la Comarca Naso Tjër Di | Auxiliar cartográfico; no se carga |
| 0105 | Comarca Naso Tjër Di | Distrito oficial (Ley 188, art. 4); se carga sin corregimientos porque no están delimitados ni codificados (ver 12) |
| 1001 | Comarca Kuna Yala (distrito) | Ficticio según ANATI; se carga solo como contenedor de los 4 corregimientos reales (ver 12) |
| 050101 | La Palma | Mismo nombre con espacios distintos según la fila; se normalizan |
| Polígonos de agua | Filas con `uso` de lago o río | No son unidades distintas: comparten el código de la unidad de tierra |

No se encontraron distritos ni corregimientos que solo existan como polígono de agua, ni
códigos que no contengan el de su unidad superior.

## 14. Criterios para incorporar los registros a la BD

1. **Una fila por código oficial**: no se crean unidades nuevas por las filas de agua.
2. **Nombres de la fuente**: sin traducir ni corregir, salvo los espacios sobrantes.
3. **Unidad superior según la fuente**: el distrito va con su `cod_prov` y el corregimiento
   con su `cod_dist`.
4. **Sin registros auxiliares** como opción seleccionable (lista `CORREGIMIENTOS_AUXILIARES`).
5. **No se inventan registros** para completar cantidades.
6. **Filas ya existentes**:
   - Una fila sin código cuyo nombre coincide, sin tildes ni mayúsculas, dentro de la misma
     unidad superior, se **adopta**: recibe el código y el nombre oficial, una sola vez. Así
     pasó con «Panama» / «Panama» / «Bella Vista» del seed antiguo, que ya usaban dos
     médicos. Se conservaron sus `id` y las direcciones siguieron apuntando a ellas.
   - Una fila con código no se modifica nunca, y nada se borra.
7. **Sin Internet**: el seed lee solo los archivos versionados.

## Fuentes complementarias

- **Ley 188 de 2020** (Gaceta Oficial 29170-A): se leyó la copia de Legispan de la Asamblea
  Nacional (ver 12). La copia del sitio de la Gaceta Oficial no se pudo descargar de forma
  automática.
- **Metodología y metadatos DPA 2025 de ANATI**: explican las cantidades 82/83 y 699/698 y
  los registros ficticio y auxiliar (ver 4 y 5).
- **MINSA**, *Perfil de salud de los territorios indígenas de Panamá* (2024): menciona tres
  corregimientos de Naso Tjër Di. No es una fuente territorial oficial; solo se usó para
  contrastar.
  <https://minsa.gob.pa/sites/default/files/direcciones/panama_perfil_de_salud_de_los_pueblos_originarios_2024.pdf>
- **INEC**: no se encontró un listado de códigos que incluya los corregimientos de Naso Tjër
  Di. Según el informe del Banco Mundial sobre el mapa de pobreza, el Censo 2023 no presenta
  la comarca como unidad aparte.
- La capa de ANATI trae, para cada unidad, la ley y la Gaceta que la crean o modifican
  (columnas `ley`, `ley_modi`, `gace`, `gace_modi`).
