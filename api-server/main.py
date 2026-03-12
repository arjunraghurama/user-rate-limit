from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from middleware.auth import KeycloakAuthMiddleware
from middleware.rate_limit import ValkeyRateLimitMiddleware
import os
import uvicorn

app = FastAPI(title="Rate Limited API with Keycloak")

# Add Middlewares
# Note: Middlewares are executed in reverse order of addition
# So RateLimitMiddleware will be executed BEFORE AuthMiddleware on the way IN
# But since AuthMiddleware extracts the user info, RateLimit needs it. 
# Therefore AuthMiddleware should process the request FIRST.
# In FastAPI, the LAST added middleware executes FIRST.
app.add_middleware(ValkeyRateLimitMiddleware)
app.add_middleware(KeycloakAuthMiddleware)

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}

@app.get("/api/data")
async def get_data(request: Request):
    # The user_id is injected by the Auth Middleware
    user_id = request.state.user_id
    return {
        "message": "Here is your rate-limited data!",
        "user_id": user_id
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
