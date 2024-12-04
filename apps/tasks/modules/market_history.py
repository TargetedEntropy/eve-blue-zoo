""" Market History Tasks """

from datetime import timedelta
from apps.authentication.models import MarketHistory, MapRegion, MiningLedger
from apps import esi, db


class MarketHistoryTasks:
    """Tasks related to Market History"""

    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.schedule_tasks()

    def schedule_tasks(self) -> None:
        """Setup task execution schedule"""
        self.scheduler.add_job(
            func=self.main,
            trigger="interval",
            seconds=3600,
            id="market_history_main",
            name="market_history_main",
            replace_existing=True,
        )

    def get_all_regions(self) -> list:
        """Gets all regions"""
        with self.scheduler.app.app_context():
            character_list = MapRegion.query.all()

        return character_list

    def get_unique_type_ids(self) -> list:
        """Get unique Type Ids from Mining Ledger"""
        with self.scheduler.app.app_context():        
            unique_type_ids = db.session.query(db.distinct(MiningLedger.type_id)).all()
        return unique_type_ids

    def main(self):
        print("Running Market History Main")

        from datetime import datetime

        print(f"now = {datetime.now()}")

        item_ids = self.get_unique_type_ids()

        for item_id in item_ids:
            item_id = item_id[0]

            print(f"Checking item_id, {item_id}")
            # Check if we have a record and if its expired
            with self.scheduler.app.app_context():
                type_id_history = (
                    db.session.query(MarketHistory)
                    .filter(MarketHistory.typeID == item_id)
                    .first()
                )

            if type_id_history is not None:

                # Check if the record exists and compare the updated_date, skip if less than 24hrs old
                if (type_id_history.updated_date > (datetime.now() - timedelta(days=1))):
                    continue


            # Get Data
            esi_params = {"region_id": 10000002, "type_id": item_id}

            market_history_data_query = esi.get_esi(character=None, schema="get_markets_region_id_history", **esi_params
            )

            market_history_datas = market_history_data_query.data
    

            for market_history_data in market_history_datas:
                
                with self.scheduler.app.app_context():
                    
                    market_history = MarketHistory(
                        typeID=item_id,
                        regionID=10000002,
                        average=market_history_data["average"],
                        date=market_history_data["date"],
                        highest=market_history_data["highest"],
                        lowest=market_history_data["lowest"],
                        order_count=market_history_data["order_count"],
                        volume=market_history_data["volume"],
                        updated_date=db.func.now()
                    )
                    db.session.merge(market_history)
                    db.session.commit()
