"""Eve Online Preston ESI Interface"""

import preston
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class EsiAuth:
    """Access to Eve Online's API using Preston"""

    def __init__(self):
        self.client = None
        self.app = None

    def init_app(self, app):
        """Initialize the Preston client with the Flask App

        Args:
            app (obj): The Flask App object
        """
        self.app = app
        
        # Initialize Preston client
        self.client = preston.Preston(
            user_agent=app.config.get("ESI_USER_AGENT", "Eve Blue Zoo/1.0"),
            client_id=app.config["ESI_CLIENT_ID"],
            client_secret=app.config["ESI_SECRET_KEY"],
            callback_url=app.config["ESI_CALLBACK"]
        )
        
        logger.info("Preston ESI client initialized")

    def get_authorize_url(self, scopes=None):
        """Get EVE SSO authorization URL
        
        Args:
            scopes (list): List of ESI scopes to request
            
        Returns:
            tuple: (authorization_url, state)
        """
        if scopes is None:
            scopes = [
                "esi-wallet.read_character_wallet.v1",
                "esi-industry.read_character_mining.v1", 
                "esi-characters.read_blueprints.v1",
                "esi-skills.read_skills.v1",
                "publicData"
            ]
        
        # Preston's get_authorize_url might return a tuple or just URL
        # Let's check what it actually returns
        result = self.client.get_authorize_url(scopes)
        
        # If Preston returns a tuple (url, state), use it
        if isinstance(result, tuple) and len(result) == 2:
            return result
        
        # If Preston returns just the URL, we need to extract state from URL or generate our own
        # For now, let's try to extract state from the URL parameters
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(result)
        query_params = parse_qs(parsed_url.query)
        
        if 'state' in query_params:
            state = query_params['state'][0]
        else:
            # If no state in URL, Preston might handle it internally
            # Let's generate our own for now
            import secrets
            state = secrets.token_urlsafe(32)
        
        return result, state

    def exchange_authorization_code(self, code, state):
        """Exchange authorization code for tokens
        
        Args:
            code (str): Authorization code from EVE SSO
            state (str): State parameter from authorization
            
        Returns:
            dict: Token data including access_token, refresh_token, expires_in
        """
        # Let's try calling Preston's methods directly to get token data
        # Preston might have different method names than expected
        try:
            # Try the most direct approach - manually exchange code for token
            import requests
            import base64
            
            # EVE Online token endpoint
            token_url = "https://login.eveonline.com/v2/oauth/token"
            
            # Prepare authentication
            auth_string = f"{self.app.config['ESI_CLIENT_ID']}:{self.app.config['ESI_SECRET_KEY']}"
            auth_b64 = base64.b64encode(auth_string.encode()).decode()
            
            # Prepare request
            headers = {
                'Authorization': f'Basic {auth_b64}',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Host': 'login.eveonline.com'
            }
            
            data = {
                'grant_type': 'authorization_code',
                'code': code
            }
            
            logger.info(f"Making direct token request to EVE SSO")
            response = requests.post(token_url, headers=headers, data=data)
            
            if response.status_code != 200:
                logger.error(f"Token request failed: {response.status_code} - {response.text}")
                raise RuntimeError(f"Token request failed: {response.status_code}")
            
            token_data = response.json()
            logger.info(f"Successfully got token data: {list(token_data.keys())}")
            
            # Store tokens in Preston client for future use
            if hasattr(self.client, 'access_token'):
                self.client.access_token = token_data.get('access_token')
            if hasattr(self.client, 'refresh_token'):
                self.client.refresh_token = token_data.get('refresh_token')
            
            return token_data
            
        except Exception as e:
            logger.error(f"Direct token exchange failed: {e}")
            raise RuntimeError(f"Failed to exchange authorization code: {e}")

    def refresh_access_token(self, refresh_token):
        """Refresh access token using refresh token
        
        Args:
            refresh_token (str): Refresh token
            
        Returns:
            dict: New token data
        """
        return self.client.refresh_access_token(refresh_token)

    def get_character_info(self, access_token):
        """Get character information from access token
        
        Args:
            access_token (str): Access token
            
        Returns:
            dict: Character information in esipy-compatible format
        """
        logger.info(f"Getting character info for access_token: {access_token}")
        
        if not access_token:
            raise RuntimeError("No access token provided")
        
        # Check if access_token looks like a JWT (has 3 parts separated by dots)
        if isinstance(access_token, str) and access_token.count('.') != 2:
            logger.error(f"Access token doesn't look like JWT: {access_token}")
            raise RuntimeError(f"Access token is not a valid JWT format (segments: {access_token.count('.') + 1})")
        
        # EVE Online access tokens are JWT tokens containing character info
        # Decode directly without verification to get character data
        import jwt
        try:
            # JWT decode expects string, not bytes for newer versions
            decoded = jwt.decode(access_token, options={"verify_signature": False})
            logger.info(f"JWT decoded token: {decoded}")
            
            # Extract character ID from sub field (format: CHARACTER:EVE:123456)
            character_id = None
            if "sub" in decoded and decoded["sub"]:
                sub_parts = decoded["sub"].split(":")
                if len(sub_parts) >= 3:
                    character_id = sub_parts[-1]  # Get the last part (character ID)
            
            # Map JWT fields to expected format
            return {
                "CharacterID": character_id,
                "CharacterName": decoded.get("name", ""),
                "CharacterOwnerHash": decoded.get("owner", ""),
                # Keep original data for debugging
                "_original": decoded
            }
        except Exception as jwt_error:
            logger.error(f"JWT decode failed: {jwt_error}")
            logger.error(f"Token being decoded: {access_token}")
            raise RuntimeError(f"Could not decode access token to get character info: {jwt_error}")

    def get_wallet(self, current_user):
        """Get a users wallet balance

        Args:
            current_user: Character object with access token

        Returns:
            dict: Wallet data
        """
        # Ensure token is valid
        if not self._validate_and_refresh_token(current_user):
            raise RuntimeError("Invalid or expired token")
        
        # Make direct HTTP request
        import requests
        
        endpoint = f"/characters/{current_user.character_id}/wallet/"
        full_url = f"https://esi.evetech.net/latest{endpoint}"
        
        headers = {
            'Authorization': f'Bearer {current_user.access_token}',
            'User-Agent': self.app.config.get("ESI_USER_AGENT", "Eve Blue Zoo/1.0")
        }
        
        response = requests.get(full_url, headers=headers)
        
        if response.status_code != 200:
            raise RuntimeError(f"Wallet request failed: {response.status_code} - {response.text}")
        
        return response.json()

    def get_esi(self, character, schema, **kwargs):
        """Get ESI Data with token refresh.

        Args:
            character: Character object with access token (can be None for public endpoints)
            schema (str): The ESI operation schema to execute
            **kwargs: Parameters to pass to the ESI operation

        Returns:
            Preston response object with .data attribute

        Raises:
            RuntimeError: If the token refresh or ESI request fails
        """
        try:
            # Handle token validation for authenticated requests
            if character is not None:
                if not self._validate_and_refresh_token(character):
                    raise RuntimeError(f"Invalid token for character {character.character_name}")
                access_token = character.access_token
            else:
                access_token = None

            # Map schema to endpoint
            endpoint = self._schema_to_endpoint(schema, **kwargs)
            
            # Make direct HTTP request since Preston doesn't have a request method
            import requests
            
            # Build full URL
            base_url = "https://esi.evetech.net/latest"
            full_url = f"{base_url}{endpoint}"
            
            # Set up headers
            headers = {
                'User-Agent': self.app.config.get("ESI_USER_AGENT", "Eve Blue Zoo/1.0")
            }
            
            if access_token:
                headers['Authorization'] = f'Bearer {access_token}'
            
            logger.info(f"Making ESI request to: {full_url}")
            response = requests.get(full_url, headers=headers)
            
            if response.status_code != 200:
                raise RuntimeError(f"ESI request failed: {response.status_code} - {response.text}")
            
            response_data = response.json()
            
            # Wrap response to match esipy interface
            class EsiResponse:
                def __init__(self, data):
                    self.data = data
            
            return EsiResponse(response_data)
            
        except Exception as error:
            message = f"Error executing ESI request for schema '{schema}': {error}"
            logger.error(message)
            raise RuntimeError(message) from error

    def _validate_and_refresh_token(self, character):
        """Validate token and refresh if needed
        
        Args:
            character: Character object with token data
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        try:
            # Check if token is expired (with 5 minute buffer)
            if hasattr(character, 'access_token_expires'):
                expires_at = character.access_token_expires
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                
                if expires_at <= datetime.utcnow() + timedelta(minutes=5):
                    # Token needs refresh
                    if hasattr(character, 'refresh_token') and character.refresh_token:
                        token_data = self.refresh_access_token(character.refresh_token)
                        
                        # Update character with new token
                        character.access_token = token_data['access_token']
                        if 'refresh_token' in token_data:
                            character.refresh_token = token_data['refresh_token']
                        
                        # Calculate expiration time
                        expires_in = token_data.get('expires_in', 1200)
                        character.access_token_expires = datetime.utcnow() + timedelta(seconds=expires_in)
                        
                        logger.info(f"Refreshed token for character {character.character_name}")
                        return True
                    else:
                        logger.warning(f"No refresh token available for character {character.character_name}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Token validation failed for character {character.character_name}: {e}")
            return False

    def _schema_to_endpoint(self, schema, **kwargs):
        """Convert esipy schema name to Preston endpoint
        
        Args:
            schema (str): esipy schema name
            **kwargs: Parameters for the endpoint
            
        Returns:
            str: Preston endpoint URL
        """
        # Map common esipy schemas to Preston endpoints
        schema_map = {
            'get_characters_character_id_wallet': '/characters/{character_id}/wallet/',
            'get_characters_character_id_skills': '/characters/{character_id}/skills/',
            'get_characters_character_id_blueprints': '/characters/{character_id}/blueprints/',
            'get_characters_character_id_mining': '/characters/{character_id}/mining/',
            'get_contracts_public_region_id': '/contracts/public/{region_id}/',
            'get_contracts_public_items_contract_id': '/contracts/public/items/{contract_id}/',
            'get_markets_region_id_history': '/markets/{region_id}/history/',
            'get_markets_region_id_orders': '/markets/{region_id}/orders/'
        }
        
        if schema not in schema_map:
            raise ValueError(f"Unknown schema: {schema}")
        
        endpoint = schema_map[schema]
        
        # Format endpoint with parameters
        try:
            return endpoint.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing parameter for schema {schema}: {e}")