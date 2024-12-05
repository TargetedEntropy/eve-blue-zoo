""" Skill Tasks """

from apps.authentication.models import Characters, SkillSet
from apps import esi, db
from ..common import is_feature_enabled

class SkillTasks:
    """Tasks related to Skills"""

    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.schedule_tasks()

    def schedule_tasks(self) -> None:
        """Setup task execution schedule"""
        self.scheduler.add_job(
            func=self.main,
            trigger="interval",
            seconds=43200,
            id="skill_main",
            name="skill_main",
            replace_existing=False,
        )

    def get_all_users(self) -> list:
        """Gets all characters"""
        with self.scheduler.app.app_context():
            character_list = Characters.query.all()

        return character_list

    def main(self):
        print("Running Skill Main")

        from datetime import datetime

        print(f"now = {datetime.now()}")

        characters = self.get_all_users()

        for character in characters:

            if not is_feature_enabled(self.scheduler.app, character.character_id, "skills"):
                print(f"Skill feature not enabled for: {character.character_name}")
                continue
            
            # Get Data
            esi_params = {"character_id": character.character_id}
            skill_data = esi.get_esi(
                character, "get_characters_character_id_skills", **esi_params
            )

            ld = skill_data.data

            with self.scheduler.app.app_context():
                skillset = (
                    db.session.query(SkillSet)
                    .filter_by(character_id=character.character_id)
                    .first()
                )

            if skillset:
                # Update the fields
                skillset.total_sp = ld["total_sp"]
                skillset.unallocated_sp = ld["unallocated_sp"]

                # Commit the changes
                with self.scheduler.app.app_context():
                    db.session.commit()

            else:
                skill_row = SkillSet(
                    character_id=character.character_id,
                    total_sp=ld["total_sp"],
                    unallocated_sp=ld["unallocated_sp"],
                )

                with self.scheduler.app.app_context():
                    db.session.merge(skill_row)
                    db.session.commit()
