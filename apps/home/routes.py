# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, request
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import create_engine, distinct, desc
from apps import esi, db
from apps.home import blueprint
from apps.authentication.models import Characters, Blueprints, InvType, SkillSet, MiningLedger, MapSolarSystems

from dotenv import dotenv_values
config = dotenv_values(".env")



@blueprint.route("/index")
@login_required
def index():
    # Get Master Wallet
    wallet = esi.get_wallet(current_user)
    
    # Get Characters
    characters = db.session.query(
        Characters.character_name,
        Characters.character_id,        
        SkillSet.total_sp,
        SkillSet.unallocated_sp
    ).join(
        SkillSet, Characters.character_id == SkillSet.character_id
    ).filter(
        Characters.master_character_id == current_user.character_id
    ).all()
    
    return render_template("home/index.html", segment="index", wallet=wallet, characters=characters)


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

@blueprint.route("/ui-miningledger.html")
@login_required
def page_miningledger():
    # Detect the current page
    segment = get_segment(request)

    data = []
    try:
        # Define the query
        query = db.session.query(distinct(MiningLedger.date)).order_by(desc(MiningLedger.date))

        # Execute the query and fetch all results
        all_dates = query.all()

        for ledger_date in all_dates:
            ledger_date = ledger_date[0]
            date_str = ledger_date.strftime('%Y-%m-%d')

            # Define the query
            ledger_query = db.session.query(
                Characters.character_name,
                MiningLedger.type_id,
                InvType.typeName,
                MiningLedger.quantity,
                MapSolarSystems.solarSystemName
            ).join(
                Characters, MiningLedger.character_id == Characters.character_id
            ).join(
                InvType, MiningLedger.type_id == InvType.typeID
            ).join(
                MapSolarSystems, MiningLedger.solar_system_id == MapSolarSystems.solarSystemID
            ).filter(
                Characters.master_character_id == current_user.character_id
            ).filter(
                MiningLedger.date == date_str
            ).group_by(
                Characters.character_name,
                MiningLedger.quantity,
                MiningLedger.solar_system_id,
                MiningLedger.type_id
            ).order_by(
                desc(MiningLedger.quantity)
            )           

            ledger_data = ledger_query.all()

            for ledger_row in ledger_data:
                character_name, typeId, typeName, quantity, solar_system_name = ledger_row
                data.append([ledger_date,character_name, typeName, quantity, solar_system_name])
               
    except Exception as e:
        print(e)
        data = []

    # Serve the file (if exists) from app/templates/home/FILE.html
    return render_template(
        "home/ui-miningledger.html", segment=segment, data=data
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
