from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class Usuario(db.Model, UserMixin):
    """Tabla de usuarios registrados en SaborIA."""

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    favoritos = db.relationship(
        "Favorito", backref="usuario", lazy=True, cascade="all, delete-orphan"
    )

    def establecer_password(self, password_plano):
        # Nunca guardamos la contraseña en texto plano: la ciframos con
        # el algoritmo seguro que trae Werkzeug (el mismo que usa Flask).
        self.password_hash = generate_password_hash(password_plano)

    def verificar_password(self, password_plano):
        return check_password_hash(self.password_hash, password_plano)


class Favorito(db.Model):
    """Relación entre un usuario y una receta de TheMealDB que guardó."""

    __tablename__ = "favoritos"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)

    # No guardamos la receta completa: solo el ID externo de TheMealDB y
    # los datos mínimos para mostrar la tarjeta sin volver a pedirla a la API.
    receta_id = db.Column(db.String(20), nullable=False)
    receta_nombre = db.Column(db.String(200), nullable=False)
    receta_imagen = db.Column(db.String(500))
    fecha_guardado = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("usuario_id", "receta_id", name="uq_usuario_receta"),
    )
