# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import aliased
from sqlalchemy import distinct, desc
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
    BlueprintLongDurationOrder,
    StaStation
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
        "home/page-user.html",
        segment=segment,
        characters=characters,
        discord_id=discord_id,
    )


@blueprint.route("/page-contracts.html", methods=["GET", "POST"])
def display_contract_selection():
    # Detect the current page
    segment = get_segment(request)

    if request.method == "POST":
        pass

    return render_template("home/page-contracts.html", segment=segment)


@blueprint.route("/autocomplete", methods=["GET"])
def autocomplete():
    query = request.args.get("query", "").strip()
    if not query:
        return jsonify([])

    results = InvType.query.filter(InvType.typeName.ilike(f"%{query}%")).limit(10).all()

    return jsonify(
        [{"typeID": item.typeID, "typeName": item.typeName} for item in results]
    )


@blueprint.route("/page-character.html", methods=["POST"])
@login_required
def page_character_post():
    # Detect the current page
    segment = get_segment(request)
    character_id = request.form["character_id"]
    print(f"segment: {segment}")
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
        print(f"Error: {e}")
        date_list = []

    # Serve the template
    return render_template(
        "home/ui-miningledger.html", segment=segment, date_list=date_list
    )


@blueprint.route("/ui-blueprints.html")
@login_required
def page_blueprints():
    # Detect the current page
    segment = get_segment(request)
    page = request.args.get(
        "page", 1, type=int
    )  # Get the page number from the query string (default to 1)
    per_page = 100  # Number of blueprints per page

    # Get All of the users' Characters
    try:
        characters = Characters.query.filter(
            Characters.master_character_id == current_user.character_id
        ).all()
    except NoResultFound:
        characters = []

    # Get all character IDs
    character_ids = [character.character_id for character in characters]

    if not character_ids:
        return render_template(
            "home/ui-blueprints.html",
            segment=segment,
            data=[],
            page=page,
            total_pages=0,
        )

    # Total number of blueprints for these characters
    total_blueprints = Blueprints.query.filter(
        Blueprints.character_id.in_(character_ids)
    ).count()

    # Calculate total pages
    total_pages = (total_blueprints + per_page - 1) // per_page  # Round up division

    # Fetch blueprints for the current page
    blueprints = (
        Blueprints.query.filter(Blueprints.character_id.in_(character_ids))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    # Fetch all item names in one query
    type_ids = {bp.type_id for bp in blueprints}
    item_names = {
        item.typeID: item.typeName
        for item in InvType.query.filter(InvType.typeID.in_(type_ids)).all()
    }

    # Build the final list
    character_map = {
        character.character_id: character.character_name for character in characters
    }
    all_blueprints = []
    for bp in blueprints:
        bp.characterName = character_map.get(bp.character_id, "Unknown")
        bp.itemName = item_names.get(bp.type_id, "Unknown")
        all_blueprints.append(bp)

    # Serve the file (if exists) from app/templates/home/FILE.html
    return render_template(
        "home/ui-blueprints.html",
        segment=segment,
        data=all_blueprints,
        page=page,
        total_pages=total_pages,
    )

# Helper - Extract current page name from request
def get_segment(req):
    try:
        segment = req.path.split("/")[-1]

        if segment == "":
            segment = "index"

        return segment

    except BaseException:
        return None

@blueprint.route("/page-bp-finder.html", methods=['GET', 'POST'])
@login_required
def bp_finder():
    # Detect the current page
    segment = get_segment(request)
    
    # Initialize variables
    missing_blueprints = []
    system_name = None
    search_radius = 5  # Default search radius in jumps
    
    if request.method == 'POST':
        system_name = request.form.get('system_name', '').strip()
        search_radius = int(request.form.get('search_radius', 5))
        
        if system_name:
            # Get all character IDs for the current user
            user_characters = db.session.query(Characters.character_id).filter(
                Characters.master_character_id == current_user.character_id
            ).all()
            user_character_ids = [char.character_id for char in user_characters]
            print(f"user_character_ids: {user_character_ids}")
            # Get all blueprint type_ids owned by the user's characters
            owned_blueprints = db.session.query(Blueprints.type_id).filter(
                Blueprints.character_id.in_(user_character_ids)
            ).distinct().all()
            owned_type_ids = [bp.type_id for bp in owned_blueprints]
            print(f"owned_type_ids: {owned_type_ids}")
            print(f"owned_type_ids_len: {len(owned_type_ids)}")
            
            # Find the system by name
            target_system = db.session.query(MapSolarSystems).filter(
                MapSolarSystems.solarSystemName.ilike(f'%{system_name}%')
            ).first()
            
            if target_system:
                # Get blueprint orders not owned by the user
                query = db.session.query(
                    BlueprintLongDurationOrder,
                    MapSolarSystems,
                    StaStation,
                    InvType
                ).join(
                    MapSolarSystems,
                    BlueprintLongDurationOrder.system_id == MapSolarSystems.solarSystemID
                ).outerjoin(
                    StaStation,
                    BlueprintLongDurationOrder.location_id == StaStation.stationID
                ).join(
                    InvType,
                    BlueprintLongDurationOrder.type_id == InvType.typeID
                ).filter(
                    ~BlueprintLongDurationOrder.type_id.in_(owned_type_ids) if owned_type_ids else True,
                    BlueprintLongDurationOrder.is_buy_order == False  # Only sell orders
                )
                
                # If search_radius is 0, only search in the exact system
                if search_radius == 0:
                    query = query.filter(
                        BlueprintLongDurationOrder.system_id == target_system.solarSystemID
                    )
                else:
                    # For radius search, we'll need to implement a more complex filter
                    # For now, let's search within the same constellation or region
                    if search_radius <= 5:
                        # Search within constellation
                        query = query.filter(
                            MapSolarSystems.constellationID == target_system.constellationID
                        )
                    else:
                        # Search within region
                        query = query.filter(
                            MapSolarSystems.regionID == target_system.regionID
                        )
                
                # Order by price
                query = query.order_by(BlueprintLongDurationOrder.price.asc())
                
                # Execute query and format results
                results = query.limit(100).all()  # Limit to prevent overwhelming results
                
                for order, system, station, item_type in results:
                    blueprint_info = {
                        'order_id': order.order_id,
                        'type_id': order.type_id,
                        'type_name': item_type.typeName,
                        'price': order.price / 100,  # Convert from cents to ISK
                        'location_id': order.location_id,
                        'system_name': system.solarSystemName,
                        'system_security': round(system.security, 1),
                        'region_id': system.regionID,
                        'constellation_id': system.constellationID,
                        'station_name': station.stationName if station else 'Citadel/Structure',
                        'duration': order.duration,
                        'last_updated': order.last_updated
                    }
                    missing_blueprints.append(blueprint_info)
    
    # Serve the template with results
    return render_template(
        "home/page-bp-finder.html",
        segment=segment,
        missing_blueprints=missing_blueprints,
        system_name=system_name,
        search_radius=search_radius,
        results_count=len(missing_blueprints)
    )


# Optional: Add an API endpoint for AJAX requests
@blueprint.route("/api/bp-finder", methods=['POST'])
@login_required
def api_bp_finder():
    """API endpoint for finding missing blueprints"""
    data = request.get_json()
    system_name = data.get('system_name', '').strip()
    search_radius = int(data.get('search_radius', 5))
    max_price = data.get('max_price')  # Optional price filter
    
    if not system_name:
        return jsonify({'error': 'System name is required'}), 400
    
    # Get all character IDs for the current user
    user_characters = db.session.query(Characters.character_id).filter(
        Characters.master_character_id == current_user.character_id
    ).all()
    user_character_ids = [char.character_id for char in user_characters]
    
    # Get all blueprint type_ids owned by the user's characters
    owned_blueprints = db.session.query(Blueprints.type_id).filter(
        Blueprints.character_id.in_(user_character_ids)
    ).distinct().all()
    owned_type_ids = [bp.type_id for bp in owned_blueprints]
    
    # Find the system
    target_system = db.session.query(MapSolarSystems).filter(
        MapSolarSystems.solarSystemName.ilike(f'%{system_name}%')
    ).first()
    
    if not target_system:
        return jsonify({'error': f'System "{system_name}" not found'}), 404
    
    # Build the query
    query = db.session.query(
        BlueprintLongDurationOrder,
        MapSolarSystems,
        StaStation,
        InvType
    ).join(
        MapSolarSystems,
        BlueprintLongDurationOrder.system_id == MapSolarSystems.solarSystemID
    ).outerjoin(
        StaStation,
        BlueprintLongDurationOrder.location_id == StaStation.stationID
    ).join(
        InvType,
        BlueprintLongDurationOrder.type_id == InvType.typeID
    ).filter(
        ~BlueprintLongDurationOrder.type_id.in_(owned_type_ids) if owned_type_ids else True,
        BlueprintLongDurationOrder.is_buy_order == False
    )
    
    # Apply price filter if provided
    if max_price:
        query = query.filter(BlueprintLongDurationOrder.price <= max_price * 100)  # Convert to cents
    
    # Apply location filter based on radius
    if search_radius == 0:
        query = query.filter(
            BlueprintLongDurationOrder.system_id == target_system.solarSystemID
        )
    elif search_radius <= 5:
        query = query.filter(
            MapSolarSystems.constellationID == target_system.constellationID
        )
    else:
        query = query.filter(
            MapSolarSystems.regionID == target_system.regionID
        )
    
    # Order by price and limit results
    query = query.order_by(BlueprintLongDurationOrder.price.asc()).limit(100)
    
    results = []
    for order, system, station, item_type in query.all():
        results.append({
            'order_id': order.order_id,
            'type_id': order.type_id,
            'type_name': item_type.typeName,
            'price': order.price / 100,
            'location': {
                'location_id': order.location_id,
                'system_name': system.solarSystemName,
                'system_security': round(system.security, 1),
                'station_name': station.stationName if station else 'Citadel/Structure'
            },
            'duration': order.duration,
            'last_updated': order.last_updated.isoformat()
        })
    
    return jsonify({
        'success': True,
        'results': results,
        'count': len(results),
        'search_params': {
            'system': target_system.solarSystemName,
            'radius': search_radius,
            'max_price': max_price
        }
    })


# Helper function to calculate jump distance between systems (optional enhancement)
def calculate_jump_distance(system1_id, system2_id):
    """
    Calculate the number of jumps between two systems.
    This would require additional EVE static data tables for jump connections.
    """
    # This is a placeholder - you would need the actual jump connection data
    # from EVE's static data export to implement this properly
    pass