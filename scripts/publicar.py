"""Publica en Instagram las publicaciones aprobadas cuya fecha ya llegó.

Variables de entorno:
    IG_TOKEN            token de acceso de Instagram (obligatorio, salvo en --prueba)
    IMAGENES_BASE_URL   dirección pública de la carpeta imagenes/
                        (en GitHub se calcula sola a partir del repositorio)
    IG_API_VERSION      versión de la API (por defecto v23.0)

Uso:
    python scripts/publicar.py             # publica lo que toca hoy
    python scripts/publicar.py --prueba    # solo muestra qué publicaría
    python scripts/publicar.py --prueba --fecha=2026-10-17
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from comun import IMAGENES, guardar, leer_config, todas_las_publicaciones

API = f"https://graph.instagram.com/{os.environ.get('IG_API_VERSION', 'v23.0')}"
DIAS_DE_GRACIA = 3  # si un sábado falló, lo reintenta hasta 3 días después


def llamar(metodo, ruta, **parametros):
    datos = urllib.parse.urlencode(parametros).encode()
    url = f"{API}/{ruta}"
    if metodo == "GET":
        url, datos = f"{url}?{datos.decode()}", None
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=datos, method=metodo), timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        detalle = e.read().decode(errors="replace")
        raise RuntimeError(f"Instagram respondió {e.code}: {detalle}") from None


def url_de_imagenes():
    if os.environ.get("IMAGENES_BASE_URL"):
        return os.environ["IMAGENES_BASE_URL"].rstrip("/")
    repo = os.environ.get("GITHUB_REPOSITORY")
    rama = os.environ.get("GITHUB_REF_NAME", "main")
    if not repo:
        sys.exit("Falta IMAGENES_BASE_URL (o ejecutar dentro de GitHub Actions).")
    return f"https://raw.githubusercontent.com/{repo}/{rama}/imagenes"


def publicar_una(token, ig_id, imagen_url, texto):
    contenedor = llamar("POST", f"{ig_id}/media", image_url=imagen_url, caption=texto,
                        access_token=token)["id"]
    for _ in range(10):  # Instagram procesa la imagen; se revisa hasta ~5 minutos
        estado = llamar("GET", contenedor, fields="status_code", access_token=token).get("status_code")
        if estado == "FINISHED":
            break
        if estado in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram no pudo procesar la imagen (estado {estado}).")
        time.sleep(30)
    else:
        raise RuntimeError("Instagram tardó demasiado en procesar la imagen.")
    return llamar("POST", f"{ig_id}/media_publish", creation_id=contenedor, access_token=token)["id"]


def main():
    prueba = "--prueba" in sys.argv
    config = leer_config()
    hoy = datetime.now(ZoneInfo(config["zona_horaria"])).date()
    for arg in sys.argv[1:]:
        if arg.startswith("--fecha="):  # para probar: --prueba --fecha=2026-10-17
            hoy = date.fromisoformat(arg.split("=", 1)[1])
    base = url_de_imagenes() if not prueba else os.environ.get("IMAGENES_BASE_URL", "<url-publica>/imagenes")

    tocan = []
    for archivo, datos, pub in todas_las_publicaciones():
        fecha = date.fromisoformat(pub["fecha"])
        if pub.get("publicado") or not pub.get("aprobado"):
            continue
        if fecha <= hoy <= fecha + timedelta(days=DIAS_DE_GRACIA):
            tocan.append((archivo, datos, pub))

    if not tocan:
        print(f"{hoy}: no hay publicaciones aprobadas pendientes para hoy.")
        return

    token = os.environ.get("IG_TOKEN")
    if not prueba and not token:
        sys.exit("Falta IG_TOKEN.")
    ig_id = llamar("GET", "me", fields="user_id,username", access_token=token)["user_id"] if not prueba else "<ig_id>"

    errores = 0
    for archivo, datos, pub in tocan:
        imagen = IMAGENES / f"{pub['id']}.jpg"
        if not imagen.exists():
            print(f"[{pub['id']}] falta la imagen {imagen.name}; ejecuta generar_imagenes.py")
            errores += 1
            continue
        texto = pub["texto_publicacion"]
        if config.get("hashtags"):
            texto += "\n\n" + config["hashtags"]
        url = f"{base}/{imagen.name}"
        if prueba:
            print(f"[PRUEBA] Publicaría {pub['id']} con {url}\n---\n{texto}\n---")
            continue
        try:
            media_id = publicar_una(token, ig_id, url, texto)
        except RuntimeError as e:
            print(f"[{pub['id']}] ERROR: {e}")
            errores += 1
            continue
        pub["publicado"] = {"cuando": datetime.now(ZoneInfo(config["zona_horaria"])).isoformat(timespec="minutes"),
                            "media_id": media_id}
        guardar(archivo, datos)
        print(f"[{pub['id']}] publicado en Instagram (id {media_id}).")

    if errores:
        sys.exit(1)


if __name__ == "__main__":
    main()
