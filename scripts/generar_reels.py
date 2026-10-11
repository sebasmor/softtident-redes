"""Convierte cada publicación de contenido/*.json en un reel MP4 vertical (1080x1920).

El reel son escenas animadas hechas con los mismos `datos` de la publicación, una escena
final con el WhatsApp y el logo animado (marca/logo-animado.mp4) para cerrar.
No lleva música: se elige en Instagram al programarlo. Solo suena el logo al final.

Necesita ffmpeg instalado.

Uso:
    python scripts/generar_reels.py            # los de hoy en adelante que sean nuevos o hayan cambiado
    python scripts/generar_reels.py ID ...     # rehace esas publicaciones sí o sí
"""
import hashlib
import json
import os
import subprocess
import sys
from datetime import date

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup
from playwright.sync_api import sync_playwright

from comun import MARCA, PLANTILLAS, RAIZ, leer_config, todas_las_publicaciones

VIDEOS = RAIZ / "videos"
HUELLAS = VIDEOS / "huellas.json"  # qué versión de cada reel ya está hecha, para no rehacerlo
FPS = 30
ANCHO, ALTO = 1080, 1920
FONDO_LOGO = "0xFEFEFE"  # color de fondo del video del logo
CIERRE = 0.4             # segundos de fundido hacia el logo


def lectura(texto, minimo=2.5, maximo=7.0):
    """Segundos para leer un texto con calma."""
    return round(min(max(len(texto) / 14 + 1.4, minimo), maximo), 2)


def el(clase, contenido, rotulo=None):
    return {"c": clase, "h": contenido, "l": rotulo}


def escena(fondo, dur, els, paso=0.35, alinear=""):
    return {"fondo": fondo, "dur": dur, "els": els, "paso": paso, "alinear": alinear}


def escena_contacto(config, fondo="oscuro"):
    return escena(fondo, 4.0, [
        el("etiqueta", "Agenda tu cita"),
        el("chico", "Escríbenos por WhatsApp"),
        el("numero", config["whatsapp"]),
        el("chico", config["ubicacion"]),
    ], paso=0.3)


def escenas_de(pub, config, marca):
    d = pub.get("datos", {})
    titulo = Markup(d.get("titulo", ""))
    tipo = pub["plantilla"]
    escenas = []

    if tipo == "destacado":
        escenas.append(escena("oscuro", 3.2, [el("etiqueta", d["etiqueta"]), el("titulo", titulo)]))
        escenas.append(escena("oscuro", lectura(d["texto"]), [el("texto grande", d["texto"])]))
        escenas.append(escena_contacto(config))

    elif tipo == "lista":
        escenas.append(escena("palido", 3.2, [el("etiqueta", d.get("etiqueta", "")), el("titulo", titulo)]))
        if d.get("texto"):
            escenas.append(escena("palido", lectura(d["texto"]), [el("texto grande", d["texto"])]))
        puntos = d["puntos"]
        escenas.append(escena("palido", round(1.6 + 1.1 * len(puntos) + 1.2, 2),
                              [el("punto", p) for p in puntos], paso=1.1))
        escenas.append(escena_contacto(config))

    elif tipo == "preguntas":
        escenas.append(escena("blanco", 3.0, [el("titulo", titulo)]))
        for q in d["preguntas"]:
            escenas.append(escena("palido", round(1.5 + lectura(q["r"], 2, 4.5), 2),
                                  [el("pregunta", q["p"]), el("respuesta", q["r"])], paso=1.2))
        escenas.append(escena_contacto(config))

    elif tipo == "presentacion":
        logo = Markup(f'<img src="{marca}/logo-color.png" alt="">')
        escenas.append(escena("blanco", 3.4, [el("logo", logo), el("titulo mediano", titulo)], alinear="centro"))
        escenas.append(escena("palido", round(1.4 + 0.6 * len(config["servicios"]) + 1.2, 2),
                              [el("etiqueta", "Te atendemos en")] + [el("punto", s) for s in config["servicios"]],
                              paso=0.6))
        escenas.append(escena("palido", 6.0, [
            el("dato", config["horario_corto"], "Horario"),
            el("dato", "Sí, también atendemos", "Emergencias"),
            el("dato", config["pagos"], "Pagos"),
            el("dato", "Te damos el precio antes de empezar", "Precio"),
        ], paso=0.7))
        escenas.append(escena_contacto(config))

    else:
        raise ValueError(f"Plantilla sin reel: {tipo}")
    return escenas


CAPA_LOGO = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600&display=swap" rel="stylesheet">
<style>html,body{margin:0;background:transparent}
body{width:1080px;height:1920px;position:relative;font-family:'Montserrat',sans-serif;text-align:center}
.t{position:absolute;left:0;right:0;top:1230px}
.a{font-size:34px;letter-spacing:8px;text-transform:uppercase;color:#4F6A70}
.n{font-size:76px;font-weight:600;color:#046C80;margin-top:16px}</style></head>
<body><div class="t"><div class="a">WhatsApp</div><div class="n">{whatsapp}</div></div></body></html>"""


def hacer_capa_logo(pagina, config, destino):
    """PNG transparente con el WhatsApp, para ponerlo debajo del logo animado."""
    temporal = PLANTILLAS / "_tmp_capa_logo.html"
    temporal.write_text(CAPA_LOGO.replace("{whatsapp}", config["whatsapp"]), encoding="utf-8")
    try:
        pagina.goto(temporal.as_uri(), wait_until="networkidle", timeout=30000)
        pagina.evaluate("document.fonts.ready")
        pagina.screenshot(path=str(destino), omit_background=True)
    finally:
        temporal.unlink(missing_ok=True)


def codificar(pagina, duracion, capa, destino):
    """Captura la animación cuadro por cuadro y la une con el logo animado usando ffmpeg."""
    cuadros = round(duracion * FPS)
    silencio = duracion - CIERRE
    filtro = (
        f"[0:v]format=yuv420p,setsar=1,settb=AVTB[a];"
        f"[1:v]fps={FPS},scale={ANCHO}:-2,pad={ANCHO}:{ALTO}:0:560:color={FONDO_LOGO},setsar=1[l];"
        f"[l][2:v]overlay=0:0:shortest=1,format=yuv420p,settb=AVTB[b];"
        f"[a][b]xfade=transition=fade:duration={CIERRE}:offset={silencio:.3f}[v];"
        f"[3:a][1:a]concat=n=2:v=0:a=1[au]"
    )
    orden = [
        "ffmpeg", "-v", "error", "-y",
        "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
        "-i", str(MARCA / "logo-animado.mp4"),
        "-loop", "1", "-i", str(capa),
        "-f", "lavfi", "-t", f"{silencio:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
        "-filter_complex", filtro, "-map", "[v]", "-map", "[au]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(destino),
    ]
    proceso = subprocess.Popen(orden, stdin=subprocess.PIPE)
    try:
        for n in range(cuadros):
            pagina.evaluate(f"irA({n * 1000 / FPS})")
            proceso.stdin.write(pagina.screenshot(type="jpeg", quality=92))
    finally:
        proceso.stdin.close()
        if proceso.wait() != 0:
            raise RuntimeError(f"ffmpeg falló al crear {destino.name}")


def main(ids):
    config = leer_config()
    entorno = Environment(loader=FileSystemLoader(PLANTILLAS), undefined=StrictUndefined, autoescape=True)
    plantilla = entorno.get_template("reel.html")
    VIDEOS.mkdir(exist_ok=True)

    huellas = json.loads(HUELLAS.read_text(encoding="utf-8")) if HUELLAS.exists() else {}
    logo = (MARCA / "logo-animado.mp4").read_bytes()
    pendientes = []
    for _, _, pub in todas_las_publicaciones():
        html = plantilla.render(escenas=escenas_de(pub, config, MARCA.as_uri()), marca=MARCA.as_uri())
        # La huella no usa la ruta de la carpeta marca/, que cambia entre tu computadora y GitHub.
        sin_ruta = plantilla.render(escenas=escenas_de(pub, config, ""), marca="")
        huella = hashlib.sha256(sin_ruta.encode() + logo).hexdigest()[:16]
        if ids:
            elegido = pub["id"] in ids
        else:
            elegido = (date.fromisoformat(pub["fecha"]) >= date.today()
                       and (huellas.get(pub["id"]) != huella or not (VIDEOS / f"{pub['id']}.mp4").exists()))
        if elegido:
            pendientes.append((pub, html, huella))
    if not pendientes:
        print("No hay reels nuevos que generar.")
        return

    opciones = {}
    if os.environ.get("CHROMIUM_PATH"):
        opciones["executable_path"] = os.environ["CHROMIUM_PATH"]

    with sync_playwright() as p:
        navegador = p.chromium.launch(**opciones)
        pagina = navegador.new_page(viewport={"width": ANCHO, "height": ALTO})
        capa = PLANTILLAS / "_tmp_capa_logo.png"
        hacer_capa_logo(pagina, config, capa)
        try:
            for pub, html, huella in pendientes:
                temporal = PLANTILLAS / f"_tmp_{pub['id']}.html"
                temporal.write_text(html, encoding="utf-8")
                try:
                    pagina.goto(temporal.as_uri(), wait_until="networkidle", timeout=30000)
                    pagina.evaluate("document.fonts.ready")
                    duracion = pagina.evaluate("window.duracion")
                    destino = VIDEOS / f"{pub['id']}.mp4"
                    codificar(pagina, duracion, capa, destino)
                    print(f"Reel listo: {destino.relative_to(RAIZ)} ({duracion + 4 - CIERRE:.0f} s)")
                    huellas[pub["id"]] = huella
                    HUELLAS.write_text(json.dumps(huellas, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                finally:
                    temporal.unlink(missing_ok=True)
        finally:
            capa.unlink(missing_ok=True)
        navegador.close()


if __name__ == "__main__":
    main(set(sys.argv[1:]))
