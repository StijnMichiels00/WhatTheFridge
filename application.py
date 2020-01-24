import os
import datetime
import re
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, errorhandle, lookup, lookup_recipe, lookup_bulk

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
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
    if request.method == "POST":
        # Must provide username
        if not request.form.get("username"):
            flash("Your username can't be empty.", "error")
            return render_template("register.html")

        # Must provide password
        elif not request.form.get("password"):
            flash("Your password can't be empty.", "error")
            return render_template("register.html")

        # Must provide confirmation
        elif not request.form.get("confirmation"):
            flash("Your password confirmation can't be empty.", "error")
            return render_template("register.html")

        # Password and confirmation have to match to successfully register
        elif request.form.get("password") != request.form.get("confirmation"):
            flash("Your password and confimation don't match.", "error")
            return render_template("register.html")

        # Checks databse if username is already taken
        user_taken = db.execute("SELECT * FROM users WHERE username = :username",
                                username=request.form.get("username"))

        # Checks if username is a letter or a number for safety reasons
        if not (request.form.get("username")).isdigit() and not (request.form.get("username")).isalpha():
            flash("Fill in a username with a letter or number!", "error")
            return render_template("register.html")

        # Return error message if username is already taken
        if len(user_taken) == 1:
            flash("This username has been taken. Choose something else...", "error")
            return render_template("register.html")

        # Insert username and password into database
        user = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                   username=request.form.get("username"), hash=generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8))

        # Remember which user is logged in
        session["user_id"] = user

        # Redirect to our search page
        flash("Welcome to WhatTheFridge?!, "+ request.form.get("username") + ". You are now registered.", "success")
        return redirect("/search")

    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # Forgets any user that is logged in
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Must provide a username
        if not request.form.get("username"):
            flash("Your username can't be empty.", "error")
            return render_template("login.html")

        # Must provide a password
        elif not request.form.get("password"):
            flash("Your password can't be empty.", "error")
            return render_template("login.html")

        # Checks databse if username is already taken
        user_taken = db.execute("SELECT * FROM users WHERE username = :username",
                                username=request.form.get("username"))

        # Checks if username is in database and if password corresponds with that user
        if len(user_taken) != 1 or not check_password_hash(user_taken[0]["hash"], request.form.get("password")):
            flash("Invalid username and/or password.", "error")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = user_taken[0]["user_id"]

        # Redirect to our search page
        flash("Welcome back, " + request.form.get("username") + "! You are now logged in.", "success")
        return redirect("/search")

    else:
        return render_template("login.html")


@app.route("/search", methods=["GET"])
@login_required
def search():
    # Make sure all ingredients in a GET-request are returned to page (for edit query button)
    if request.args.get("ingredients"):
        # Format them for textbox
        ingredients = request.args.get("ingredients").replace(",","\n")
        return render_template("search.html",ingredients=ingredients)
    return render_template("search.html")


@app.route("/support", methods=["GET"])
def support():
    if not session:
        # No personalised support page when logged out
        return render_template("support.html")
    else:
        # Get personalised support page when user is logged in
        username = db.execute("SELECT username FROM users WHERE user_id=:id", id=session["user_id"])[0]["username"]
        return render_template("support.html", username=username)


@app.route("/results", methods=["POST"])
@login_required
def results():
    ingredients=request.form.get("itemlist")
    ranking=request.form.get("ranking")
    if not ingredients:
        flash("Provide at least one ingredient.", "warning")
        return redirect("/search")

    # Lookup
    recipes_info = lookup(ingredients, ranking=1)

    # Lookup extra info
    # Create string of recipes ids
    ids = []
    for recipe in recipes_info[0]:
        ids.append(recipe['id'])

    recipes_extra_info = lookup_bulk(ids)

    # Error when results are empty (API limit reached (probably))
    if recipes_info == None:
        flash("Something went wrong. Get in touch with us for more information (402).", "error")
        return redirect("/search")
    # Error when no results could be found
    if len(recipes_info[0]) == 0:
        flash("We couldn't find any results.", "error")
        return redirect("/search")
    # return results page
    return render_template("results.html", recipes=recipes_info[0], ingredients=recipes_info[1], recipe_count=len(recipes_info[0]), extra_info=recipes_extra_info)



@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    if request.method == "POST":
        gluten_free = request.form.get("gluten_free")
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
        if gluten_free == "gluten_free":
            preferences = preferences + " gluten_free"

        # If vegetarian selected, add vegetarian to preferences
        if vegetarian == "vegetarian":
            preferences = preferences + " vegetarian"

        # If vegan selected, add vegan to preferences
        if vegan == "vegan":
            preferences = preferences + " vegan"

        db.execute("UPDATE users SET exclusions=:p WHERE user_id=:user_id", p=preferences, user_id=session["user_id"])

        return redirect("/profile")

    else:
         # Retrieve username from database
        username = db.execute("SELECT username FROM users WHERE user_id=:user_id", user_id=session["user_id"])[0]["username"]
        check = db.execute("SELECT exclusions FROM users WHERE user_id=:user_id", user_id=session["user_id"])[0]["exclusions"]
        print(check)
        print("--------------------------------------------------------------------------")
        print(check.split(" "))
        # Create lists for checkboxes
        box_gluten_free = ""
        box_vegetarian = ""
        box_vegan = ""

        if check:
            # If user selected gluten free, keep gluten free selected
            if "gluten_free" in check:
                box_gluten_free = "checked"

            # If user selected vegetarian, keep vegetarian selected
            if "vegetarian" in check:
                box_vegetarian = "checked"

            # If user selected vegan, keep vegan selected
            if "vegan" in check:
                box_vegan = "checked"

            return render_template("profile.html", username=username, box_gluten_free=box_gluten_free, box_vegetarian=box_vegetarian, box_vegan=box_vegan)


@app.route("/addfavorite", methods=["GET"])
@login_required
def addfavorite():

    id = request.args.get("id")

    # Save favorites from user in database
    if id:
        db.execute("INSERT INTO saved (recipe, user_id) VALUES (:recipe, :user_id)", recipe=id, user_id=session["user_id"])
        flash("Saved!")
        return redirect(request.referrer)

    else:
        errorhandle("NoID",400)

@app.route("/favorites", methods=["GET", "POST"])
@login_required
def favorites():

    if request.method == "POST":
        if request.form.get("Submit exclusions"):
            print("test")
        #  db.execute("REMOVE ")
        pass
    else:
        saved_recipes = db.execute("SELECT * FROM saved WHERE user_id=:user_id", user_id=session["user_id"])

        ids = []
        timestamp = dict()
        for recipe in saved_recipes:
            ids.append(recipe['recipe'])
            timestamp[recipe['recipe']] = recipe['timestamp']
        if None in ids:
            errorhandle("DBCorruptfor", 400)
        info_recipes = lookup_bulk(ids)

        return render_template("favorite.html", info_recipes=info_recipes, timestamp=timestamp)

@app.route("/recipe", methods=["GET"])
@login_required
def recipe():
    # Get ID from get argument
    id=request.args.get("id")

    # Find recipe info with ID
    recipeinfo = lookup_recipe(id)

    # The recipe isn't found with the ID
    if recipeinfo is None:
        return errorhandle("IDErrorUnavailable", 400)
    url = recipeinfo["sourceUrl"]

    # Change every url to https (for safety/iFrame rules)
    url = url.replace('http://','https://')

    # Fetch recipes to check the saved ids
    saved_recipes = db.execute("SELECT * FROM saved WHERE user_id=:user_id AND recipe=:recipe", user_id=session["user_id"], recipe=id)
    # If recipe already is in favourites (flash message to modify save button)
    if len(saved_recipes) > 0:
        flash("Internal: already saved")

    return render_template("recipe_iframe.html", url=url, recipeinfo=recipeinfo, id=id)


@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    if request.method == "POST":
        password = request.form.get("password")

        # Retrieve current hash
        code0 = db.execute("SELECT hash FROM users WHERE id=:q", q=session["user_id"])
        for cd in code0:
            code = cd["hash"]

        # Create new hash
        npassword = request.form.get("newpassword")
        newpassword = generate_password_hash(npassword)

        # Check if password is correct
        if check_password_hash(code, password) == False:
            flash("Your current password incorrect", "error")
            return render_template("password.html")

        # Change password
        else:
            db.execute("UPDATE users SET hash=:p WHERE user_id=:d", p=newpassword, d=session["user_id"])
            return render_template("index.html")
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
