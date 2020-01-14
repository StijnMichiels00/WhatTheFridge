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
            # Return function errorhandle if no username is provided
            return errorhandle("You must type in a username!")

        # Must provide password
        elif not request.form.get("password"):
            # Return function errorhandle if no password is provided
            return errorhandle("You must type in a password!")

        # Must provide confirmation
        elif not request.form.get("confirmation"):
            # Return function errorhandle if no confirmation is provided
            return errorhandle("You must type in a confirmation!")

        # Password and confirmation have to match to successfully register
        elif request.form.get("password") != request.form.get("confirmation"):
            # Return function errorhandle if password and confirmation don't match
            return errorhandle("Password and confirmation must match!")

        # Checks databse if username is already taken
        user_taken = db.execute("SELECT * FROM users WHERE username = :username",
                                username=request.form.get("username"))

        # Return error message if username is already taken
        if len(user_taken) == 1:
            return errorhandle("Username is already taken!")

        # Redirect to homepage
        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    return print("TODO")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    return ("search.html")


@app.route("/results", methods=["GET", "POST"])
@login_required
def results():
    return print("TODO")


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    return print("TODO")


@app.route("/favorites", methods=["GET"])
@login_required
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
