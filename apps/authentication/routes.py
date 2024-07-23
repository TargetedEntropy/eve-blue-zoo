# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import random
import hmac
import hashlib
import urllib.parse
import json
import esipy
from apps.authentication.util import verify_pass
from flask import render_template, redirect, request, url_for, session
from flask_login import current_user, login_user, logout_user
from apps import db, login_manager, esi
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.authentication.models import Users, Characters
from sqlalchemy.orm.exc import NoResultFound
from cryptography.fernet import Fernet
from esipy.exceptions import APIException


fen_key = Fernet.generate_key()
cipher_suite = Fernet(fen_key)


@blueprint.route("/")
def route_default():
    return redirect(url_for("authentication_blueprint.login"))


def Encrypt(text_f):
    encrypted = fen_key.encrypt(bytes(text_f.get(), "utf-8"))
    print("[*] Encrypted: {}".format(encrypted))
    return encrypted


def Decrypt(text_f):
    plain = fen_key.decrypt(bytes(text_f.get(), "utf-8"))
    print("[*] Plain: {}".format(plain))
    return plain


def generate_token(salt="None"):
    """Generates a non-guessable OAuth token
    
    Generate encrypted string to be used as OAuth token.  Use the
    current_user.master_character_id if user already logged in. This
    allows characters to be associated to the original login.
    """

    # Generate encrypted string with master_character_id
    obj = {"salt": salt}
    j = json.dumps(obj)

    encMessage = urllib.parse.quote_plus(cipher_suite.encrypt(j.encode()))

    return encMessage


# Login & Registration
@blueprint.route("/sso/login")
def sso_login():
    """this redirects the user to the EVE SSO login"""
    if current_user.is_authenticated:
        token = generate_token(current_user.character_id)
    else:
        token = generate_token()

    session["token"] = urllib.parse.unquote_plus(token)

    return redirect(
        esi.esisecurity.get_auth_uri(
            scopes=['esi-wallet.read_character_wallet.v1', 'esi-industry.read_character_mining.v1', 'esi-characters.read_blueprints.v1', 'esi-markets.structure_markets.v1', 'publicData', 'esi-skills.read_skills.v1'],
            state=token,
        )
    )


@blueprint.route("/sso/callback")
def callback():
    """This is where the user comes after he logged in SSO"""

    # get the code from the login process
    code = request.args.get("code")
    token = request.args.get("state")
    # compare the state with the saved token for CSRF check
    sess_token = session.pop("token", "")

    if token != str(sess_token):
        return "Login EVE Online SSO failed: Session Token Mismatch", 403

    if sess_token == "" or token == None:
        return "Login EVE Online SSO failed: Session Token is Empty", 403

    # try to get tokens
    try:
        auth_response = esi.esisecurity.auth(code)
    except APIException as e:
        return "Login EVE Online SSO failed: %s" % e, 403

    # we get the character informations
    cdata = esi.esisecurity.verify()

    # if sess_token is None or token is None or token != sess_token:
    #     return "Login EVE Online SSO failed: Session Token Mismatch", 403
    if current_user.is_authenticated:
        token = token.encode()
        decMessage = cipher_suite.decrypt(token)
        json_data = json.loads(decMessage)
        master_character_id = json_data["salt"]

        # This is a logged out user, check in database, if the user exists
        characterID = cdata["sub"].split(":")[2]
        try:
            character = Characters.query.filter(
                Characters.character_id == characterID,
            ).one()

        except NoResultFound:
            character = Characters()
            character.character_id = characterID
            character.master_character_id = master_character_id

        character.character_owner_hash = cdata["owner"]
        character.character_name = cdata["name"]
        character.update_token(auth_response)

        # now the character is ready, so update/create it and log the character
        try:
            db.session.merge(character)
            db.session.commit()

        except BaseException:
            db.session.rollback()
            return "Cannot add the user - uid: %d" % characterID

        return redirect(url_for("home_blueprint.index"))

    else:

        # This is a logged out user, check in database, if the user exists
        characterID = cdata["sub"].split(":")[2]
        try:
            user = Users.query.filter(
                Users.character_id == characterID,
            ).one()

        except NoResultFound:
            user = Users()
            user.character_id = characterID

        user.character_owner_hash = cdata["owner"]
        user.character_name = cdata["name"]
        user.update_token(auth_response)

        # now the user is ready, so update/create it and log the user
        try:
            db.session.merge(user)
            db.session.commit()

            login_user(user)
            session.permanent = True

        except BaseException:
            db.session.rollback()
            logout_user()
            return "Cannot login the user - uid: %d" % characterID

        return redirect(url_for("home_blueprint.index"))


@blueprint.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm(request.form)
    if "login" in request.form:

        # read form data
        username = request.form["username"]
        password = request.form["password"]

        # Locate user
        user = Users.query.filter_by(username=username).first()

        # Check the password
        if user and verify_pass(password, user.password):

            login_user(user)
            return redirect(url_for("authentication_blueprint.route_default"))

        # Something (user or pass) is not ok
        return render_template(
            "accounts/login.html",
            segment="login",
            msg="Wrong user or password",
            form=login_form,
        )

    if not current_user.is_authenticated:
        return render_template(
            "accounts/login.html",
            segment="login",
            form=login_form)
    return redirect(url_for("home_blueprint.index"))


@blueprint.route("/register", methods=["GET", "POST"])
def register():
    create_account_form = CreateAccountForm(request.form)
    if "register" in request.form:

        username = request.form["username"]
        email = request.form["email"]

        # Check usename exists
        user = Users.query.filter_by(username=username).first()
        if user:
            return render_template(
                "accounts/register.html",
                msg="Username already registered",
                segment="register",
                success=False,
                form=create_account_form,
            )

        # Check email exists
        user = Users.query.filter_by(email=email).first()
        if user:
            return render_template(
                "accounts/register.html",
                msg="Email already registered",
                segment="register",
                success=False,
                form=create_account_form,
            )

        # else we can create the user
        user = Users(**request.form)
        db.session.add(user)
        db.session.commit()

        return render_template(
            "accounts/register.html",
            msg='User created please <a href="/login">login</a>',
            segment="register",
            success=True,
            form=create_account_form,
        )

    else:
        return render_template(
            "accounts/register.html",
            segment="register",
            form=create_account_form)


@blueprint.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home_blueprint.index"))


# Errors


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template("home/page-403.html"), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template("home/page-403.html"), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template("home/page-404.html"), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template("home/page-500.html"), 500
