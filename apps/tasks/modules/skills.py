""" Skill Tasks """

from apps.authentication.models import Characters, SkillSet#, Skill
from apps import esi, db


class SkillTasks:
    """Tasks related to Skills"""

    def __init__(self, scheduler):

        self.scheduler = scheduler
        self.characters = self.get_all_users()

        self.schedule_tasks()

    def schedule_tasks(self) -> None:
        """Setup task execution schedule"""
        self.scheduler.add_job(
            func=self.main,
            trigger="interval",
            seconds=30,
            id="skill_main",
            name="skill_main",
            replace_existing=True,
        )

    def get_all_users(self) -> list:
        """Gets all characters"""
        with self.scheduler.app.app_context():
            character_list = Characters.query.all()
            print(f"characters: {character_list}")

        return character_list

    def main(self):
        print("Running Skill Main")

        from datetime import datetime
        print(f"now = {datetime.now()}")

        for character in self.characters:
            print(f"Checking: {character.character_name}")

            # Get Data
            esi_params = {"character_id": character.character_id}
            skill_data = esi.get_esi(
                character, "get_characters_character_id_skills", **esi_params
            )

            ld = skill_data.data

            with self.scheduler.app.app_context():
                skillset = db.session.query(SkillSet).filter_by(character_id=character.character_id).first()

            if skillset:
                # Update the fields
                skillset.total_sp = ld["total_sp"]
                skillset.unallocated_sp = ld["unallocated_sp"]
                
                # Commit the changes
                with self.scheduler.app.app_context():
                    db.session.commit()
                print(f"Updated SkillSet for character, {character.character_name}")
            else:
                skill_row = SkillSet(
                    character_id=character.character_id,
                    total_sp=ld["total_sp"],
                    unallocated_sp=ld["unallocated_sp"]
                    )


                with self.scheduler.app.app_context():
                    db.session.merge(skill_row)
                    db.session.commit()                
