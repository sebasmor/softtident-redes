"""Funciones compartidas: rutas del proyecto y lectura del contenido."""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONTENIDO = RAIZ / "contenido"
IMAGENES = RAIZ / "imagenes"
PLANTILLAS = RAIZ / "plantillas"
MARCA = RAIZ / "marca"


def leer_config():
    return json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))


def archivos_de_contenido():
    return sorted(CONTENIDO.glob("*.json"))


def leer(archivo):
    return json.loads(archivo.read_text(encoding="utf-8"))


def guardar(archivo, datos):
    archivo.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def todas_las_publicaciones():
    """Devuelve (archivo, datos_del_archivo, publicacion) para cada publicación."""
    for archivo in archivos_de_contenido():
        datos = leer(archivo)
        for pub in datos.get("publicaciones", []):
            yield archivo, datos, pub
