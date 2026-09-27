"""
Funciones para hablar con la API pública TheMealDB (themealdb.com).

TheMealDB es gratuita para uso de desarrollo con la clave "1", pero tiene
limitaciones importantes que hay que tener en cuenta:
  - No da información nutricional (calorías, azúcar, etc.) en ningún endpoint.
  - No tiene un filtro específico para "sin gluten" ni para "apto diabéticos".
  - El filtro por categoría/ingrediente (filter.php) devuelve datos incompletos
    (solo id, nombre e imagen); para ver el detalle completo hay que pedir
    lookup.php con el id de cada receta.
Por eso, en este proyecto NO se inventan datos: donde la API no da
información, se avisa al usuario en vez de completar con valores falsos.
"""

import os

import requests

MEALDB_API_KEY = os.environ.get("MEALDB_API_KEY", "1")
BASE_URL = f"https://www.themealdb.com/api/json/v1/{MEALDB_API_KEY}"
TIMEOUT = 8  # segundos

# Palabras clave que suelen indicar gluten. Es una clasificación orientativa
# hecha a partir del nombre de los ingredientes, NO una garantía médica.
INGREDIENTES_CON_GLUTEN = [
    "flour", "harina", "wheat", "trigo", "barley", "cebada", "rye", "centeno",
    "malt", "malta", "beer", "cerveza", "pasta", "spaghetti", "noodle",
    "bread", "pan", "breadcrumb", "crumb", "cracker", "galleta", "couscous",
    "semolina", "sémola", "soy sauce", "salsa de soja", "oats", "avena",
    "pastry", "tortilla de trigo", "bun", "cake flour", "self raising",
]

# Categorías de TheMealDB que suelen coincidir con "sin animales" (orientativo).
CATEGORIAS_VEGANAS = {"vegan"}
CATEGORIAS_VEGETARIANAS = {"vegetarian", "vegan"}


class ErrorAPIRecetas(Exception):
    """Se levanta cuando TheMealDB no responde o responde con error."""


def _get(endpoint, params=None):
    try:
        resp = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as exc:
        raise ErrorAPIRecetas(
            "No se pudo conectar con el servicio externo de recetas (TheMealDB). "
            "Puede ser un problema de conexión o que el servicio esté caído."
        ) from exc


def buscar_por_nombre(nombre):
    data = _get("search.php", {"s": nombre})
    return data.get("meals") or []


def buscar_por_ingrediente(ingrediente):
    data = _get("filter.php", {"i": ingrediente})
    return data.get("meals") or []


def filtrar_por_categoria(categoria):
    data = _get("filter.php", {"c": categoria})
    return data.get("meals") or []


def listar_categorias():
    data = _get("categories.php")
    return data.get("categories") or []


def obtener_receta(receta_id):
    data = _get("lookup.php", {"i": receta_id})
    meals = data.get("meals") or []
    return meals[0] if meals else None


def obtener_recetas_aleatorias(cantidad=6):
    """Trae varias recetas al azar. La API gratuita solo permite pedir
    una por vez (random.php), así que se llama varias veces y se ignoran
    los duplicados."""
    recetas = []
    vistos = set()
    intentos = 0
    while len(recetas) < cantidad and intentos < cantidad * 3:
        intentos += 1
        data = _get("random.php")
        meals = data.get("meals") or []
        if meals and meals[0]["idMeal"] not in vistos:
            vistos.add(meals[0]["idMeal"])
            recetas.append(meals[0])
    return recetas


def extraer_ingredientes(receta):
    """TheMealDB guarda los ingredientes como strIngredient1..20 /
    strMeasure1..20 en vez de una lista. Esta función arma la lista."""
    ingredientes = []
    for i in range(1, 21):
        nombre = (receta.get(f"strIngredient{i}") or "").strip()
        cantidad = (receta.get(f"strMeasure{i}") or "").strip()
        if nombre:
            ingredientes.append({"nombre": nombre, "cantidad": cantidad or "a gusto"})
    return ingredientes


def clasificar_vegano(receta):
    categoria = (receta.get("strCategory") or "").lower()
    return categoria in CATEGORIAS_VEGANAS


def clasificar_ingredientes_con_gluten(ingredientes):
    """Devuelve la lista de ingredientes de la receta que podrían contener
    gluten, según una lista de palabras clave. Es orientativo: no reemplaza
    la verificación de una etiqueta real ni el criterio de un profesional."""
    sospechosos = []
    for ing in ingredientes:
        nombre = ing["nombre"].lower()
        if any(palabra in nombre for palabra in INGREDIENTES_CON_GLUTEN):
            sospechosos.append(ing["nombre"])
    return sospechosos


# Categorías que se muestran como destacadas en el inicio, mapeadas a
# categorías reales de TheMealDB (api/json/v1/1/categories.php).
CATEGORIAS_DESTACADAS = [
    {"id": "Breakfast", "nombre": "Desayunos", "icono": "☀️"},
    {"id": "Vegetarian", "nombre": "Vegetarianas", "icono": "🥗"},
    {"id": "Seafood", "nombre": "Mariscos", "icono": "🐟"},
    {"id": "Pasta", "nombre": "Pastas", "icono": "🍝"},
    {"id": "Chicken", "nombre": "Pollo", "icono": "🍗"},
    {"id": "Dessert", "nombre": "Postres", "icono": "🍰"},
]
