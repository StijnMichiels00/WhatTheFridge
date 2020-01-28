import requests
import urllib.parse
import os
from flask import redirect, render_template, jsonify, request, session, make_response
from functools import wraps
import json

api_key = "09fe7b8ca2d84dc2aa231c91a507b5c1"

# api_key="c68807a59a4f4601b7387e05cf1350a2"

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


def lookup(ingredients, ranking, number):
    """
    Lookup recipes by ingredients

    https://spoonacular.com/food-api/docs#Search-Recipes-by-Ingredients
    """

    ingredients_string = ingredients.splitlines()
    ingredients = ','.join(ingredients_string)
    try:
        with open('static/results.json', 'r') as cachefile:
            data = json.load(cachefile)
            if data[ingredients]:
                return (data[ingredients], ingredients)

    except (KeyError):
        try:
            response = requests.get(
                f"https://api.spoonacular.com/recipes/findByIngredients?ingredients={(ingredients)}&ranking={ranking}&number={number}&apiKey={api_key}")
            response.raise_for_status()
            cache = dict()
            cache[ingredients] = response.json()
            with open('static/results.json', 'r+') as cachefile:
                old_dict = json.load(cachefile)
                old_dict.update(cache)
                cachefile.seek(0)
                cachefile.write(json.dumps(old_dict))
                cachefile.truncate()

        except requests.RequestException:
            return None

        # Parse response
        try:
            recipes = response.json()
            return recipes, ingredients

        except (KeyError, TypeError, ValueError):
            return None


def lookup_recipe(id, ranking=1):
    """
    Lookup recipes by id

    https://spoonacular.com/food-api/docs#Search-Recipes-by-Ingredients
    """
    try:
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


def lookup_bulk(ids):
    """
    Bulk lookup recipes by id

    https://spoonacular.com/food-api/docs#Get-Recipe-Information-Bulk
    """

    ids_list = [str(i) for i in ids]
    ids_string = ",".join(ids_list)
    try:
        with open('static/results_extra.json', 'r') as cachefile:
            data = json.load(cachefile)
            if data[ids_string] is not "KeyError":
                return (data[ids_string])
    except(KeyError):
        try:
            response = requests.get(f"https://api.spoonacular.com/recipes/informationBulk?ids={ids_string}&apiKey={api_key}")
            response.raise_for_status()
            cache = dict()
            cache[ids_string] = response.json()
            with open('static/results_extra.json', 'r+') as cachefile:
                old_dict = json.load(cachefile)
                old_dict.update(cache)
                cachefile.seek(0)
                cachefile.write(json.dumps(old_dict))
                cachefile.truncate()

        except requests.RequestException:
            return None

        # Parse response
        try:

            recipesinfo = response.json()
            return recipesinfo

        except (KeyError, TypeError, ValueError):
            return None


def get_extra_info(recipes_info):
    ids = []
    for recipe in recipes_info[0]:
        ids.append(recipe['id'])
    return lookup_bulk(ids)

