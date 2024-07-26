# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, request, redirect, url_for
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import aliased
from sqlalchemy import create_engine, distinct, desc
from apps import esi, db
from apps.home import blueprint
from apps.authentication.models import (
    Users,
    Characters,
    Blueprints,
    InvType,
    SkillSet,
    MiningLedger,
    MapSolarSystems,
    CharacterNotifications,
)

from dotenv import dotenv_values

config = dotenv_values(".env")


@blueprint.route("/index")
@login_required
def index():
    # Get Master Wallet
    wallet = esi.get_wallet(current_user)

    # Get Characters
    characters = (
        db.session.query(
            Characters.character_name,
            Characters.character_id,
            SkillSet.total_sp,
            SkillSet.unallocated_sp,
        )
        .join(SkillSet, Characters.character_id == SkillSet.character_id)
        .filter(Characters.master_character_id == current_user.character_id)
        .all()
    )

    return render_template(
        "home/index.html", segment="index", wallet=wallet, characters=characters
    )


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
        
    discord_id = None
    
    try:
        user = Users.query.filter(
            Users.character_id == current_user.character_id
        ).first()
        discord_id = user.discord_user_id
    except NoResultFound:
        user = []

    

    # Serve the file (if exists) from app/templates/home/FILE.html
    return render_template(
        "home/page-user.html", segment=segment, characters=characters, discord_id=discord_id
    )


@blueprint.route("/page-character.html", methods=["POST"])
@login_required
def page_character_post():
    # Detect the current page
    segment = get_segment(request)
    character_id = request.form["character_id"]

    ownercheck = (
        db.session.query(Characters)
        .filter(Characters.master_character_id == current_user.character_id)
        .filter(Characters.character_id == character_id)
        .first()
    )

    if not ownercheck:
        return render_template("home/page-404.html"), 404

    if request.method == "POST":
        preferences = request.form.getlist("preferences")
        preferences_str = ",".join(preferences)

        try:
            characternotifications = (
                db.session.query(CharacterNotifications)
                .filter(CharacterNotifications.character_id == character_id)
                .filter(
                    CharacterNotifications.master_character_id
                    == current_user.character_id
                )
                .one()
            )

            characternotifications.enabled_notifications = preferences_str

            db.session.commit()
        except Exception as error:
            characternotifications = CharacterNotifications(
                character_id=character_id,
                master_character_id=current_user.character_id,
                enabled_notifications=preferences_str,
            )
            db.session.add(characternotifications)
            db.session.commit()

        return redirect(
            f"{url_for('home_blueprint.page_character_get')}?character_id={character_id}"
        )

    try:
        if not character_id.isnumeric():
            return render_template("home/page-404.html"), 404
    except Exception as error:
        print(f"Login page failed, error: {error}")
        return render_template("home/page-404.html"), 404


@blueprint.route("/page-character.html", methods=["GET"])
@login_required
def page_character_get():
    # Detect the current page
    segment = get_segment(request)
    character_id = request.args.get("character_id")
    try:
        if not character_id.isnumeric():
            return render_template("home/page-404.html"), 404
    except Exception as error:
        return render_template("home/page-404.html"), 404

    notifications = (
        db.session.query(CharacterNotifications.enabled_notifications)
        .filter(CharacterNotifications.character_id == character_id)
        .filter(CharacterNotifications.master_character_id == current_user.character_id)
        .first()
    )

    if notifications:
        notifications = notifications[0]
    else:
        notifications = ""

    try:
        # Get Characters
        character = (
            db.session.query(
                Characters.character_name,
                Characters.character_id,
                SkillSet.total_sp,
                SkillSet.unallocated_sp,
            )
            .join(SkillSet, Characters.character_id == SkillSet.character_id)
            .filter(Characters.character_id == character_id)
            .one()
        )

    except NoResultFound:
        characters = []
        return render_template("home/page-404.html"), 404

    # Serve the file (if exists) from app/templates/home/FILE.html
    return render_template(
        "home/page-character.html",
        segment=segment,
        character=character,
        notifications=notifications,
    )


@blueprint.route("/ui-miningledger.html")
@login_required
def page_miningledger():
    # Detect the current page
    segment = get_segment(request)

    try:
        # # Define the query
        # query = db.session.query(distinct(MiningLedger.date)).order_by(desc(MiningLedger.date))

        # Aliasing the Characters table for the join
        CharactersAlias = aliased(Characters)

        # Updating the query
        query = (
            db.session.query(distinct(MiningLedger.date))
            .join(Characters, MiningLedger.character_id == Characters.character_id)
            .filter(Characters.master_character_id == current_user.character_id)
            .order_by(desc(MiningLedger.date))
        )

        # Execute the query and fetch all results
        all_dates = query.all()

        date_list = []

        for ledger_date in all_dates:

            daily_totals = []

            ledger_date = ledger_date[0]

            date_str = ledger_date.strftime("%Y-%m-%d")

            # Define the query
            ledger_query = (
                db.session.query(
                    Characters.character_name,
                    MiningLedger.type_id,
                    InvType.typeName,
                    MiningLedger.quantity,
                    MapSolarSystems.solarSystemName,
                )
                .join(Characters, MiningLedger.character_id == Characters.character_id)
                .join(InvType, MiningLedger.type_id == InvType.typeID)
                .join(
                    MapSolarSystems,
                    MiningLedger.solar_system_id == MapSolarSystems.solarSystemID,
                )
                .filter(Characters.master_character_id == current_user.character_id)
                .filter(MiningLedger.date == date_str)
                .group_by(
                    Characters.character_name,
                    MiningLedger.quantity,
                    MiningLedger.solar_system_id,
                    MiningLedger.type_id,
                )
                .order_by(desc(MiningLedger.quantity))
            )

            ledger_data = ledger_query.all()

            data_builder = []
            for ledger_row in ledger_data:
                character_name, typeId, typeName, quantity, solar_system_name = (
                    ledger_row
                )

                manual = 1
                for daily_total in daily_totals:
                    if daily_total[4] == typeId and daily_total[3] == solar_system_name:
                        daily_total[2] += quantity
                        manual = 0

                if manual == 1:
                    daily_totals.append(
                        [ledger_date, typeName, quantity, solar_system_name, typeId]
                    )

            for dt in daily_totals:
                data_builder.append(dt)

            date_list.append(data_builder)

    except Exception as e:
        print(f"error: {e}")
        data = []

    # Serve the file (if exists) from app/templates/home/FILE.html
    return render_template(
        "home/ui-miningledger.html", segment=segment, date_list=date_list
    )


@blueprint.route("/ui-blueprints.html")
@login_required
def page_blueprints():
    # Detect the current page
    segment = get_segment(request)

    # Get All of the users' Characters
    try:
        characters = Characters.query.filter(
            Characters.master_character_id == current_user.character_id
        ).all()
    except NoResultFound:
        characters = []

    # Get all the Blueprints they own
    all_blueprints = []
    for character in characters:
        blueprints = Blueprints.query.filter(
            Blueprints.character_id == character.character_id
        ).all()

        for bp in blueprints:
            item_name = InvType.query.filter(InvType.typeID == bp.type_id).first()
            bp.characterName = character.character_name
            bp.itemName = item_name.typeName
            all_blueprints.append(bp)

    # Serve the file (if exists) from app/templates/home/FILE.html
    return render_template(
        "home/ui-blueprints.html", segment=segment, data=all_blueprints
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
