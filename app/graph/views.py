from flask import render_template, jsonify, url_for, request, session, redirect, flash
from . import graph
import random, time
from flask_mail import Message


@graph.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("/graph/index.html")
