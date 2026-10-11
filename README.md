# SOFTTIDENT – Redes automáticas

Publica solo en Instagram, cada sábado a las 9:45, las publicaciones que apruebes.
Funciona en GitHub (gratis), así que publica aunque tu computadora esté apagada.

**Cómo es el ciclo de cada mes**

1. Le pides a Claude Code: *"genera el contenido de diciembre"*. Crea los textos y las imágenes.
2. Los revisas. Si te gustan, le dices *"apruébalos"* (o cambias `"aprobado": false` a `true`).
3. GitHub publica cada sábado lo aprobado y lo marca como publicado.

---

## Instalación (una sola vez, unos 30 minutos)

### 1. Crea el repositorio en GitHub
1. Crea una cuenta gratis en [github.com](https://github.com).
2. Botón **New repository** → nombre `softtident-redes` → **Public** → **Create repository**.
   Tiene que ser público para que Instagram pueda descargar las imágenes. Solo se ven
   las publicaciones y el código; el token de Instagram queda oculto como secreto.
3. Sube todos los archivos de esta carpeta (incluida la carpeta `.github`). La forma más fácil es
   con [GitHub Desktop](https://desktop.github.com): *Add local repository* → elige esta carpeta → *Publish*.
4. En el repositorio: **Settings → Actions → General → Workflow permissions** → marca
   **Read and write permissions** → **Save**.

### 2. Consigue el token de Instagram
Necesitas tu cuenta de Instagram profesional (de empresa o creador).
1. Entra a [developers.facebook.com](https://developers.facebook.com) con tu cuenta de Facebook
   y crea una app (**Crear app**).
2. Elige el caso de uso para **administrar mensajes y contenido de Instagram** y entra a
   **API de Instagram con inicio de sesión de Instagram**.
3. En **Generar tokens de acceso**, agrega tu cuenta de Instagram del consultorio, acepta los
   permisos y copia el token. Debe incluir los permisos `instagram_business_basic` e
   `instagram_business_content_publish`.

### 3. Guarda el token en GitHub
**Settings → Secrets and variables → Actions → New repository secret**
- Nombre: `IG_TOKEN` · Valor: el token que copiaste.

Opcional, para que el token se renueve solo cada mes (dura 60 días):
- Crea un token en GitHub → *Settings → Developer settings → Fine-grained tokens*, solo para este
  repositorio, con permiso **Secrets: Read and write**.
- Guárdalo como secreto con el nombre `GH_PAT`.

Si no haces esto, repite el paso 2 y actualiza `IG_TOKEN` cada 50 días.

### 4. Prueba
- Pestaña **Actions → Generar imágenes → Run workflow**: deben aparecer los JPEG en `imagenes/`.
- **Actions → Publicar en Instagram → Run workflow**: si hoy no toca nada, dirá
  "no hay publicaciones aprobadas pendientes para hoy". Eso significa que funciona.

---

## Uso diario

| Quiero… | Qué hago |
| --- | --- |
| Contenido del próximo mes | Abrir Claude Code en esta carpeta: *"genera el contenido de enero"* |
| Cambiar un texto | Editar el archivo en `contenido/` (en GitHub, ícono del lápiz) |
| Que algo no se publique | Poner `"aprobado": false` |
| Cambiar horario o WhatsApp | Editar `config.json`; las imágenes se rehacen solas |
| Ver si se publicó | Pestaña **Actions**, o el campo `publicado` en el archivo del mes |

## Bueno saber
- Solo publica en **Instagram**. Para Facebook necesitas crear una página del consultorio;
  luego se puede agregar.
- No programes las mismas publicaciones en Meta Business Suite, o saldrán dos veces.
- Si un sábado falla, lo reintenta hasta 3 días después.
- GitHub puede retrasar las tareas programadas unos minutos.
