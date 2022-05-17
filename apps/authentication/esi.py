
#from esipy import App, EsiClient, EsiSecurity
import esipy

class EsiAuth:
    
    def __init__(self):
        self.esisecurity = None
        self.esiclient = None
        
    
    def init_app(self, app):
        
        
        esiapp = esipy.App.create(app.config['ESI_SWAGGER_JSON'])

        # init the security object
        self.esisecurity = esipy.EsiSecurity(
            app=esiapp,
            redirect_uri=app.config['ESI_CALLBACK'],
            client_id=app.config['ESI_CLIENT_ID'],
            secret_key=app.config['ESI_SECRET_KEY'],
            headers={"User-Agent": "merriam@gmail.com"}
        )

        # init the client
        self.esiclient = esipy.EsiClient(
            security=self.esisecurity, cache=None, headers={"User-Agent": app.config['ESI_USER_AGENT']}
        )
        