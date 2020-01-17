import requests
import urllib.parse
import os
from flask import redirect, render_template, request, session
from functools import wraps

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def errorhandle(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("error.html", code=code, message=escape(message)), code


def lookup(ingredients):
    """
    Lookup recipes by ingredients

    https://spoonacular.com/food-api/docs#Search-Recipes-by-Ingredients
    """
    ingredients_string = ingredients.splitlines()
    ingredients = ','.join(ingredients_string)

    try:
        api_key = "c413253e08574e40ba92563a5126e415"
        response = requests.get(f"https://api.spoonacular.com/recipes/findByIngredients?ingredients={(ingredients)}&apiKey={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        recipes = response.json()
        return recipes, ingredients

    except (KeyError, TypeError, ValueError):
        return None

def lookup_recipe(id):
    """
    Lookup recipes by id

    https://spoonacular.com/food-api/docs#Search-Recipes-by-Ingredients
    """
    try:
        api_key = "c413253e08574e40ba92563a5126e415"
        response = requests.get(f"https://api.spoonacular.com/recipes/{id}/information?apiKey={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        recipeinfo = response.json()
        return recipeinfo

    except (KeyError, TypeError, ValueError):
        return None

