import os

basedir = os.path.abspath(os.path.dirname(__file__))


def _armar_uri_bd():
    """Arma la URL de la base de datos.
    En desarrollo usa SQLite. En producción (Render) usa la variable
    DATABASE_URL que provee PostgreSQL (Render la da con prefijo
    'postgres://', pero SQLAlchemy moderno necesita 'postgresql://').
    """
    url = os.environ.get("DATABASE_URL")
    if url:
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    return f"sqlite:///{os.path.join(basedir, 'saboria.db')}"


class Config:
    # Clave usada por Flask para firmar la sesión y las cookies.
    # En producción SIEMPRE se debe definir con una variable de entorno.
    SECRET_KEY = os.environ.get("SECRET_KEY", "clave-de-desarrollo-cambiar-en-produccion")

    SQLALCHEMY_DATABASE_URI = _armar_uri_bd()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Clave de TheMealDB. La "1" es la clave de pruebas pública y gratuita
    # que ofrece TheMealDB (sirve para desarrollo, tiene límites de uso).
    MEALDB_API_KEY = os.environ.get("MEALDB_API_KEY", "1")
