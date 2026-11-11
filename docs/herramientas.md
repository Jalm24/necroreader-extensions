# Herramientas

Todo vive en `tools/` (Python 3, solo stdlib). Todos los empaquetadores
comparten `extpack.py` (el manifest, el contenedor y su validación) y
releen lo que escriben antes de declarar `ok`.

## `extpack.py` — la base (biblioteca, no CLI)

- `manifest_bin(type, id, name, version, author, languages)`: un
  `manifest.bin` byte-exacto con el parser del instalador.
- `parse_manifest(bytes)`: lo lee igual que el C++ y rechaza cualquier
  atajo que el instalador rechazaría.
- `sized_json(texto)`: el sobre u32+JSON que usan `behaviors.bin`,
  `theme.bin` y los idiomas.
- `build_container(path, entries)`: escribe el zip reproducible (orden
  estable).

## `build_provider.py`

```sh
tools/build_provider.py --name "Mi fuente" \
    [--author X] [--version 1.0.0] [--id mifuente] [--icon icon.png] \
    [--bases https://api.example.com/v1/] \
    behaviors.json -o mifuente.necroext
```

- Valida los ids de las secciones del Home y **quita el texto de
  interfaz** (`title` de las secciones, `action` no-token).
- Compacta y ordena el JSON (salida reproducible).

## `build_theme.py`

```sh
tools/build_theme.py --name "Mi tema" theme.json \
    [--icons ./icons] -o mitema.necroext
```

- `theme.json`: paleta (tokens top-level) + `spacing` + `layout`.
- `--icons`: carpeta de PNGs; cada uno entra como `icons/<nombre>.png`.

## `build_langpack.py`

```sh
tools/build_langpack.py --name "Mi idioma" es:mi_es.json en:mi_en.json \
    -o miidioma.necroext
```

Cada argumento `CODE:FILE` es la tabla de ese idioma.

## `build_bundle.py`

```sh
tools/build_bundle.py --name "Mi pack" --id mipack \
    tema.necroext lang.necroext -o mipack.necroext
```

## `sweep_l10n.py`

```sh
tools/sweep_l10n.py
```

Recorre el código del lector y vuelca el inventario de claves L10n con
sus textos builtin — el punto de partida de cualquier traducción.
(Corre dentro del árbol del lector; espera encontrar las fuentes
junto a él.)

## Instalación y prueba en el device

1. Copia el `.necroext` a la tarjeta SD (p. ej. `/sdcard/Download/`).
2. En el app: **Yo → Manejar Extensiones → [+]** y elige el archivo.
3. Los temas se activan en la sección **Temas** (radio; se aplica al
   reiniciar). Los providers se activan en **Proveedores**. Los idiomas
   en la pantalla Yo.

## Los nombres de los iconos (para overrides de tema)

Estos son los sprites builtin, por nombre de archivo PNG
(`rating_*` son 24px de origen; el resto 32 — cualquier tamaño de PNG
funciona, el app escala):

```
ic_arrow_back_light   ic_menu_more          ic_web                ic_comment_white
ic_menu_download_white ic_read_previous     ic_read_next          ic_picture
ic_sent               ic_read_tab_chapter   ic_read_tab_setting   ic_read_tab_rotate
ic_read_tab_brightness ic_auto_scroll       ic_auto_scroll_checked ic_read_ttob
ic_read_ltor          ic_read_rtol          ic_read_ttob_light    ic_read_ltor_light
ic_read_rtol_light    ic_sub_light          ic_add_light          ic_sub_speed
ic_add_speed          ic_read_detail        ic_read_share         ic_read_feedback
ic_chapter_to_reading ic_chapter_to_end     ic_chapter_to_top     ic_menu_sort_asc
ic_menu_sort_desc     ic_tab_home           ic_tab_bookshelf      ic_tab_discover
ic_tab_me             rating_bright         rating_dark           ic_search
```

Dónde se usan los del lector: `ic_read_*` y `ic_auto_scroll*` en las
barras del lector; `ic_chapter_to_*` e `ic_menu_sort_*` en la lista de
capítulos; `rating_*` son las estrellas del puntaje (el tema con arte
propio de estrellas recibe tints de 0: sus colores mandan).
