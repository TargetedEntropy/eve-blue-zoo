# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, request
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from sqlalchemy.orm.exc import NoResultFound
from apps import esi
from apps.home import blueprint
from apps.authentication.models import Characters




@blueprint.route("/index")
@login_required
def index():
    wallet = esi.get_wallet(current_user)
    return render_template("home/index.html", segment="index", wallet=wallet)


@blueprint.route("/<template>")
@login_required
def route_template(template):
    try:

        if not template.endswith(".html"):
            pass

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template("home/page-404.html"), 404

    except BaseException:
        return render_template("home/page-500.html"), 500


@blueprint.route("/page-user.html")
@login_required
def page_user():
    # Detect the current page
    segment = get_segment(request)

    try:
        characters = Characters.query.filter(
            Characters.master_character_id == current_user.character_id
        )
    except NoResultFound:
        characters = []

    # Serve the file (if exists) from app/templates/home/FILE.html
    return render_template(
        "home/page-user.html", segment=segment, characters=characters
    )


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split("/")[-1]

        if segment == "":
            segment = "index"

        return segment

    except BaseException:
        return None
