# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import random
import hmac
import hashlib
import urllib.parse
import json
import logging
from apps.authentication.util import verify_pass
from flask import render_template, redirect, request, url_for, session
from flask_login import current_user, login_user, logout_user, login_required
from apps import login_manager, esi
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from sqlalchemy.orm.exc import NoResultFound
from cryptography.fernet import Fernet
from apps import discord_client
from flask_discord import requires_authorization

from models.users import Users
from models.characters import Characters
from flask import g

logger = logging.getLogger(__name__)

def get_cipher_suite():
    """Get a Fernet cipher suite using app's secret key"""
    from flask import current_app
    import base64
    import hashlib
    
    # Use Flask's SECRET_KEY to generate a consistent Fernet key
    secret_key = current_app.config['SECRET_KEY'].encode()
    # Hash to get exactly 32 bytes for Fernet key
    key_hash = hashlib.sha256(secret_key).digest()
    # Encode as base64 for Fernet
    fernet_key = base64.urlsafe_b64encode(key_hash)
    return Fernet(fernet_key)



@blueprint.route("/")
def route_default():
    return redirect(url_for("authentication_blueprint.login"))


def Encrypt(text_f):
    cipher_suite = get_cipher_suite()
    encrypted = cipher_suite.encrypt(bytes(text_f.get(), "utf-8"))
    print("[*] Encrypted: {}".format(encrypted))
    return encrypted


def Decrypt(text_f):
    cipher_suite = get_cipher_suite()
    plain = cipher_suite.decrypt(bytes(text_f.get(), "utf-8"))
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

    cipher_suite = get_cipher_suite()
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

    # Get authorization URL from Preston
    scopes = [
        "esi-wallet.read_character_wallet.v1",
        "esi-industry.read_character_mining.v1",
        "esi-characters.read_blueprints.v1",
        "esi-markets.structure_markets.v1",
        "publicData",
        "esi-skills.read_skills.v1",
    ]
    
    auth_url, state = esi.get_authorize_url(scopes)
    # Store the state for verification
    session["oauth_state"] = state
    session["csrf_token"] = token
    
    return redirect(auth_url)


@blueprint.route("/sso/callback")
def callback():
    """This is where the user comes after he logged in SSO"""

    # get the code from the login process
    code = request.args.get("code")
    state = request.args.get("state")
    
    # Verify OAuth state to prevent CSRF
    oauth_state = session.pop("oauth_state", "")
    csrf_token = session.pop("csrf_token", "")
    sess_token = session.pop("token", "")
    
    # Clear any potentially corrupted session tokens
    session.pop("token", None)

    if state != oauth_state:
        return "Login EVE Online SSO failed: OAuth State Mismatch", 403

    if not code or not state:
        return "Login EVE Online SSO failed: Missing code or state", 403

    # try to get tokens using Preston
    try:
        auth_response = esi.exchange_authorization_code(code, state)
    except Exception as e:
        return f"Login EVE Online SSO failed: {e}", 403

    # get the character information from the access token
    try:
        cdata = esi.get_character_info(auth_response['access_token'])
    except Exception as e:
        return f"Failed to get character info: {e}", 403

    # Extract character ID from Preston character info
    # Preston returns character info in a different format than esipy
    character_id_str = cdata.get("CharacterID")
    if not character_id_str:
        return f"Failed to get character ID from SSO response: {cdata}", 403
    
    characterID = int(character_id_str)
    character_name = cdata.get("CharacterName", "")
    character_owner_hash = cdata.get("CharacterOwnerHash", "")

    db = g.db
    
    if current_user.is_authenticated:
        # Adding additional character to existing user
        if csrf_token:
            try:
                cipher_suite = get_cipher_suite()
                token_bytes = csrf_token.encode()
                decMessage = cipher_suite.decrypt(token_bytes)
                json_data = json.loads(decMessage)
                master_character_id = json_data["salt"]
            except Exception as e:
                # If decryption fails (old token), use current user as master
                logger.warning(f"Failed to decrypt CSRF token: {e}, using current user as master")
                master_character_id = current_user.character_id
        else:
            master_character_id = current_user.character_id

        # Check if character already exists
        try:
            character = db.query(Characters).filter(
                Characters.character_id == characterID,
            ).one()
        except NoResultFound:
            character = Characters()
            character.character_id = characterID
            character.master_character_id = master_character_id

        character.character_owner_hash = character_owner_hash
        character.character_name = character_name
        character.sso_is_valid = True
        character.update_token(auth_response)

        # Save character
        try:
            db.merge(character)
            db.commit()
        except Exception as e:
            db.rollback()
            return f"Cannot add the character - uid: {characterID}, error: {e}", 500

        return redirect(url_for("home_blueprint.index"))

    else:
        # New user login
        try:
            user = db.query(Users).filter(
                Users.character_id == characterID,
            ).one()
        except NoResultFound:
            user = Users()
            user.character_id = characterID

        user.character_owner_hash = character_owner_hash
        user.character_name = character_name
        user.update_token(auth_response)

        # Save user and login
        try:
            db.merge(user)
            db.commit()

            login_user(user)
            session.permanent = True

        except Exception as e:
            db.rollback()
            logout_user()
            return f"Cannot login the user - uid: {characterID}, error: {e}", 500

        return redirect(url_for("home_blueprint.index"))


@blueprint.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm(request.form)
    if "login" in request.form:
        # read form data
        username = request.form["username"]
        password = request.form["password"]

        # Locate user
        db = g.db
        user = db.query(Users).filter_by(username=username).first()

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
        return render_template("accounts/login.html", segment="login", form=login_form)
    return redirect(url_for("home_blueprint.index"))


@blueprint.route("/register", methods=["GET", "POST"])
def register():
    create_account_form = CreateAccountForm(request.form)
    if "register" in request.form:
        username = request.form["username"]
        email = request.form["email"]

        # Check usename exists
        db = g.db
        user = db.query(Users).filter_by(username=username).first()
        if user:
            return render_template(
                "accounts/register.html",
                msg="Username already registered",
                segment="register",
                success=False,
                form=create_account_form,
            )

        # Check email exists
        user = db.query(Users).filter_by(email=email).first()
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
        db.add(user)
        db.commit()

        return render_template(
            "accounts/register.html",
            msg='User created please <a href="/login">login</a>',
            segment="register",
            success=True,
            form=create_account_form,
        )

    else:
        return render_template(
            "accounts/register.html", segment="register", form=create_account_form
        )


@blueprint.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home_blueprint.index"))


# Discord


@blueprint.route("/discord/login")
@login_required
def discord_login():
    return discord_client.create_session(scope=["identify"])


@blueprint.route("/discord/callback/")
def discord_callback():
    discord_client.callback()
    user = discord_client.fetch_user()

    if user:
        db = g.db
        user_data = db.query(Users).filter(
            Users.character_id == current_user.character_id,
        ).one()

        user_data.discord_user_id = user.id

        db.merge(user_data)
        db.commit()
    else:
        print("user not found")
    welcome_user(user)
    return redirect(url_for("home_blueprint.index"))


def welcome_user(user):
    print("sending welcome")
    dm_channel = discord_client.bot_request(
        "/users/@me/channels", "POST", json={"recipient_id": user.id}
    )
    return discord_client.bot_request(
        f"/channels/{dm_channel['id']}/messages",
        "POST",
        json={"content": "Thanks for authorizing the app!"},
    )


@blueprint.route("/me/")
@requires_authorization
def me():
    user = discord_client.fetch_user()
    return f"""
    <html>
        <head>
            <title>{user.name}</title>
        </head>
        <body>
            <img src='{user.avatar_url}' />
        </body>
    </html>"""


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
