# eip-peltomappi

## Ohjeistuksen kehittäminen

Ohjeistusta voi kehittää lokaalisti seuraavasti.

### MkDocs virtuaaliympäristön kanssa

1. Luo Python-virtuaaliympäristö:

```shell
python -m venv .venv
```

2. Aktivoi virtuaaliympäristö.

Windows:

```shell
.\.venv\Scripts\activate
```

Linux/macOS:

```shell
source ./.venv/bin/activate
```

3. Asenna MkDocs virtuaaliympäristöön:

```shell
pip install -r requirements.txt
```

Kun virtuaaliympäristö on luotu ja asennus tehty, seuraavan kerran kun aloitat
kehityksen ainoastaan kohta 2 täytyy toistaa (virtuaaliympäristön aktivointi).

### MkDocs ilman virtuaaliympäristöä

Asenna MkDocs:

```shell
pip install mkdocs
```

### MkDocs

Käynnistä palvelin samassa kansiossa, jossa tiedosto `mkdocs.yml` sijaitsee:

```shell
mkdocs serve
```

Sivut näkyvät selaimessa osoitteessa `http://127.0.0.1:8000` tai `localhost:8000`.

Sivut voi myös kääntää:

```shell
mkdocs build
```

Tällöin sivut löytyy `site` kansiosta, josta voit myös avata ne selaimeen.
