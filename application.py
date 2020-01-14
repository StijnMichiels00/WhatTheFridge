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
@login_required
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # If no username is typed in, error
        if not request.form.get("username"):
            # Return function errorhandle if no username is typed in
            return errorhandle("You must type in a username", 400)

        # If no password is typed in, error
        elif not request.form.get("password"):
            # Return function errorhandle if no password is typed in
            return errorhandle("You must type in a password", 400)


@app.route("/login", methods=["GET", "POST"])
def login():
    return print("TODO")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    return print("TODO")


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
