# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""


from apps import login_manager
from shared.models.users import Users

@login_manager.user_loader
def user_loader(character_id):
    return Users.query.filter_by(character_id=character_id).first()


@login_manager.request_loader
def request_loader(request):
    character_name = request.form.get("character_name")
    user = Users.query.filter_by(character_name=character_name).first()
    return user if user else None
