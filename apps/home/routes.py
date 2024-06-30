# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, request
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import create_engine
from apps import esi
from apps.home import blueprint
from apps.authentication.models import Characters

from dotenv import dotenv_values
config = dotenv_values(".env")



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

engine = create_engine(config["SQLALCHEMY_DATABASE_URI"])
connection = engine.connect()


def get_price(type_id, quantity):
    query = f"select avg from itemPrices where type_id = {type_id} order by date_created limit 1"
    cursor = connection.execute(query)
    try:
        price_data = cursor.fetchone()[0]
    except Exception as e:
        print(f"Failed to execute query: {query} : {e}")
    
    value = price_data * quantity
    return value


@blueprint.route("/ui-miningledger.html")
@login_required
def page_miningledger():
    # Detect the current page
    segment = get_segment(request)

    data = []
    try:
        cursor = connection.execute("select distinct(date) from MiningLedger order by date desc")
        all_dates = cursor.fetchall()

        for ledger_date in all_dates:
            daily_total = 0
            ledger_date = ledger_date[0]
            date_str = ledger_date.strftime('%Y-%m-%d')
            cursor = connection.execute(
                f"select Characters.character_name,MiningLedger.type_id,invTypes.TypeName,MiningLedger.quantity,mapSolarSystems.solarSystemName from MiningLedger INNER JOIN Characters ON MiningLedger.character_id = Characters.character_id INNER JOIN invTypes ON MiningLedger.type_id = invTypes.typeID  INNER JOIN mapSolarSystems ON MiningLedger.solar_system_id = mapSolarSystems.solarSystemID where date = '{date_str}' group by Characters.character_name,quantity,solar_system_id,type_id,type_id order by MiningLedger.quantity desc"
            )

            ledger_data = cursor.fetchall()
            #print(ledger_data)
            date_count = 0
            for ledger_row in ledger_data:
                character_name, typeId, typeName, quantity, solar_system_name = ledger_row
                
                value = 0 # get_price(typeId, quantity)

                # print(f"{character_name}:{typeName}:{solar_system_name}:{quantity}:{value}")
                if date_count >= 1:
                    ledger_date = ""
                data.append([ledger_date,character_name, typeName, quantity, solar_system_name, value])
                daily_total = daily_total + value
                
                date_count = date_count + 1
            data.append([ledger_date, "", "", "", "Daily Total", daily_total])
            data.append([" ", " ", " ", " ", " ", " "])

    except Exception as e:
        print(e)
        data = []

    # Serve the file (if exists) from app/templates/home/FILE.html
    return render_template(
        "home/ui-miningledger.html", segment=segment, data=data
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
