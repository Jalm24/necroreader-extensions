# NecroReader — API de extensiones y herramientas

La documentación y las herramientas para crear extensiones de
[NecroReader](https://github.com/Jalm24/NecroReader): el lector de manga
nativo (C++/Android) donde **el contenido y la estética viven en
extensiones**, no en la app.

La app base no trae providers ni temas de terceros: es una concha con un
proveedor fantasma (un Home de placeholders sin red). Todo lo demás entra
como `.necroext`.

## Los cuatro tipos de extensión

| Tipo | Para qué | Documento |
|------|----------|-----------|
| **provider** | una fuente de contenido (API, scraper declarativo) | [`docs/provider.md`](docs/provider.md) |
| **theme** | paleta, espaciados, composición, iconos | [`docs/theme.md`](docs/theme.md) |
| **lang** | traducciones de la interfaz | [`docs/lang.md`](docs/lang.md) |
| **bundle** | varios packs en un solo archivo | [`docs/bundle.md`](docs/bundle.md) |

El formato del contenedor (`.necroext` = zip + `manifest.bin`) está en
[`docs/formato-necroext.md`](docs/formato-necroext.md).

## Inicio rápido

```sh
# un provider (contra una API ficticia de ejemplo)
tools/build_provider.py --name "Mi fuente" \
    examples/provider-ejemplo/behaviors.json -o mifuente.necroext

# un tema (paleta + composición)
tools/build_theme.py --name "Mi tema" \
    examples/tema-ejemplo/tema.json -o mitema.necroext

# un pack de idioma
tools/build_langpack.py --name "Mi idioma" \
    es:examples/langpack-ejemplo/es.json -o miidioma.necroext

# todos juntos
tools/build_bundle.py --name "Mi pack" tema.necroext miidioma.necroext \
    -o mipack.necroext
```

Copia el `.necroext` a la tarjeta SD e instálalo en
**Yo → Manejar Extensiones → [+]**. Detalles de cada herramienta y los
nombres de los iconos: [`docs/herramientas.md`](docs/herramientas.md).

## Principios del contrato

1. **Los providers mandan variables, nunca texto de interfaz.** Los
   encabezados del Home y los botones los pinta el app con el pack de
   idioma activo; lo que el empaquetador recibe como UI text, lo quita.
2. **Los temas mandan en la estética**: paleta, espaciados, composición
   de cada pantalla y los iconos. El layout del provider es solo el
   fallback cuando el tema no dice nada.
3. **Nada rompe por omitir**: cada cosa que un pack no declara baja al
   look builtin. Un tema de solo paleta es válido; un provider sin
   estante también.
4. **La app base no conoce APIs**: el provider builtin responde todo con
   vacío (el Home de placeholders). Un provider real reemplaza esa vida
   al instalarse.

## Licencia

MIT — ver [`LICENSE`](LICENSE).
