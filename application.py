import os
import datetime
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, errorhandle, lookup

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
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Must provide username
        if not request.form.get("username"):
            flash("Your username can't be empty.")
            return render_template("register.html")

        # Must provide password
        elif not request.form.get("password"):
            flash("Your password can't be empty.")
            return render_template("register.html")

        # Must provide confirmation
        elif not request.form.get("confirmation"):
            flash("Your password confirmation can't be empty.")
            return render_template("register.html")

        # Password and confirmation have to match to successfully register
        elif request.form.get("password") != request.form.get("confirmation"):
            flash("Your password and confimation don't match.")
            return render_template("register.html")

        # Checks databse if username is already taken
        user_taken = db.execute("SELECT * FROM users WHERE username = :username",
                                username=request.form.get("username"))

        # Return error message if username is already taken
        if len(user_taken) == 1:
            flash("This username has been taken. Choose something else...")
            return render_template("register.html")

        # Insert username and password into database
        user = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                   username=request.form.get("username"), hash=generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8))

        # Remember which user is logged in
        session["user_id"] = user

        # Redirect to our search page
        flash("You are now registered.")
        return redirect("/search")

    else:
        return render_template("register.html")

@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    if request.method == "POST":
        password = request.form.get("password")

        # Haalt de huidige hash op
        code0 = db.execute("SELECT hash FROM users WHERE id=:q", q=session["user_id"])
        for cd in code0:
            code = cd["hash"]

        # Maakt nieuwe hash
        npassword = request.form.get("newpassword")
        newpassword = generate_password_hash(npassword)

        # Wachtwoord check
        if check_password_hash(code, password) == False:
            flash("Password incorrect")
            return render_template("password.html")

        # Veranderen wachtwoord in database
        else:
            db.execute("UPDATE users SET hash=:p WHERE id=:d", p=newpassword, d=session["user_id"])
            return render_template("index.html")

    else:
        return render_template("password.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # Forgets any user that is logged in
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Must provide a username
        if not request.form.get("username"):
            flash("Your username can't be empty.")
            return render_template("login.html")

        # Must provide a password
        elif not request.form.get("password"):
            flash("Your password can't be empty.")
            return render_template("login.html")

        # Checks databse if username is already taken
        user_taken = db.execute("SELECT * FROM users WHERE username = :username",
                                username=request.form.get("username"))

        # Checks if username is in database and if password corresponds with that user
        if len(user_taken) != 1 or not check_password_hash(user_taken[0]["hash"], request.form.get("password")):
            flash("Invalid username and/or password.")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = user_taken[0]["id"]

        # Redirect to our search page
        return redirect("/search")

    else:
        return render_template("login.html")


@app.route("/search", methods=["GET", "POST"])
# @login_required
def search():
    if request.method == "POST":
        pass

    return render_template("search.html")


@app.route("/support", methods=["GET"])
# @login_required
def support():
    if not session:
        return render_template("support.html")
    else:
        username = db.execute("SELECT username FROM users WHERE id=:id", id=session["user_id"])[0]["username"]
        return render_template("support.html", username=username)


@app.route("/results", methods=["POST"])
# @login_required
def results():
    if request.form.get("itemlist"):
        errorhandle(400,"Something went wrong...")
    pass


@app.route("/profile", methods=["GET", "POST"])
# @login_required
def profile():
    # Retrieve username from database
    username = [x["username"] for x in (db.execute("SELECT username FROM users WHERE id=:q", q=session["user_id"]))][0]
    check = [x["favorite"] for x in (db.execute("SELECT * FROM favorites WHERE user_id=:n", n=session["user_id"]))]

    # Create lists for checkboxes
    box_meat = []
    box_fish = []
    box_all = []

    # If user selected meat, keep meat selected
    if "Meat" in check:
        box_meat.append("checked")
        box_meat = box_meat[0]

    # If user selected fish, keep fish selected
    if "Fish" in check:
        box_fish.append("checked")
        box_fish = box_fish[0]

    # If user selected fish and meat, keep both selected
    if "Meat'Fish" in check:
        box_all.append("checked")
        box_all = box_all[0]

    if request.method == "POST":
        meat = request.form.get("meat")
        fish = request.form.get("fish")

        preferences = []

        # If meat selected, add meat to preferences
        if meat == "Meat":
            preferences.append(meat)

        # If fish selected, add fish to preferences
        if fish == "Fish":
            preferences.append(fish)

        # If meat and fish selected, add both to preferences
        if check == "Meat'Fish":
            preferences.append("Meat'Fish")

        if len(check) == 0:
            db.execute("INSERT INTO favorites (favorite, user_id) VALUES (:favorite, :user_id)", favorite=preferences, user_id=session["user_id"])

        else:
            db.execute("UPDATE favorites SET favorite=:p WHERE user_id=:d", p=preferences, d=session["user_id"])
            # db.execute("DELETE FROM favorites WHERE user_id=:d", d=session["user_id"])
            # db.execute("INSERT INTO favorites (favorite, user_id) VALUES (:favorite, :user_id)", favorite=preferences, user_id=session["user_id"])
        return render_template("index.html", preferences=preferences)

    else:
        return render_template("profile.html", username=username, box_meat=box_meat, box_fish=box_fish, box_all=box_all)


@app.route("/favorites", methods=["GET"])
# @login_required
def favorites():
    return print("TODO")


@app.route("/help", methods=["GET"])
def helps():
    return print("TODO")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return errorhandle(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
