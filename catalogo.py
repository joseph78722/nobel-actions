import argparse
import csv
import html
import json
import os
from pathlib import Path

CATEGORIAS = {"Química", "Física", "Medicina", "Literatura", "Paz", "Ciencias Económicas"}


def cargar(ruta):
    ediciones = {}
    with ruta.open(newline="", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        if lector.fieldnames != ["anio", "categoria", "premiados"]:
            raise ValueError(f"{ruta}: encabezados incorrectos")
        for fila in lector:
            anio, categoria, premiados = (fila[c] for c in lector.fieldnames)
            if (None in fila or anio not in {"2023", "2024", "2025"}
                    or categoria not in CATEGORIAS or not (premiados or "").strip()):
                raise ValueError(f"{ruta}, línea {lector.line_num}: año, categoría o premiados inválidos")
            premios = ediciones.setdefault(anio, {})
            if categoria in premios:
                raise ValueError(f"{ruta}, línea {lector.line_num}: categoría repetida")
            premios[categoria] = premiados
    for anio in ("2023", "2024", "2025"):
        if set(ediciones.get(anio, {})) != CATEGORIAS:
            raise ValueError(f"{ruta}: categorías incompletas para {anio}")
    return ediciones


def generar(anio, premios):
    carpeta = Path("public")
    carpeta.mkdir(exist_ok=True)
    commit = os.environ.get("GITHUB_SHA", "local")
    (carpeta / "commit.txt").write_text(commit + "\n", encoding="utf-8")
    (carpeta / "premios.json").write_text(
        json.dumps({"anio": anio, "premios": premios}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lista = "".join(
        f"<dt>{html.escape(categoria)}</dt><dd>{html.escape(nombres)}</dd>"
        for categoria, nombres in sorted(premios.items())
    )
    (carpeta / "index.html").write_text(
        f"""<!doctype html>
<html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Premios Nobel · {anio}</title>
<main><h1>Premios Nobel · {anio}</h1><dl>{lista}</dl>
<p><a href="premios.json">Catálogo en JSON</a></p>
<p>Commit <code>{html.escape(commit)}</code></p>
<p><a href="https://www.nobelprize.org/about/developer-zone-2/">Fuente: NobelPrize.org</a></p>
</main></html>""",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("modo", choices=["validar", "generar"])
    modo = parser.parse_args().modo
    try:
        ediciones = cargar(Path("datos/premios.csv"))
        anio = Path("datos/anio.txt").read_text(encoding="utf-8").strip()
        if anio not in ediciones:
            raise ValueError("datos/anio.txt debe contener 2023, 2024 o 2025")
        if modo == "generar":
            generar(anio, ediciones[anio])
        print(f"{anio}: {len(ediciones[anio])} categorías")
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()