"""Skill Tasks"""

from datetime import datetime
from models.characters import Characters, SkillSet
from models.database import SessionLocal
from ..esi_client import esi
from ..common import invalidate_sso


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
            seconds=3600,
            id="skill_main",
            name="skill_main",
            replace_existing=False,
        )

    def get_all_users(self) -> list:
        """Gets all characters"""
        with SessionLocal() as session:
            character_list = session.query(Characters).filter_by(sso_is_valid=True).all()

        return character_list

    def main(self):
        print(f"Running Skill Main: {datetime.now()}")

        characters = self.get_all_users()

        for character in characters:
            print(f"Checking: {character.character_name}", end="")

            # Get Data
            esi_params = {"character_id": character.character_id}
            try:
                skill_data = esi.get_esi(
                    character, "get_characters_character_id_skills", **esi_params
                )
            except RuntimeError as e:
                print(f"Failed to get ESI data, invalidating user: {e}")
                invalidate_sso(self.scheduler.app, character_id=character.character_id)
                continue
            ld = skill_data.data

            with SessionLocal() as session:
                skillset = (
                    session.query(SkillSet)
                    .filter_by(character_id=character.character_id)
                    .first()
                )

            if skillset:
                # Update the fields
                skillset.total_sp = ld["total_sp"]
                skillset.unallocated_sp = ld["unallocated_sp"]

                # Commit the changes
                with SessionLocal() as session:
                    try:
                        session.merge(skillset)
                        session.commit()
                    except Exception as error:
                        print(f"Failed to commit row: {skillset}, error: {error}")

            else:
                skill_row = SkillSet(
                    character_id=character.character_id,
                    total_sp=ld["total_sp"],
                    unallocated_sp=ld["unallocated_sp"],
                )

                with SessionLocal() as session:
                    try:
                        session.merge(skill_row)
                        session.commit()
                    except Exception as error:
                        print(f"Failed to commit row: {skill_row}, error: {error}")

            print("...done")
