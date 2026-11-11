# Bundle: varios packs en un archivo

Un `bundle` (`type: "bundle"`) es un sobre de **distribución**: un zip
(`.necroext`) que lleva otros `.necroext` dentro. El instalador abre el
sobre e instala cada pack interior como **extensión independiente** (con
su propio manifest, id y tipo); el bundle en sí nunca se guarda.

```sh
tools/build_bundle.py --name "Mi pack" --id mipack \
    tema.necroext lang.necroext -o mipack.necroext
```

Usos típicos:

- Entregar **tema + idioma** juntos (van de la mano: la estética y las
  palabras).
- Repartir una familia de temas.

Reglas:

- Los packs interiores conservan su manifest: cada uno instala y se
  actualiza por su propio id.
- El bundle lleva su propio `manifest.bin` (type `bundle`), pero el
  instalador solo lo usa para mostrar el sobre; el staging es de los
  interiores.
- Si un interior falla la validación, se instala el resto y el error
  nombra al fallado.
