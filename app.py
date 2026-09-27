import os

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

import mealdb_api as mealdb
from config import Config
from models import Favorito, Usuario, db


def crear_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.login_message = "Iniciá sesión para acceder a esa página."
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    @login_manager.user_loader
    def cargar_usuario(usuario_id):
        return db.session.get(Usuario, int(usuario_id))

    with app.app_context():
        db.create_all()

    registrar_rutas(app)
    return app


def registrar_rutas(app):
    # ---------- Inicio ----------
    @app.route("/")
    def inicio():
        recomendadas = []
        error_api = None
        try:
            recomendadas = mealdb.obtener_recetas_aleatorias(6)
        except mealdb.ErrorAPIRecetas as exc:
            error_api = str(exc)

        return render_template(
            "index.html",
            categorias=mealdb.CATEGORIAS_DESTACADAS,
            recomendadas=recomendadas,
            error_api=error_api,
        )

    # ---------- Búsqueda ----------
    @app.route("/buscar")
    def buscar():
        nombre = request.args.get("q", "").strip()
        ingrediente = request.args.get("ingrediente", "").strip()
        categoria = request.args.get("categoria", "").strip()

        resultados = []
        error_api = None
        se_busco = bool(nombre or ingrediente or categoria)

        if se_busco:
            try:
                if nombre:
                    resultados = mealdb.buscar_por_nombre(nombre)
                elif ingrediente:
                    resultados = mealdb.buscar_por_ingrediente(ingrediente)
                elif categoria:
                    resultados = mealdb.filtrar_por_categoria(categoria)
            except mealdb.ErrorAPIRecetas as exc:
                error_api = str(exc)

        return render_template(
            "search.html",
            resultados=resultados,
            error_api=error_api,
            se_busco=se_busco,
            q=nombre,
            ingrediente=ingrediente,
            categoria=categoria,
            favoritos_ids=_ids_favoritos_usuario(),
        )

    # ---------- Detalle de receta ----------
    @app.route("/receta/<receta_id>")
    def receta_detalle(receta_id):
        try:
            receta = mealdb.obtener_receta(receta_id)
        except mealdb.ErrorAPIRecetas as exc:
            flash(str(exc), "error")
            return redirect(url_for("inicio"))

        if receta is None:
            flash("No se encontró esa receta en TheMealDB.", "error")
            return redirect(url_for("buscar"))

        ingredientes = mealdb.extraer_ingredientes(receta)
        pasos = [p.strip() for p in (receta.get("strInstructions") or "").split("\r\n") if p.strip()]
        if len(pasos) <= 1:
            # Algunas recetas separan los pasos con saltos de línea simples
            # o con puntos, en vez de \r\n.
            pasos = [p.strip() for p in (receta.get("strInstructions") or "").split("\n") if p.strip()]

        es_vegano = mealdb.clasificar_vegano(receta)
        ingredientes_con_gluten = mealdb.clasificar_ingredientes_con_gluten(ingredientes)

        es_favorito = False
        if current_user.is_authenticated:
            es_favorito = (
                Favorito.query.filter_by(usuario_id=current_user.id, receta_id=receta_id).first()
                is not None
            )

        return render_template(
            "recipe_detail.html",
            receta=receta,
            ingredientes=ingredientes,
            pasos=pasos,
            es_vegano=es_vegano,
            ingredientes_con_gluten=ingredientes_con_gluten,
            es_favorito=es_favorito,
        )

    # ---------- Dietas especiales ----------
    @app.route("/dietas")
    def dietas():
        return render_template("special_diets.html")

    @app.route("/dietas/<tipo>")
    def dieta_recetas(tipo):
        if tipo not in ("vegano", "celiaco", "diabetico"):
            return redirect(url_for("dietas"))

        resultados = []
        error_api = None
        try:
            if tipo == "vegano":
                resultados = mealdb.filtrar_por_categoria("Vegan")
            elif tipo == "celiaco":
                # TheMealDB no tiene filtro "sin gluten": mostramos un
                # conjunto amplio de recetas y advertimos que hay que
                # revisar los ingredientes de cada una (ver plantilla).
                resultados = mealdb.filtrar_por_categoria("Vegetarian")
            elif tipo == "diabetico":
                # Tampoco hay filtro por azúcar/carbohidratos: se muestran
                # categorías que tienden a tener menos azúcar agregada,
                # dejando la advertencia bien visible.
                resultados = mealdb.filtrar_por_categoria("Seafood")
        except mealdb.ErrorAPIRecetas as exc:
            error_api = str(exc)

        titulos = {
            "vegano": "Recetas veganas",
            "celiaco": "Recetas para celíacos",
            "diabetico": "Recetas para diabéticos",
        }

        return render_template(
            "diet_recipes.html",
            tipo=tipo,
            titulo=titulos[tipo],
            resultados=resultados,
            error_api=error_api,
            favoritos_ids=_ids_favoritos_usuario(),
        )

    # ---------- Favoritos ----------
    @app.route("/favoritos")
    @login_required
    def favoritos():
        lista = (
            Favorito.query.filter_by(usuario_id=current_user.id)
            .order_by(Favorito.fecha_guardado.desc())
            .all()
        )
        return render_template("favorites.html", favoritos=lista)

    @app.route("/favoritos/agregar", methods=["POST"])
    @login_required
    def favoritos_agregar():
        receta_id = request.form.get("receta_id")
        receta_nombre = request.form.get("receta_nombre")
        receta_imagen = request.form.get("receta_imagen")

        if not receta_id or not receta_nombre:
            flash("Faltan datos de la receta para guardarla en favoritos.", "error")
            return redirect(request.referrer or url_for("inicio"))

        ya_existe = Favorito.query.filter_by(
            usuario_id=current_user.id, receta_id=receta_id
        ).first()
        if not ya_existe:
            nuevo = Favorito(
                usuario_id=current_user.id,
                receta_id=receta_id,
                receta_nombre=receta_nombre,
                receta_imagen=receta_imagen,
            )
            db.session.add(nuevo)
            db.session.commit()
            flash("Receta guardada en favoritos.", "exito")

        return redirect(request.referrer or url_for("favoritos"))

    @app.route("/favoritos/quitar", methods=["POST"])
    @login_required
    def favoritos_quitar():
        receta_id = request.form.get("receta_id")
        fav = Favorito.query.filter_by(
            usuario_id=current_user.id, receta_id=receta_id
        ).first()
        if fav:
            db.session.delete(fav)
            db.session.commit()
            flash("Receta quitada de favoritos.", "info")
        return redirect(request.referrer or url_for("favoritos"))

    # ---------- Usuarios ----------
    @app.route("/registro", methods=["GET", "POST"])
    def registro():
        if current_user.is_authenticated:
            return redirect(url_for("perfil"))

        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            password2 = request.form.get("password2", "")

            if not nombre or not email or not password:
                flash("Completá todos los campos.", "error")
            elif len(password) < 6:
                flash("La contraseña debe tener al menos 6 caracteres.", "error")
            elif password != password2:
                flash("Las contraseñas no coinciden.", "error")
            elif Usuario.query.filter_by(email=email).first():
                flash("Ya existe una cuenta con ese correo electrónico.", "error")
            else:
                usuario = Usuario(nombre=nombre, email=email)
                usuario.establecer_password(password)
                db.session.add(usuario)
                db.session.commit()
                login_user(usuario)
                flash(f"¡Bienvenido/a, {nombre}!", "exito")
                return redirect(url_for("inicio"))

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("perfil"))

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            usuario = Usuario.query.filter_by(email=email).first()

            if usuario and usuario.verificar_password(password):
                login_user(usuario)
                flash(f"Hola de nuevo, {usuario.nombre}.", "exito")
                siguiente = request.args.get("next")
                return redirect(siguiente or url_for("inicio"))

            flash("Correo o contraseña incorrectos.", "error")

        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Sesión cerrada.", "info")
        return redirect(url_for("inicio"))

    @app.route("/perfil")
    @login_required
    def perfil():
        cantidad_favoritos = Favorito.query.filter_by(usuario_id=current_user.id).count()
        return render_template("profile.html", cantidad_favoritos=cantidad_favoritos)

    # ---------- Utilidad interna ----------
    def _ids_favoritos_usuario():
        if not current_user.is_authenticated:
            return set()
        favs = Favorito.query.filter_by(usuario_id=current_user.id).all()
        return {f.receta_id for f in favs}


app = crear_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(debug=debug, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
