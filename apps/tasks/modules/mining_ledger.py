""" Mining Ledger Tasks """

from datetime import datetime
from apps.authentication.models import Characters, MiningLedger
from apps import esi, db

class MiningLedgerTasks:
    """Tasks related to the Mining Ledger"""

    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.schedule_tasks()

    def schedule_tasks(self) -> None:
        """Setup task execution schedule"""
        self.scheduler.add_job(
            func=self.main,
            trigger="interval",
            seconds=3600,
            id="mining_ledger_main",
            name="mining_ledger_main",
            replace_existing=False,
        )

    def get_all_users(self) -> list:
        """Gets all characters"""
        with self.scheduler.app.app_context():
            character_list = Characters.query.filter_by(sso_is_valid=True).all()
        return character_list

    def main(self):
        print("Running Mining Ledger Main")

        from datetime import datetime

        print(f"now = {datetime.now()}")

        characters = self.get_all_users()

        for character in characters:

            # Get Data
            esi_params = {"character_id": character.character_id}
            ledger_data = esi.get_esi(
                character, "get_characters_character_id_mining", **esi_params
            )

            # Save Data
            for ld in ledger_data.data:
                mining_row = MiningLedger(
                    character_id=character.character_id,
                    date=ld["date"],
                    quantity=ld["quantity"],
                    solar_system_id=ld["solar_system_id"],
                    type_id=ld["type_id"],
                )

                with self.scheduler.app.app_context():
                    db.session.merge(mining_row)
                    db.session.commit()
