""" Mining Ledger Tasks """

from apps.authentication.models import Characters

class MiningLedgerTasks:
    """ Tasks related to the Mining Ledger """
    
    def __init__(self):
        self.characters = self.get_all_users()
        

    def get_all_users(self):
        character_list = Characters.query.all()
        # cursor = connection.execute(
        #     f"select character_id,character_name,refresh_token from Characters"
        # )

        # character_list = cursor.fetchall()
        return character_list

    def get_mining_ledger(character_id):
        """Get mining ledger data for a character_id

        Args:
            character_id (_type_): an individual character's id
            
        Returns:
            string: contract data json structure        
        """
        esi_req = esiapp.op["get_characters_character_id_mining"](character_id=character_id)
        ledger_req = esiclient.request(esi_req)
        return ledger_req.data

    def does_row_exist(ledger_data):
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
        for character in self.characters:
            #character_id = character_id[0]

            character_id, character_name, refresh_token = character
            print(f"Checking: {character_name}")
            # print(character_id)
            # print(character_name)
            
            # print("Refreshing the token")
            # token = refresh_esi_token(refresh_token)
            
            # print("Getting ledger details")
            # ledger_data = get_mining_ledger(character_id)
            # for ld in ledger_data:
            #     ld['character_id'] = character_id
            #     if does_row_exist(ld): continue
            #     ledger_query = mining_ledger.insert().values(
            #         character_id = character_id,
            #         date = ld['date'],
            #         quantity = ld['quantity'],
            #         solar_system_id = ld['solar_system_id'],
            #         type_id = ld['type_id']
            #     )
            #     result = connection.execute(ledger_query)
                