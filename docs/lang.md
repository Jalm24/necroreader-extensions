# Lang: traducciones de la interfaz

Todo texto visible del app pasa por `L10n.t(clave, fallback)` — el idioma
es un tema de **claves**, no de textos incrustados. Un pack de idioma
(`type: "lang"`) lleva **un `.bin` por código de idioma**, nombrado con el
código: `es.bin`, `en.bin`, …

## Formato de la tabla

Cada `.bin` es un JSON (u32 de largo + JSON compacto):

```json
{ "tab.home": "Inicio", "tabs.following": "SIGUIENTE", "...": "..." }
```

- Las claves que faltan **no rompen nada**: el builtin de ese idioma
  responde (el fallback del código llama). Un pack traduce un subconjunto
  si quiere.
- El idioma del app y el pack activo se eligen en la pantalla "Yo"; un
  pack puede declarar varios idiomas (una entrada por código).

## Cómo obtener la lista de claves

`tools/sweep_l10n.py` recorre el código del app y vuelca el inventario de
claves con sus textos builtin — la base de trabajo de una traducción:

```sh
tools/sweep_l10n.py            # vuelca la tabla completa a stdout
```

Traduce los valores que quieras y guarda el resultado como `<code>.json`;
el empaquetador lo convierte.

## Reglas de oro

1. **Los encabezados del Home también son claves**: `home.section.<id>` —
   el texto de la sección lo pinta el pack de idioma, el provider solo
   manda el id. Si tu provider declara una sección sin clave, el lector
   muestra el id crudo (honrado, depurable).
2. Las variables del behaviors nunca llevan texto de usuario.
3. Los packs de idioma y los de tema son extensiones separadas — un
   `bundle` puede distribuirlos juntos.

## Empaquetado

```sh
tools/build_langpack.py --name "Mi idioma" --author "Yo" \
    es:mi_es.json en:mi_en.json -o miidioma.necroext
```
