""" Mining Ledger Tasks """

from apps.authentication.models import Characters
from apps import esi

class MiningLedgerTasks:
    """ Tasks related to the Mining Ledger """
    
    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.characters = self.get_all_users()

    def get_all_users(self):
        with self.scheduler.app.app_context():
            character_list = Characters.query.all()
            print(f"characters: {character_list}")

        return character_list

    def get_mining_ledger(self, character_id):
        """Get mining ledger data for a character_id

        Args:
            character_id (_type_): an individual character's id
            
        Returns:
            string: contract data json structure        
        """
        esi_req = self.esiapp.op["get_characters_character_id_mining"](character_id=character_id)
        ledger_req = self.esiclient.request(esi_req)
        return ledger_req.data

    def does_row_exist(self, ledger_data):
        """Check if a contract has been stored

        Args:
            contract_id (Integer): Contract identifier

        Returns:
            boolean: Does it exist or not
        """ 
        query = f"select id from MiningLedger where character_id = {ledger_data['character_id']} and date = '{ledger_data['date']}' and quantity = {ledger_data['quantity']} and solar_system_id = {ledger_data['solar_system_id']} and type_id = {ledger_data['type_id']}"   
        cursor = connection.execute(query)
        data = cursor.fetchone()
        if data:
            return True
        else:
            return False
    
    
    def main(self):
        print("Running Mining Ledger Main")
        # self.init_app(self.scheduler.app)
        for character in self.characters:
            #character_id = character_id[0]

            #character_id, character_name, refresh_token = character
            print(f"Checking: {character.character_name}")



            print("Getting ledger details")
            esi_params = {
                'character_id': character.character_id
            }            
            ledger_data = esi.get_esi(character, "get_characters_character_id_mining", **esi_params)
            for ld in ledger_data.data:
                ld['character_id'] = character.character_id
                print(f"ld: {ld}")
#                if does_row_exist(ld): continue
            #     ledger_query = mining_ledger.insert().values(
            #         character_id = character_id,
            #         date = ld['date'],
            #         quantity = ld['quantity'],
            #         solar_system_id = ld['solar_system_id'],
            #         type_id = ld['type_id']
            #     )
            #     result = connection.execute(ledger_query)
                break

            # print(f"esi_data: {esi_data}")
            
            break