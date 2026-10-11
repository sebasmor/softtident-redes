# SOFTTIDENT – Redes automáticas

Este proyecto publica en Instagram el contenido del consultorio dental SOFTTIDENT
(San Gerardo, Camilo Ponce Enríquez, Ecuador). Claude Code genera el contenido de cada
mes; la dueña o el dueño lo aprueba; GitHub lo publica solo.

**Modo actual: publicación a mano.** No hay token de Instagram (no se pudo verificar el
celular en Meta). Los flujos `publicar.yml` y `renovar-token.yml` están apagados. Las
publicaciones se programan a mano en la app de Instagram con `PUBLICAR-A-MANO.md`, que
genera `scripts/hoja_manual.py` (el flujo "Generar imágenes" lo corre solo). Tras aprobar
contenido nuevo, ejecuta también `python scripts/hoja_manual.py` antes del commit.

## Cómo funciona
- `config.json`: datos fijos del consultorio (WhatsApp, horario, ubicación, servicios).
- `contenido/AAAA-MM.json`: publicaciones del mes. Cada una tiene `id`, `fecha`,
  `aprobado`, `plantilla`, `datos` y `texto_publicacion`. El campo `publicado` lo escribe
  el robot; nunca lo borres ni lo inventes.
- `plantillas/*.html`: diseños de 1080×1350 con la marca. `presentacion`, `destacado`
  (fondo verde azulado: emergencias, avisos), `lista` (tratamientos y consejos, 3 a 5
  puntos), `preguntas` (hasta 5 preguntas).
- `scripts/generar_imagenes.py` hace los JPEG en `imagenes/`; `scripts/publicar.py` publica
  (solo imágenes, no reels).
- **Cada sábado sale un reel** (no la imagen). `scripts/generar_reels.py` hace `videos/<id>.mp4`
  (1080×1920, escenas animadas con `plantillas/reel.html` + `marca/logo-animado.mp4` al final),
  a partir de los mismos `datos`. Sin música: la eligen en Instagram. Necesita ffmpeg.
  `videos/huellas.json` evita rehacer reels que no cambiaron. En Windows, si Chromium no
  arranca, usa `CHROMIUM_PATH` apuntando al Chrome instalado.

## Cuando te pidan "genera el contenido de <mes>"
1. Crea `contenido/AAAA-MM.json` con una publicación por sábado de ese mes, todas con
   `"aprobado": false`. El `id` es `AAAA-MM-DD-tema`.
2. Alterna los tipos: emergencias, tratamiento, prevención o consejo, conócenos o preguntas.
   No repitas un tema de los últimos 2 meses (revisa los archivos anteriores).
3. Respeta los feriados de Ecuador: si un sábado cae en feriado, usa `destacado` para avisar
   si se atiende.
4. Ejecuta `python scripts/generar_imagenes.py <ids>` y `python scripts/generar_reels.py <ids>`
   y muestra imágenes y reels para revisión. Reels de 15 a 40 segundos: si sale más largo, recorta textos.
5. Cuando aprueben, cambia `aprobado` a `true`, haz commit y push.

## Reglas de contenido
- Español sencillo y cercano, de tú, frases cortas. Público: familias y trabajadores mineros.
- Siempre cerrar `texto_publicacion` con el WhatsApp 099 406 4555.
- No prometer resultados ni usar palabras como "garantizado" o "perfecto". No inventar precios
  ni promociones: si no te las dan, no las pongas. "Te damos el precio antes de empezar" sí.
- No usar nombres de personas del equipo. No usar fotos de pacientes.
- Endodoncias: solo dientes de una raíz (uniradiculares).
- Se atiende también a niños. Pagos en efectivo o transferencia. Hay atención de emergencias.
- Textos en imágenes: títulos de máximo 4 palabras por línea; los puntos de `lista`, de una línea.

## Ideas de reserva ya escritas
Señales de que necesitas ir al dentista · diente roto o golpe: qué hacer · quién te atiende
(equipo, sin nombres) · endodoncia: salvar tu diente · dulces y niños · prótesis: volver a
masticar y sonreír · cuidar tus dientes en jornadas largas de trabajo.
