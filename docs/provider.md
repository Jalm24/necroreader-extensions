# Provider: el contrato `behaviors`

Un provider declara **variables y pasos**, nunca texto de interfaz. El JSON
de behaviors (`behaviors.bin` = u32 de largo + JSON compacto) tiene cinco
claves de primer nivel:

```json
{
  "config":   { ... },   // bases, headers, default_body, constants
  "setup":    [ ... ],   // pasos con nombre que corren una vez
  "actions":  { ... },   // una entrada por acción del núcleo
  "mappers":  { ... },   // campos de respuesta -> campos de manga/capítulo
  "follows":  { ... }    // (opcional) el estante del servidor
}
```

## `config`

```json
"config": {
  "bases":   { "api": "https://api.example.com/v1/", "default": "..." },
  "headers": { "Content-Type": "application/json; charset=UTF-8" },
  "default_body": { "lang": "{{lang}}" },
  "constants": { "appId": "..." }
}
```

- `bases`: nombres a los que los pasos se refieren con `"base": "api"`.
- `default_body`: campos que entran en **cada** POST (el paso puede
  añadir o sobreescribir).
- `constants`: valores fijos que referencias como `{{constants.appId}}`.

## `setup`

Lista de bloques con nombre (`"name"`) que se ejecutan **una sola vez** por
sesión. Una acción los exige con `"requires": ["ensure_config"]`. Cada
bloque es una acción en miniatura (`requires` + `steps`).

## `actions`

Una por acción del núcleo. Cada una lleva `requires` (nombres de setup) y
`steps` (la secuencia). La respuesta de la acción es lo que el último paso
de parse deja en el contexto.

| Acción               | Variables que recibe            | Produce                        |
|----------------------|---------------------------------|--------------------------------|
| `get_home`           | `{{articleNum}} {{cmtNum}}`     | secciones del Home             |
| `get_feed`           | `{{type}}` ("hot"/"latest"/"for_you"), `{{page}}` | lista de mangas |
| `search`             | `{{keyword}} {{page}}`          | lista de mangas                |
| `get_manga_details`  | `{{mangaId}}`                   | un manga completo              |
| `get_chapters`       | `{{mangaId}}`                   | lista de capítulos             |
| `get_chapter_pages`  | `{{chapterId}}` `{{pageIndex}}` | lista de páginas               |
| `get_recommendations`| `{{mangaId}} {{num}}`           | lista de mangas                |
| `get_catalog`        | `{{page}}`                      | lista de mangas                |

## Tipos de paso

| `type`               | Claves                          | Qué hace                          |
|----------------------|---------------------------------|-----------------------------------|
| `http_post` / `http_get` | `base`, `path`, `body`, `on_error`, `headers` | el pedido de red; el body acepta objetos o un string JSON; `{{...}}` se renderiza |
| `parse_list`         | `root`, `using_mapper`, `mapping` | una lista JSON -> filas de manga/capítulo/página |
| `parse_object`       | `root`, `using_mapper`, `mapping` | un objeto JSON -> un manga       |
| `parse_home_sections`| `sections`                      | las secciones del Home (abajo)    |
| `extract_state`      | `mapping`                       | campos de la respuesta -> estado (`{{state.nombre}}`) |
| `switch`             | `expression`, `cases`, `default`, `store_as` | elige un valor y lo guarda en estado |
| `account_store`      | `mapping`                       | campos -> la cuenta del estante   |

- `root` acepta string o lista de rutas de reserva (`["info", "$root"]`).
- `mapping` por campo acepta string o lista de candidatos
  (`"coverUrl": ["cover", "pic_path", "thumb"]`).
- `on_error: "continue"` deja que la carga siga si el paso falla.

## `mappers`

El diccionario de campos. `manga_item` es el estándar:

```json
"manga_item": {
  "id": ["id", "book_id"],
  "title": ["name", "title"],
  "coverUrl": ["cover", "pic_path", "thumb"],
  "description": ["intro", "description"],
  "author": "author",
  "category": "category_str",
  "lastChapter": "last_chapter_title",
  "rate": "rate_star"
}
```

Campos de manga: `id title coverUrl description author category
lastChapter rate`. De capítulo: `id number title url date shortLabel
isNew`. De página: `imageUrl width height index`.

## Las secciones del Home (`parse_home_sections`)

```json
{ "type": "parse_home_sections", "sections": [
    { "id": "original", "layout": "carousel_big", "source": "og_book",
      "fallback": { "path": "...", "method": "post", "body": {...}, "root": "list" } }
] }
```

- `id`: **variable**, no texto. La interfaz pinta su encabezado con
  `L10n.t("home.section." + id)`; un provider que manda `title` ve cómo el
  empaquetador se lo quita.
- `layout`: el **predeterminado** de la sección (`carousel_big`,
  `featured`, `grid_3`, `grid_2`). El tema gana: su composición y su
  `loop` mandan; esto solo es el fallback cuando el tema no pina el slot.
- `loop`: histórico — hoy lo ignora el lector (el loop es palabra del
  tema); déjalo fuera.
- `source`: ruta(s) de la respuesta donde vive la lista (string o lista
  de reservas).
- `request` (opcional): si la sección necesita su propio pedido, lleva
  `base`/`path`/`body`/`method`; si no, comparte la respuesta del paso
  anterior.
- `fallback` (opcional): pedido de reserva si `source` no da filas.

## Variables y expresiones

- De petición: `{{page}}`, `{{keyword}}`, `{{mangaId}}`, `{{chapterId}}`,
  `{{pageIndex}}`, `{{num}}`, `{{type}}`, `{{articleNum}}`, `{{cmtNum}}`.
- De estado: `{{state.nombre}}` (lo que guardaron `extract_state`/`switch`).
- De config: `{{constants.x}}`; del idioma: `{{lang}}`.
- De la cuenta: `{{account.campo}}` (lo que guardó `account_store`).
- Generadores del estante: `{{gen.user}}`, `{{gen.email}}`, `{{gen.pass}}`,
  `{{gen.random}}` — valores por cuenta, no por sesión.
- Función: `{{md5(texto)}}` para firmas.

## El estante del servidor (`follows`, opcional)

Sincroniza la biblioteca del lector con una cuenta del servicio, sin
UI del provider:

```json
"follows": {
  "account": {
    "register_when_missing": ["user_id", "token"],
    "register": { "requires": [...], "steps": [ ... http_post de registro ...,
                   { "type": "account_store", "mapping": {"user_id": "info.user_id"} } ] }
  },
  "add":    { "requires": [...], "steps": [ ... alta del manga ... ] },
  "remove": { "requires": [...], "steps": [ ... baja del manga ... ] },
  "sync":   { "requires": [...], "steps": [ ... pedido de la lista ... ],
              "rows": { "root": "list", "id": "book_id",
                        "latest": "info.last_chapter_title", "check_time": "check_time" } }
}
```

- `account.register_when_missing`: los campos que la cuenta necesita; si
  faltan, corre `account.register` (una sola vez). El empaquetador exige
  que `register` termine en `account_store`.
- `add`/`remove`: se corren con `{{mangaId}}` cargado.
- `sync.rows`: convierte la respuesta en filas del estante (`id`,
  `latest`, `check_time`). El `check_time` vuelve en el próximo sync.

La cuenta es **del provider y del idioma**: `{{gen.*}}` genera una
identidad sombra nueva por (provider, idioma); el registro no verifica
correo. Si el servidor responde un error 1001, el lector limpia la
identidad y re-registra.

## Empaquetado

```sh
tools/build_provider.py --name "Mi fuente" --bases https://api.example.com/v1/ \
    behaviors.json -o mifuente.necroext
```

El empaquetador quita los campos de texto de interfaz (`title` de las
secciones, `action` no-token) y valida los ids. `assets/icon.png`
(opcional) es la fila del manejador de extensiones.
