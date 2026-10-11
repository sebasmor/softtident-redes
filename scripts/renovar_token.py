"""Renueva el token de Instagram (dura 60 días) e imprime el nuevo en la salida estándar.

El flujo de GitHub lo guarda de nuevo como secreto IG_TOKEN.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

token = os.environ.get("IG_TOKEN")
if not token:
    sys.exit("Falta IG_TOKEN.")
url = "https://graph.instagram.com/refresh_access_token?" + urllib.parse.urlencode(
    {"grant_type": "ig_refresh_token", "access_token": token})
with urllib.request.urlopen(url, timeout=60) as r:
    respuesta = json.loads(r.read())
print(respuesta["access_token"])
dias = respuesta.get("expires_in", 0) // 86400
print(f"Token renovado; vence en {dias} días.", file=sys.stderr)
