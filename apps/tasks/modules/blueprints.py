"""Blueprint Tasks"""

from datetime import datetime
from apps.authentication.models import Characters, Blueprints
from apps import esi, db
from ..common import invalidate_sso


class BlueprintTasks:
    """Tasks related to Blueprints"""

    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.schedule_tasks()

    def schedule_tasks(self) -> None:
        """Setup task execution schedule"""
        self.scheduler.add_job(
            func=self.main,
            trigger="interval",
            seconds=3600,
            id="blueprint_main",
            name="blueprint_main",
            replace_existing=False,
            max_instances=1
        )

    def get_all_users(self) -> list:
        """Gets all characters"""
        with self.scheduler.app.app_context():
            character_list = Characters.query.filter_by(sso_is_valid=True).all()

        return character_list

    def main(self):
        print(f"Running Blueprint Main: {datetime.now()}")

        characters = self.get_all_users()

        for character in characters:
            print(f"Checking: {character.character_name}", end="")

            try:
                # Get Data
                esi_params = {"character_id": character.character_id}
                blueprint_data = esi.get_esi(
                    character, "get_characters_character_id_blueprints", **esi_params
                )
            except RuntimeError as e:
                print(f"Failed to get ESI data, invalidating user: {e}")
                invalidate_sso(self.scheduler.app, character_id=character.character_id)

            # Save Data
            for ld in blueprint_data.data:
                blueprint_row = Blueprints(
                    character_id=character.character_id,
                    location_flag=ld["location_flag"],
                    location_id=ld["location_id"],
                    material_efficiency=ld["material_efficiency"],
                    quantity=ld["quantity"],
                    runs=ld["runs"],
                    time_efficiency=ld["time_efficiency"],
                    type_id=ld["type_id"],
                )

                with self.scheduler.app.app_context():
                    db.session.merge(blueprint_row)
                    db.session.commit()

            print("...done")
