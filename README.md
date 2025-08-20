# eip-peltomappi

## Kehittäminen

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

Asenna [uv-työkalu](https://docs.astral.sh/uv/) projektin hallinnointiin:

```shell
pip install uv
```

Päivitä projektiympäristö (asentaa tarvittavat riippuvuudet):

```shell
uv sync --all-groups
```

Asenna pre-commit hook:

```shell
pre-commit install
```

## Ohjeistuksen kehittäminen

Ennen ohjeistuksen kehittämistä toista ensin [aiemmat komennot](#kehittäminen).
Kun olet toistanut vaiheet kerran, ohjeistusta voi kehittää. Varmista kuitenkin,
että virtuaaliympäristö on aktivoitu.

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
