"""Crea PUBLICAR-A-MANO.md: cada publicación aprobada con su reel, su imagen y su texto listo para copiar.

Sirve para programar las publicaciones a mano en la app de Instagram.

Uso:
    python scripts/hoja_manual.py
"""
from datetime import date

from comun import RAIZ, leer_config, todas_las_publicaciones

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
HORA = "9:45"

INSTRUCCIONES = """# Publicar a mano en Instagram

Cada sábado sale un **reel**. Para cada uno de abajo:

1. Toca **Descargar reel** y guárdalo en el celular (en la página que se abre: ⋮ o mantener
   presionado → *Descargar*).
2. En Instagram: **+** → **Reel** → elige el video → **Siguiente**.
3. Toca **Audio** (ícono de nota musical), elige una canción y toca **Listo** → **Siguiente**.
4. Copia el texto (botón de copiar del recuadro gris) y pégalo en la descripción.
5. **Más opciones** → **Programar este reel** → elige la fecha y la hora indicadas → **Programar**.
6. Revisa tus programadas en tu perfil → ☰ → **Contenido programado**.

Si un día prefieres publicar la imagen en vez del reel, usa **Descargar imagen** y en el
paso 2 elige **Publicación** (sin el paso 3).

Esta hoja muestra solo lo aprobado de hoy en adelante. No sabe qué ya programaste:
revísalo en **Contenido programado**.
"""


def fecha_larga(texto):
    f = date.fromisoformat(texto)
    return f"{DIAS[f.weekday()]} {f.day} de {MESES[f.month - 1]} de {f.year}"


def main():
    config = leer_config()
    hoy = date.today()
    pubs = sorted((p for _, _, p in todas_las_publicaciones()
                   if p.get("aprobado") and not p.get("publicado")
                   and date.fromisoformat(p["fecha"]) >= hoy),
                  key=lambda p: p["fecha"])

    partes = [INSTRUCCIONES]
    if not pubs:
        partes.append("\n_No hay publicaciones aprobadas pendientes._\n")
    for pub in pubs:
        texto = pub["texto_publicacion"]
        if config.get("hashtags"):
            texto += "\n\n" + config["hashtags"]
        imagen = f"imagenes/{pub['id']}.jpg"
        video = f"videos/{pub['id']}.mp4"
        enlaces = f"[⬇️ Descargar imagen]({imagen}?raw=true)"
        if (RAIZ / video).exists():
            enlaces = f"[🎬 Descargar reel]({video}?raw=true) · " + enlaces
        partes.append(
            f"\n---\n\n## {fecha_larga(pub['fecha'])} · {HORA}\n\n"
            f"<img src=\"{imagen}\" width=\"320\">\n\n"
            f"{enlaces}\n\n"
            f"```text\n{texto}\n```\n"
        )

    destino = RAIZ / "PUBLICAR-A-MANO.md"
    destino.write_text("".join(partes), encoding="utf-8")
    print(f"Hoja lista: {destino.name} ({len(pubs)} publicaciones)")


if __name__ == "__main__":
    main()
