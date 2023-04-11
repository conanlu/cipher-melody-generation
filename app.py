import os
import generate_melody
from flask import Flask, flash, jsonify, redirect, render_template, request, session

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

PREFIX = "static/images/"


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
def quote():
    if request.method == "POST":
        symbol = request.form.get("symbol")
        generate_melody.generate(symbol)
        return render_template("result.html", prefix=PREFIX, url="sing.png")
    else:
        # show form if not post
        return render_template("index.html")
