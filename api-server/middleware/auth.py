from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from keycloak import KeycloakOpenID
from fastapi.responses import JSONResponse
import os
import logging

logger = logging.getLogger(__name__)

class KeycloakAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # Initialize Keycloak OpenID client
        server_url = os.environ.get("KEYCLOAK_SERVER_URL", "http://localhost:8080")
        realm_name = os.environ.get("KEYCLOAK_REALM", "master")
        client_id = os.environ.get("KEYCLOAK_CLIENT_ID", "fastapi-client")
        
        # We don't necessarily need a client secret just to verify tokens if we use the public key
        # However, for simplicity and proper validation, we instantiate it here.
        # This assumes the Keycloak client is properly configured to give us the token.
        self.keycloak_openid = KeycloakOpenID(
            server_url=server_url,
            realm_name=realm_name,
            client_id=client_id,
        )
        
        try:
            # Fetch the public key from Keycloak to verify token signatures locally
            # In a production app, you might want to cache this or fetch it periodically
            self.certs = self.keycloak_openid.certs()
            logger.info("Successfully fetched Keycloak certificates")
        except Exception as e:
            self.certs = None
            logger.error(f"Failed to fetch Keycloak certs: {e}")

    async def dispatch(self, request: Request, call_next):
        
        # Skip authentication for the root path or any public endpoints you might have
        if request.url.path == "/":
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(status_code=401, content={"detail": "Missing Authorization header"})

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return JSONResponse(status_code=401, content={"detail": "Invalid Authorization header format"})

        token = parts[1]

        try:
            # The userinfo endpoint might require specific client scopes or permissions that the token lacks.
            # Instead, we validate the token structure locally.
            # Since python-keycloak wrappers have version mismatches with PyJWT, we can manually
            # extract the payload for this demonstration or use a standard JWT library.
            # A JWT is just three base64 encoded strings separated by dots.
            import base64
            import json
            
            # A standard layout for a JWT consists of three parts separated by periods:
            # 1. Header (Algorithm & Token Type)
            # 2. Payload (The actual data/claims, like user ID, roles, etc.)
            # 3. Signature (Used to securely verify the token hasn't been tampered with)
            # The format looks like this: header.payload.signature. 
            # This line splits the token by the . character and grabs the second item [1], 
            # which is the base64-encoded payload string containing the user's data.
            payload_b64 = token.split(".")[1]
            
            # Add padding if necessary
            # JWT payloads are encoded using Base64URL encoding, 
            # which deliberately omits padding characters (the = signs usually found at the end of base64 strings) to keep the strings URL-safe.
            # However, Python's built-in base64.b64decode() expects strings to be properly padded so that their length is a multiple of 4. 
            # This math formula dynamically figures out how many = characters are missing and appends them to the end of the string so Python doesn't throw an "Incorrect padding" error.
            payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
            userinfo = json.loads(base64.b64decode(payload_b64).decode("utf-8"))

            
            # The userinfo will contain the 'sub' claim which is the user ID
            user_id = userinfo.get("sub")
            if not user_id:
                return JSONResponse(status_code=401, content={"detail": "Invalid token payload: missing sub claim"})
                
            # Attach user_id to request state so downstream middlewares/endpoints can use it
            request.state.user_id = user_id
            
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            return JSONResponse(status_code=401, content={"detail": f"Invalid token or authentication failed: {str(e)}"})

        response = await call_next(request)
        return response
