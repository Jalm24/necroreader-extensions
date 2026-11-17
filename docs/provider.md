# Provider: the `behaviors` contract

A provider declares **variables and steps**, never interface text. The
behaviors JSON (`behaviors.bin` = u32 length + compact JSON) has five
top-level keys:

```json
{
  "config":   { "...": "..." },   // bases, headers, default_body, constants
  "setup":    [ "..." ],          // named steps that run once
  "actions":  { "...": "..." },   // one entry per core action
  "mappers":  { "...": "..." },   // response fields -> manga/chapter fields
  "follows":  { "...": "..." }    // (optional) the server-side shelf
}
```

## Folder layout

```
my-provider/
  manifest.json      {"type": "provider", "id": "my-provider", ...}
  behaviors.json
  assets/            optional; icon.png is the manager row icon
```

```sh
python3 tools/necroext.py build my-provider -o dist/
```

The packer validates section ids, strips interface text and checks the
installer's size limits. See [`tools.md`](tools.md).

## `config`

```json
"config": {
  "bases":   { "api": "https://api.example.com/v1/", "default": "..." },
  "headers": { "Content-Type": "application/json; charset=UTF-8" },
  "default_body": { "lang": "{{lang}}" },
  "constants": { "appId": "..." }
}
```

- `bases`: names that steps refer to with `"base": "api"`.
- `default_body`: fields sent in **every** POST (a step may add or
  overwrite them).
- `constants`: fixed values referenced as `{{constants.appId}}`.

## `setup`

A list of named blocks (`"name"`) that run **once per session**. An action
requires them with `"requires": ["ensure_config"]`. Each block is a miniature
action (`requires` + `steps`).

## `actions`

One per core action. Each carries `requires` (setup names) and `steps` (the
sequence). The action's result is whatever the last parse step leaves in the
context.

| Action | Variables it receives | Produces |
|--------|-----------------------|----------|
| `get_home` | `{{articleNum}} {{cmtNum}}` | the Home sections |
| `get_feed` | `{{type}}` ("hot"/"latest"/"for_you"), `{{page}}` | manga list |
| `search` | `{{keyword}} {{page}}` | manga list |
| `get_manga_details` | `{{mangaId}}` | a full manga |
| `get_chapters` | `{{mangaId}}` | chapter list |
| `get_chapter_pages` | `{{chapterId}}` `{{pageIndex}}` | page list |
| `get_recommendations` | `{{mangaId}} {{num}}` | manga list |
| `get_catalog` | `{{page}}` | manga list |

## Step types

| `type` | Keys | What it does |
|--------|------|--------------|
| `http_post` / `http_get` | `base`, `path`, `body`, `on_error`, `headers` | the network request; the body accepts objects or a JSON string; `{{...}}` is rendered |
| `parse_list` | `root`, `using_mapper`, `mapping` | a JSON list → manga/chapter/page rows |
| `parse_object` | `root`, `using_mapper`, `mapping` | a JSON object → one manga |
| `parse_home_sections` | `sections` | the Home sections (below) |
| `extract_state` | `mapping` | response fields → state (`{{state.name}}`) |
| `switch` | `expression`, `cases`, `default`, `store_as` | picks a value and stores it in state |
| `account_store` | `mapping` | fields → the shelf account |

- `root` accepts a string or a list of fallback paths (`["info", "$root"]`).
- A per-field `mapping` accepts a string or a list of candidates
  (`"coverUrl": ["cover", "pic_path", "thumb"]`).
- `on_error: "continue"` lets the load go on if the step fails.

## `mappers`

The field dictionary. `manga_item` is the standard:

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

Manga fields: `id title coverUrl description author category lastChapter
rate`. Chapter fields: `id number title url date shortLabel isNew`. Page
fields: `imageUrl width height index`.

## Home sections (`parse_home_sections`)

```json
{ "type": "parse_home_sections", "sections": [
    { "id": "original", "layout": "carousel_big", "source": "og_book",
      "fallback": { "path": "...", "method": "post", "body": {...}, "root": "list" } }
] }
```

- `id`: a **variable**, not text. The interface paints its header with
  `L10n.t("home.section." + id)`; a provider that sends `title` sees the
  packer drop it.
- `layout`: the section's **default** (`carousel_big`, `featured`, `grid_3`,
  `grid_2`). The theme wins: its composition and `loop` decide; this is only
  the fallback when the theme does not pin the slot.
- `loop`: legacy — the reader ignores it today (loop is the theme's word);
  leave it out.
- `source`: response path(s) where the list lives (a string or a list of
  fallbacks).
- `request` (optional): when the section needs its own request, it carries
  `base`/`path`/`body`/`method`; otherwise it shares the previous step's
  response.
- `fallback` (optional): a reserve request when `source` yields no rows.

## Variables and expressions

- From the request: `{{page}}`, `{{keyword}}`, `{{mangaId}}`,
  `{{chapterId}}`, `{{pageIndex}}`, `{{num}}`, `{{type}}`, `{{articleNum}}`,
  `{{cmtNum}}`.
- From state: `{{state.name}}` (whatever `extract_state`/`switch` stored).
- From config: `{{constants.x}}`; from the language: `{{lang}}`.
- From the account: `{{account.field}}` (stored by `account_store`).
- Shelf generators: `{{gen.user}}`, `{{gen.email}}`, `{{gen.pass}}`,
  `{{gen.random}}` — per account, not per session.
- Function: `{{md5(text)}}`, for signatures.

## The server-side shelf (`follows`, optional)

Syncs the reader's library with a service account, with no provider UI:

```json
"follows": {
  "account": {
    "register_when_missing": ["user_id", "token"],
    "register": { "requires": ["..."], "steps": [ "..." ,
                   { "type": "account_store", "mapping": {"user_id": "info.user_id"} } ] }
  },
  "add":    { "requires": ["..."], "steps": [ "..." ] },
  "remove": { "requires": ["..."], "steps": [ "..." ] },
  "sync":   { "requires": ["..."], "steps": [ "..." ],
              "rows": { "root": "list", "id": "book_id",
                        "latest": "info.last_chapter_title", "check_time": "check_time" } }
}
```

- `account.register_when_missing`: the fields the account needs; when they
  are missing, `account.register` runs once. The packer requires `register`
  to end in `account_store`.
- `add`/`remove`: run with `{{mangaId}}` loaded.
- `sync.rows`: turns the response into shelf rows (`id`, `latest`,
  `check_time`). `check_time` comes back on the next sync.

The account belongs to **provider and language**: `{{gen.*}}` derives a new
shadow identity per (provider, language); registration does not verify email.
If the server answers error 1001, the reader drops the identity and
registers again.
