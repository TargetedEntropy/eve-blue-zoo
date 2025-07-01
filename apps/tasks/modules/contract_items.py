"""Contract Tasks"""

from datetime import datetime
from apps.authentication.models import Characters, Contract, ContractItem
from apps import esi, db
from sqlalchemy.orm import aliased
from sqlalchemy.sql import func


class ContractItemTasks:
    """Tasks related to Contract Items"""

    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.schedule_tasks()

    def schedule_tasks(self) -> None:
        """Setup task execution schedule"""
        self.scheduler.add_job(
            func=self.main,
            trigger="interval",
            seconds=300,
            id="contract_item_main",
            name="contract_item_main",
            replace_existing=False,
        )

    def get_all_users(self) -> list:
        """Gets all characters"""
        with self.scheduler.app.app_context():
            character_list = Characters.query.filter_by(sso_is_valid=True).all()
        return character_list

    def get_contracts_without_items(self) -> list:
        """Get contracts without items, we need to get the items"""
        with self.scheduler.app.app_context():
            contracts_without_items = (
                Contract.query.outerjoin(
                    ContractItem, Contract.id == ContractItem.contract_id
                )
                .filter(ContractItem.contract_id.is_(None))
                .all()
            )
        #                .limit(50) \

        return contracts_without_items

    def main(self):
        print(f"Running Contract Items Main: {datetime.now()}")

        characters = self.get_all_users()

        for character in characters:
            print(f"Checking: {character.character_name}", end="")

            contracts = self.get_contracts_without_items()
            for contract in contracts:
                # Get Data
                if contract.type not in ["item_exchange", "auction"]:
                    continue
                print(f"Checking: {contract.id}")
                esi_params = {"contract_id": contract.id}

                try:
                    esi_data = esi.get_esi(
                        character,
                        "get_contracts_public_items_contract_id",
                        **esi_params,
                    )
                except Exception as error:
                    continue

                if hasattr(esi_data.data, "error"):
                    continue

                # Save Data
                for ld in esi_data.data:
                    contract_item_row = ContractItem(
                        contract_id=contract.id,
                        record_id=ld.get("record_id", None),
                        is_blueprint_copy=ld.get("is_blueprint_copy", None),
                        is_included=ld.get("is_included", None),
                        item_id=ld.get("item_id", None),
                        material_efficiency=ld.get("material_efficiency", None),
                        quantity=ld.get("quantity", None),
                        runs=ld.get("runs", None),
                        time_efficiency=ld.get("time_efficiency", None),
                        type_id=ld.get("type_id", None),
                    )

                    with self.scheduler.app.app_context():
                        db.session.merge(contract_item_row)
                        db.session.commit()

            print("...Done")
