# El formato `.necroext`

Un `.necroext` es un **zip plano** (el instalador lo abre tal cual) con dos
clases de miembros:

1. `manifest.bin` — obligatorio, siempre primero en importancia: identifica
   la extensión.
2. El payload del tipo: lo que cada tipo exige (ver las páginas de cada uno).

## `manifest.bin`

Binario pequeño, byte-exacto con el parser del instalador:

```
"NECR"                              magic (4 bytes)
u32 versión (1,0,0)                 4 bytes: 01 00 00 00
u32 payloadSize                     little-endian
u32 crc32(payload)
payload:
    u8len  type                     "provider" | "theme" | "lang" | "bundle"
    u8len  id                       [A-Za-z0-9._-]{1,64}, sin punto inicial
    u16len name                     nombre visible
    u16len version                  texto libre ("1.0.0")
    u16len author
    u8     langCount
    (u8len code)*                   códigos de idioma (solo type "lang")
```

Los strings son UTF-8; `u8len` es 1 byte de largo + bytes; `u16len` es
little-endian de 2 bytes + bytes.

No escribas el manifest a mano: **`tools/extpack.py` lo genera y lo
valida** (`manifest_bin()`, `parse_manifest()`), y todos los
empaquetadores del repo lo usan.

## Reglas del instalador (lo que te rechazará)

- `manifest.bin` ausente o con magic/versión/CRC malos → rechazo.
- `id` inválido (vacío, >64, caracteres fuera del set) → rechazo.
- **Tamaño máximo del payload** por binario (behaviors/theme): el
  instalador rechaza bins que lo excedan — mantén el JSON compacto.
- Type `lang`: cada idioma declarado en el manifest **debe** tener su
  `<code>.bin` en el contenedor, y ningún otro `.bin` extra.
- Type `theme`: exige `theme.bin`; los PNGs opcionales viven en `icons/`.
- Type `provider`: exige `behaviors.bin`.
- Type `bundle`: no se instala como tal — el instalador abre el zip y
  instala cada `.necroext` interior como extensión independiente.

## Qué es cada tipo

| Tipo      | Para qué                                    | Payload                  |
|-----------|---------------------------------------------|--------------------------|
| `provider`| una fuente de contenido (API/deublicación)  | `behaviors.bin`          |
| `theme`   | paleta, espaciados, composición e iconos    | `theme.bin` + `icons/`   |
| `lang`    | traducciones de la interfaz                 | `<code>.bin` por idioma  |
| `bundle`  | distribución de varios packs en un archivo  | otros `.necroext`        |

Los tres primeros se instalan como extensiones independientes; el bundle
solo es un sobre de distribución.
