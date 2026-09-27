# SaborIA

Página web de recetas hecha con Flask + SQLite/PostgreSQL, conectada a la
API pública TheMealDB. Proyecto de Tecnicatura en Informática.

## 1. Instalar y correr en local

```bash
python -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env             # y completá SECRET_KEY con una clave propia

python app.py
```

Abrí `http://localhost:5000` en el navegador. La base SQLite (`saboria.db`)
se crea sola la primera vez que se ejecuta la app.

## 2. Publicar en Render (paso a paso)

1. Subí este proyecto a un repositorio de GitHub (público o privado).
2. Entrá a [render.com](https://render.com) y creá una cuenta (podés usar tu
   cuenta de GitHub para entrar directo).
3. En el panel de Render, tocá **New +** → **Blueprint**, y conectá el
   repositorio que subiste. Render va a detectar el archivo `render.yaml`
   de este proyecto y va a proponer crear automáticamente:
   - un servicio web (`saboria`) con Gunicorn,
   - una base de datos PostgreSQL gratuita (`saboria-db`).
4. Confirmá la creación. Render instala las dependencias, genera solo la
   `SECRET_KEY` y conecta la base de datos (`DATABASE_URL`) automáticamente.
5. Cuando el despliegue termine (estado **Live**), Render te da una URL
   pública del tipo `https://saboria.onrender.com`. Esa es tu página.

Si preferís no usar `render.yaml`, podés crear el **Web Service** y la
**PostgreSQL** a mano desde "New +"; en ese caso configurá vos las
variables de entorno `SECRET_KEY`, `MEALDB_API_KEY` y `DATABASE_URL`
(el valor de `DATABASE_URL` te lo da Render en la página de la base
de datos, como "Internal Database URL").

> Nota: como asistente no tengo acceso a Internet ni a tu cuenta de GitHub
> o Render desde este entorno, así que no puedo hacer el despliegue por vos:
> los pasos de arriba los tenés que hacer manualmente.

## 3. Limitaciones conocidas de TheMealDB

- No da información nutricional (calorías, azúcares, etc.).
- No tiene filtro específico "sin gluten" ni "apto para diabéticos": las
  secciones de celíacos y diabéticos muestran advertencias en vez de
  garantías, y la app señala qué ingredientes podrían tener gluten según
  su nombre (de forma orientativa, no como certificación).
