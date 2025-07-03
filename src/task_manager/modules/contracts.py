"""Contract Tasks"""
from datetime import datetime
from models.users import Characters
from models.common import MapRegion
from models.contracts import Contract
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
            seconds=3600,
            id="contracts_main",
            name="contracts_main",
            replace_existing=False,
            max_instances=1
        )
    
    def get_all_users(self) -> list:
        """Gets all characters"""
        with self.scheduler.app.app_context():
            character_list = Characters.query.filter_by(sso_is_valid=True).all()
        return character_list
    
    def get_all_regions(self) -> list:
        """Gets all regions from the database"""
        with self.scheduler.app.app_context():
            regions = MapRegion.query.all()
        return regions

    def main(self):
        """
        Contracts Main
        """
        print(f"Running Contracts Main: {datetime.now()}")
        characters = self.get_all_users()
        regions = self.get_all_regions()
        
        if not characters:
            print("No valid characters found for API access")
            return
        
        # Use first available character for all regions
        # (assuming public contract data doesn't require specific character permissions)
        character = characters[0]
        
        for region in regions:
            print(f"\nProcessing Region: {region.regionName} (ID: {region.regionID})")
            
            try:
                # Get Data for specific region
                esi_params = {"region_id": region.regionID}
                contract_data = esi.get_esi(
                    character, "get_contracts_public_region_id", **esi_params
                )
                
                # Check if we got valid data
                if contract_data and hasattr(contract_data, 'data') and contract_data.data:
                    contracts_saved = 0
                    
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
                            volume=ld.get("volume", None),
                        )
                        with self.scheduler.app.app_context():
                            db.session.merge(contract_row)
                            contracts_saved += 1
                    
                    # Commit after processing all contracts for this region
                    with self.scheduler.app.app_context():
                        db.session.commit()
                    
                    print(f"  Saved {contracts_saved} contracts")
                else:
                    print("  No contracts found")
                    
            except Exception as e:
                print(f"  Error: {str(e)}")
                # Continue with next region even if one fails
                continue
        
        print(f"\nCompleted all regions at: {datetime.now()}")