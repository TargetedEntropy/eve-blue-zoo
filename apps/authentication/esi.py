
#from esipy import App, EsiClient, EsiSecurity
import esipy

class EsiAuth:
    
    def __init__(self):
        self.esisecurity = None
        self.esiclient = None
        self.esiapp = None
        
    
    def init_app(self, app):
        
        
        self.esiapp = esipy.App.create(app.config['ESI_SWAGGER_JSON'])

        # init the security object
        self.esisecurity = esipy.EsiSecurity(
            app=self.esiapp,
            redirect_uri=app.config['ESI_CALLBACK'],
            client_id=app.config['ESI_CLIENT_ID'],
            secret_key=app.config['ESI_SECRET_KEY'],
            headers={"User-Agent": "merriam@gmail.com"}
        )

        # init the client
        self.esiclient = esipy.EsiClient(
            security=self.esisecurity, cache=None, headers={"User-Agent": app.config['ESI_USER_AGENT']}
        )

    def get_wallet(self, current_user):
        """Get a users wallet transactions

        Args:
            current_user (UsersModel): the current user from the Users login_manager Model

        Returns:
            string: json of wallet transactions
        """        
        self.esisecurity.update_token(current_user.get_sso_data())

        op = self.esiapp.op['get_characters_character_id_wallet'](
            character_id=current_user.character_id
        )
        return self.esiclient.request(op)