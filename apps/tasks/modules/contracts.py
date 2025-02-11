"""Contract Tasks"""

from datetime import datetime
from apps.authentication.models import Characters, Contract
from apps import esi, db


class ContractTasks:
    """Tasks related to Contracts"""

    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.schedule_tasks()

    def schedule_tasks(self) -> None:
        """Setup task execution schedule"""
        self.scheduler.add_job(
            func=self.main,
            trigger="interval",
            seconds=30,
            id="contracts_main",
            name="contracts_main",
            replace_existing=False,
        )

    def get_all_users(self) -> list:
        """Gets all characters"""
        with self.scheduler.app.app_context():
            character_list = Characters.query.filter_by(sso_is_valid=True).all()
        return character_list

    def main(self):
        print(f"Running Contracts Main: {datetime.now()}")

        characters = self.get_all_users()

        for character in characters:
            print(f"Checking: {character.character_name}", end="")

            # Get Data
            esi_params = {"region_id": 10000066}
            contract_data = esi.get_esi(
                character, "get_contracts_public_region_id", **esi_params
            )
            
            # Save Data
            for ld in contract_data.data:
                contract_row = Contract(
                    id=ld["contract_id"],
                    buyout=ld.get("buyout", None),
                    collateral=ld.get("collateral", None),
                    date_expired=ld["date_expired"],
                    date_issued=ld["date_issued"],               
                    days_to_complete=ld.get("days_to_complete", None),
                    end_location_id=ld.get("end_location_id", None),
                    for_corporation=ld.get("for_corporation", False),
                    issuer_corporation_id=ld.get("issuer_corporation_id", None),
                    issuer_id=ld.get("issuer_id", None),
                    price=ld.get("price", None),
                    reward=ld.get("reward", None),
                    start_location_id=ld.get("start_location_id", None),
                    title=ld.get("title", None),
                    type=ld.get("type", None),
                    volume=ld.get("volume", None)
                )


                with self.scheduler.app.app_context():
                    db.session.merge(contract_row)
                    db.session.commit()

            print("...Done")
