"""Mining Ledger Tasks"""

from datetime import datetime
from models.characters import Characters, MiningLedger
from models.database import SessionLocal
from ..esi_client import esi


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
            max_instances=1
        )

    def get_all_users(self) -> list:
        """Gets all characters"""
        with SessionLocal() as session:
            character_list = session.query(Characters).filter_by(sso_is_valid=True).all()
        return character_list

    def main(self):
        print(f"Running Mining Ledger Main: {datetime.now()}")

        characters = self.get_all_users()

        for character in characters:
            print(f"Checking: {character.character_name}", end="")

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

                with SessionLocal() as session:
                    session.merge(mining_row)
                    session.commit()

            print("...Done")
