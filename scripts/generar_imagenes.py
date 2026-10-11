"""Convierte cada publicación de contenido/*.json en una imagen JPEG de 1080x1350.

Uso:
    python scripts/generar_imagenes.py            # genera todas
    python scripts/generar_imagenes.py ID ...     # solo esas publicaciones
"""
import os
import sys

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from playwright.sync_api import sync_playwright

from comun import IMAGENES, MARCA, PLANTILLAS, leer_config, todas_las_publicaciones


def main(ids):
    config = leer_config()
    entorno = Environment(loader=FileSystemLoader(PLANTILLAS), undefined=StrictUndefined, autoescape=True)
    IMAGENES.mkdir(exist_ok=True)

    pendientes = [p for _, _, p in todas_las_publicaciones() if not ids or p["id"] in ids]
    if not pendientes:
        print("No hay publicaciones para generar.")
        return

    opciones = {}
    if os.environ.get("CHROMIUM_PATH"):
        opciones["executable_path"] = os.environ["CHROMIUM_PATH"]

    with sync_playwright() as p:
        navegador = p.chromium.launch(**opciones)
        pagina = navegador.new_page(viewport={"width": 1080, "height": 1350})
        for pub in pendientes:
            plantilla = entorno.get_template(f"{pub['plantilla']}.html")
            html = plantilla.render(config=config, marca=MARCA.as_uri(), **pub.get("datos", {}))
            temporal = PLANTILLAS / f"_tmp_{pub['id']}.html"
            temporal.write_text(html, encoding="utf-8")
            try:
                pagina.goto(temporal.as_uri(), wait_until="networkidle", timeout=30000)
                pagina.evaluate("document.fonts.ready")
                destino = IMAGENES / f"{pub['id']}.jpg"
                pagina.screenshot(path=str(destino), type="jpeg", quality=92, full_page=False)
                print(f"Imagen lista: {destino.relative_to(IMAGENES.parent)}")
            finally:
                temporal.unlink(missing_ok=True)
        navegador.close()


if __name__ == "__main__":
    main(set(sys.argv[1:]))
