# Theme: paleta, espaciados, composición e iconos

`theme.bin` es un JSON (u32 de largo + JSON compacto) con tres partes, todas
opcionales salvo alguna paleta:

```json
{
  "accent": "#008000", "...18 tokens...": "...",
  "spacing": { "details.block_gap": 16 },
  "layout":  { "startup": "home", "tabs": [...], "home": {...},
               "library": {...}, "discover": {...}, "details": {...} }
}
```

Todo lo que el documento omite **baja al look builtin**: un tema puede ser
solo paleta. El builtin claro es el "Por defecto"; el oscuro se llama
**Default-Dark**; ambos viven en la app.

## Paleta (los 18 tokens)

| token         | uso                                   |
|---------------|---------------------------------------|
| `accent`      | botones primarios, títulos de sección, estrellas llenas |
| `title`       | texto principal                       |
| `content`     | texto secundario                      |
| `read`        | filas ya leídas                       |
| `white`       | **el fondo del app**                  |
| `black`       | negro puro                            |
| `soft`        | texto sobre el acento / perillas      |
| `bar_bg`      | barra de pestañas inferior            |
| `tabs_bg`     | fondo de la franja de pestañas        |
| `top_bar`     | barras de lector y detalles           |
| `card`        | caja de búsqueda, botón seguir        |
| `filled`      | botones sólidos secundarios           |
| `border`      | bordes de botones/contornos           |
| `hairline`    | líneas de separación finas            |
| `divider`     | separadores                           |
| `placeholder` | portada fantasma antes de cargar      |
| `link`        | enlaces en comentarios                |
| `dim`         | switches apagados                     |

Formato `#RRGGBB` o `#AARRGGBB`. En un tema oscuro, `white` **es el fondo**
(negro) — el claro neutro de encima vive en `soft`.

## `spacing` (dp, enteros)

`details.block_gap`, `details.button_gap`, `details.desc_gap`,
`details.rec_gap`, `search.button_gap`. Los valores locos o desconocidos
bajan al builtin; las medidas de las piezas **no** son del tema, solo los
huecos entre ellas.

## `layout`

### El tablero de pestañas (2–5 slots)

```json
"startup": "home",
"tabs": [ {"panel": "library"}, {"panel": "home"},
          {"panel": "discover"}, {"panel": "yo"} ]
```

- `panel`: `home` | `library` | `discover` | `yo`. **Ninguno es
  obligatorio** (puedes armar el tablero que quieras); si el tema olvida
  `yo`, entra solo al final (el manejador de extensiones tiene que quedar
  alcanzable).
- `label`: opcional, la clave L10n del texto (si falta, usa la del panel).
- `startup`: panel inicial; sin él abre el **primer slot**.

### El Home por slots

```json
"home": { "order": [
    {"id": "home.latest",  "layout": "grid_3"},
    {"id": "home.original", "layout": "carousel_big", "loop": true}
] }
```

- Cada entrada = **contenido + carrusel propio**; las repeticiones son
  válidas (la misma sección dos veces con formas distintas).
- `id`: la variable de la sección del provider (`home.<id>`). Id
  desconocido: la entrada cae, el resto vive.
- `layout`: `carousel_big` | `featured` | `grid_3` | `grid_2` (atajos:
  `carousel`, `grid`, `grid2`, `grid3`). Sin `layout` manda el que el
  provider declaró. **`featured` tiene loop activo por defecto**; solo
  `"loop": false` explícito lo apaga. El loop es palabra del tema: el
  provider no decide nunca.

### Las pantallas de lista

```json
"library":  { "order": ["search", "tabs", "list"], "list": "list" },
"discover": { "order": ["search", "tabs", "list"] }
```

- `order`: la pila de componentes, en el orden que quieras (`search`,
  `tabs`, `list` — la lista siempre última). El builtin de Mis mangas hoy
  es `["tabs", "list", "search"]` (la búsqueda vive abajo).
- `list` (solo library): `"list"` (el diseño propio) o `"catalog"`
  (reutiliza la fila de Descubre).

### Detalles

```json
"details": {
  "flow": ["buttons", "tabs"],
  "tabs": { "detail": ["header", "description", "recs"],
            "chapter": [], "comment": [] }
}
```

- `flow`: los bloques fijos, en orden. Tokens: `header`, `buttons`,
  `tabs` (la franja; una sola).
- `tabs.<page>`: los bloques libres de cada página, en orden. Tokens:
  `header`, `buttons`, `description`, `recs`. Cada bloque libre se coloca
  **exactamente una vez** entre el flow y las páginas; cualquier esquema
  inválido baja el tema entero al builtin.

## Iconos (`icons/<nombre>.png`)

Un PNG por icono, nombrado como el sprite (ver la tabla completa en
`docs/herramientas.md`). Cualquier tamaño funciona: el app escala al
pedido de cada sitio. El **tint** se aplica igual que al arte builtin:

- tint ≠ 0: reemplaza los colores y conserva la **alpha** de la forma.
  Si el PNG es un disco blanco con glifo, el blanco se descarta primero
  (la regla "disco") para que el tint se vea como el nativo; un glifo
  directo toma el tint entero.
- tint = 0: el PNG pinta sus colores propios.

Eso te da dos estilos: **arte que hereda el color del tema** (silueta
gris/alpha, se tiñe con el acento) o **arte de colores fijos** (el PNG
trae su paleta; los sitios que tiñen reciben tints de 0 por arte
propio — p. ej. las estrellas).

## Empaquetado

```sh
tools/build_theme.py --name "Mi tema" theme.json --icons ./icons \
    -o mitema.necroext
```
