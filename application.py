import os
import datetime
import re
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, errorhandle, lookup, lookup_recipe, lookup_bulk, get_extra_info

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.after_request
def after_request(response):
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///wtf.db")


@app.route("/")
def home():
    # Return splash page
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Get username, password, confirmation
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Must provide username
        if not username:
            flash("Your username can't be empty.", "error")
            return render_template("register.html")

        # Must provide password
        elif not password:
            flash("Your password can't be empty.", "error")
            return render_template("register.html")

        # Must provide confirmation
        elif not confirmation:
            flash("Your password confirmation can't be empty.", "error")
            return render_template("register.html")

        # Password and confirmation have to match to successfully register
        elif password != confirmation:
            flash("Your password and confimation don't match.", "error")
            return render_template("register.html")

        # Checks databse if username is already taken
        user_taken = db.execute("SELECT * FROM users WHERE username = :username",
                                username=username)

        # Checks if username is a letter or a number for safety reasons
        if not (username).isdigit() and not (username).isalpha():
            flash("Fill in a username with a letter or number!", "error")
            return render_template("register.html")

        # Return error message if username is already taken
        elif len(user_taken) == 1:
            flash("This username has been taken. Choose something else...", "error")
            return render_template("register.html")

        # Insert username and password into database
        user = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                          username=username, hash=generate_password_hash(password, method='pbkdf2:sha256', salt_length=8))

        # Remember which user is logged in
        session["user_id"] = user

        # Redirect to our search page and flash success message
        flash("Welcome to WhatTheFridge?!, " + username + ". You are now registered.", "success")
        return redirect("/onboarding")

    else:
        return render_template("register.html")


@app.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Get preferences from checkboxes
        glutenFree = request.form.get("glutenFree")
        vegetarian = request.form.get("vegetarian")
        vegan = request.form.get("vegan")
        preferences = ""

        # If gluten free selected, add gluten free to preferences
        if glutenFree == "glutenFree":
            preferences = preferences + ",glutenFree"

        # If vegetarian selected, add vegetarian to preferences
        if vegetarian == "vegetarian":
            preferences = preferences + ",vegetarian"

        # If vegan selected, add vegan to preferences
        if vegan == "vegan":
            preferences = preferences + ",vegan"

        # If nothing is selected, add NULL to preferences
        if not glutenFree and not vegetarian and not vegan:
            preferences = ",NULL"

        # Remove first comma
        preferences = preferences[1:]

        # Update database
        db.execute("UPDATE users SET diets=:preferences WHERE user_id=:user_id",
                   preferences=preferences, user_id=session["user_id"])

        flash("Your profile is now complete!", "success")
        return redirect("/search")

    else:
        return render_template("onboarding.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # Forgets any user that is logged in
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Get username
        username = request.form.get("username")
        password = request.form.get("password")

        # Must provide a username
        if not username:
            flash("Your username can't be empty.", "error")
            return render_template("login.html")

        # Must provide a password
        elif not password:
            flash("Your password can't be empty.", "error")
            return render_template("login.html")

        # Checks databse if username is already taken
        user_taken = db.execute("SELECT * FROM users WHERE username = :username",
                                username=username)

        # Checks if username is in database and if password corresponds with that user
        if len(user_taken) != 1 or not check_password_hash(user_taken[0]["hash"], password):
            flash("Invalid username and/or password.", "error")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = user_taken[0]["user_id"]

        # Redirect to our search page
        flash("Welcome back, " + username + "! You are now logged in.", "success")
        return redirect("/search")

    else:
        return render_template("login.html")


@app.route("/search", methods=["GET"])
@login_required
def search():
    # Make sure all ingredients in a GET-request are returned to page (for edit ingredients button)
    if request.args.get("ingredients"):
        # Format them for textbox
        ingredients = request.args.get("ingredients").replace(",", "\n")
        return render_template("search.html", ingredients=ingredients)
    return render_template("search.html")


@app.route("/support", methods=["GET"])
def support():
    if not session:
        # No personalised support page when not logged in
        return render_template("support.html")
    else:
        # Get personalised support page when user is logged in
        username = db.execute("SELECT username FROM users WHERE user_id=:user_id", user_id=session["user_id"])[0]["username"]
        return render_template("support.html", username=username)


@app.route("/results", methods=["POST"])
@login_required
def results():
    # Get information from database and from search
    ingredients = request.form.get("itemlist")
    ranking = request.form.get("ranking")
    if ranking is None:
        ranking = 1
    diets = db.execute("SELECT diets FROM users WHERE user_id=:user_id", user_id=session["user_id"])[0]["diets"].split(",")

    # Raise error when no ingredients are chosen
    if not ingredients:
        flash("Provide at least one ingredient.", "warning")
        return redirect("/search")

    # Check diets
    if len(diets) == 1 and 'NULL' not in diets:
        recipes_info = lookup(ingredients, ranking=1, number=15)
        recipes_extra_info = get_extra_info(recipes_info)
        recipes_result = []
        recipes_result_extra = []
        recipe_count = 0
        # Filter out recipes with diet
        for i in range(len(recipes_info[0])):
            if recipes_extra_info[i][diets[0]] == True and recipe_count < 10:
                recipes_result.append(recipes_info[0][i])
                recipes_result_extra.append(recipes_extra_info[i])
                recipe_count += 1

    elif len(diets) == 2:
        recipes_info = lookup(ingredients, ranking=1, number=20)
        recipes_extra_info = get_extra_info(recipes_info)
        recipes_result = []
        recipes_result_extra = []
        recipe_count = 0
        # Filter out recipes with two diet
        for i in range(len(recipes_info[0])):
            if recipes_extra_info[i][diets[0]] == True and recipes_extra_info[i][diets[1]] == True and recipe_count < 10:
                recipes_result.append(recipes_info[0][i])
                recipes_result_extra.append(recipes_extra_info[i])
                recipe_count += 1

    elif len(diets) == 3:
        recipes_info = lookup(ingredients, ranking=1, number=20)
        recipes_extra_info = get_extra_info(recipes_info)
        recipes_result = []
        recipes_result_extra = []
        recipe_count = 0
        # Filter out recipes with diet vegan/vegetarian & glutenfree
        for i in range(len(recipes_info[0])):
            if recipes_extra_info[i]['vegan'] == True and recipes_extra_info[i]['glutenFree'] == True and recipe_count < 10:
                recipes_result.append(recipes_info[0][i])
                recipes_result_extra.append(recipes_extra_info[i])
                recipe_count += 1

    else:
        # Regular lookup without diets
        recipes_info = lookup(ingredients, ranking)
        recipes_result = recipes_info[0]

        # Lookup extra information
        recipes_result_extra = get_extra_info(recipes_info)

    # Error when results are empty (API limit reached)
    if recipes_info == None:
        flash("Something went wrong. Get in touch with us for more information (402).", "error")
        return redirect("/search")
    # Error when no results could be found
    elif len(recipes_result) == 0:
        flash("We couldn't find any results.", "error")
        return redirect("/search")
    # return results page
    return render_template("results.html", recipes=recipes_result, ingredients=recipes_info[1], recipe_count=len(recipes_result), extra_info=recipes_result_extra, diets=diets)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        # Get preferences from checkboxes
        glutenFree = request.form.get("glutenFree")
        vegetarian = request.form.get("vegetarian")
        vegan = request.form.get("vegan")
        preferences = ""

        # Log out button
        logout = request.form.get("log_out")

        if logout is not None:
            session.clear()
            flash("You are now logged out.", "success")
            return redirect("/")

        # If gluten free selected, add gluten free to preferences
        if glutenFree == "glutenFree":
            preferences = preferences + ",glutenFree"

        # If vegetarian selected, add vegetarian to preferences
        if vegetarian == "vegetarian":
            preferences = preferences + ",vegetarian"

        # If vegan selected, add vegan to preferences
        if vegan == "vegan":
            preferences = preferences + ",vegan"

        # If nothing is selected, add NULL to preferences
        if not glutenFree and not vegetarian and not vegan:
            preferences = ",NULL"

        # Remove first comma
        preferences = preferences[1:]

        # Update database
        db.execute("UPDATE users SET diets=:preferences WHERE user_id=:user_id",
                   preferences=preferences, user_id=session["user_id"])

        flash("Preferences updated successfully", "success")
        return redirect("/profile")

    else:
        # Retrieve username from database
        username = db.execute("SELECT username FROM users WHERE user_id=:user_id", user_id=session["user_id"])[0]["username"]
        check = db.execute("SELECT diets FROM users WHERE user_id=:user_id", user_id=session["user_id"])[0]["diets"]

        # Create lists for checkboxes
        box_glutenFree = ""
        box_vegetarian = ""
        box_vegan = ""

        if check:
            # If user selected gluten free, keep gluten free selected
            if "glutenFree" in check:
                box_glutenFree = "checked"

            # If user selected vegetarian, keep vegetarian selected
            if "vegetarian" in check:
                box_vegetarian = "checked"

            # If user selected vegan, keep vegan selected
            if "vegan" in check:
                box_vegan = "checked"

            return render_template("profile.html", username=username, box_glutenFree=box_glutenFree, box_vegetarian=box_vegetarian, box_vegan=box_vegan)

        return render_template("profile.html", username=username, box_glutenFree=box_glutenFree, box_vegetarian=box_vegetarian, box_vegan=box_vegan)


@app.route("/addfavorite", methods=["GET"])
@login_required
def addfavorite():

    # Get ID for database
    id = request.args.get("id")

    # Save favorites from user in database
    if id:
        db.execute("INSERT INTO saved (recipe, user_id) VALUES (:recipe, :user_id)", recipe=id, user_id=session["user_id"])
        flash("Saved!")
        return redirect(request.referrer)

    else:
        errorhandle("NoID", 400)


@app.route("/favorites", methods=["GET", "POST"])
@login_required
def favorites():

    # When delete button is clicked
    if request.method == "POST":
        delete = (request.form.get("delete"))
        db.execute("DELETE FROM saved WHERE recipe=:r", r=delete)
        return redirect("/favorites")

    else:
        # Get saved recipes from database
        saved_recipes = db.execute("SELECT * FROM saved WHERE user_id=:user_id", user_id=session["user_id"])
        ids = []
        timestamp = dict()

        # Add IDs to list for bulk lookup and create timestamp dict.
        for recipe in saved_recipes:
            ids.append(recipe['recipe'])
            timestamp[recipe['recipe']] = recipe['timestamp']

        # Lookup
        info_recipes = lookup_bulk(ids)

        return render_template("favorite.html", info_recipes=info_recipes, timestamp=timestamp)


@app.route("/recipe", methods=["GET"])
@login_required
def recipe():
    # Get ID from get argument
    id = request.args.get("id")

    # Find recipe info with ID
    recipeinfo = lookup_recipe(id)

    # The recipe isn't found with the ID
    if recipeinfo is None:
        return errorhandle("IDErrorUnavailable", 400)
    url = recipeinfo["sourceUrl"]

    # Change every url to https (for safety/iFrame rules)
    url = url.replace('http://', 'https://')

    # Fetch recipes to check the saved ids
    saved_recipes = db.execute("SELECT * FROM saved WHERE user_id=:user_id AND recipe=:recipe",
                               user_id=session["user_id"], recipe=id)

    # If recipe already is in favourites (flash message to modify save button)
    if len(saved_recipes) > 0:
        flash("Internal: already saved")

    return render_template("recipe_iframe.html", url=url, recipeinfo=recipeinfo, id=id)


@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    if request.method == "POST":

        # Get variables
        currentpassword = request.form.get("current_password")
        newpassword = request.form.get("newpassword")
        confirmnewpassword = request.form.get("confirmnewpassword")

        # Must provide password
        if not currentpassword:
            flash("Your password can't be empty.", "error")
            return render_template("password.html")

        elif not newpassword:
            flash("Your new password can't be empty.", "error")
            return render_template("password.html")

        # Must provide confirmation
        elif not confirmnewpassword:
            flash("Your password confirmation can't be empty.", "error")
            return render_template("password.html")

        # Password and confirmation have to match to successfully change password
        elif newpassword != confirmnewpassword:
            flash("Your password and confimation don't match.", "error")
            return render_template("password.html")

        # Retrieve current hash
        currentpw = db.execute("SELECT hash FROM users WHERE user_id=:user_id", user_id=session["user_id"])[0]["hash"]

        # Check if password is correct
        if check_password_hash(currentpw, currentpassword) == False:
            flash("Your current password is incorrect", "error")
            return render_template("password.html")

        # Change password
        else:
            db.execute("UPDATE users SET hash=:password WHERE user_id=:user_id",
                       password=generate_password_hash(newpassword), user_id=session["user_id"])
            flash("Your password was changed", "success")
            return redirect("/profile")

    else:
        return render_template("password.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return errorhandle(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
