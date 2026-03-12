from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import valkey
import os
import time

class ValkeyRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        
        valkey_host = os.environ.get("VALKEY_HOST", "localhost")
        valkey_port = int(os.environ.get("VALKEY_PORT", 6379))
        
        self.rate_limit_requests = int(os.environ.get("RATE_LIMIT_REQUESTS", 5))
        self.rate_limit_window = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", 60))
        
        self.client = valkey.Valkey(host=valkey_host, port=valkey_port, db=0, decode_responses=True)
        
    async def dispatch(self, request: Request, call_next):
        
        # Skip rate limiting for public endpoints if we don't have a user_id
        # Note: Depending on the middleware order, user_id should be set by Auth Middleware
        if not hasattr(request.state, "user_id"):
            return await call_next(request)
            
        user_id = request.state.user_id
        
        # Use a fixed window strategy based on the current minute
        # For example, if time is 10:45:30, window is based on 10:45:00
        current_time_bucket = int(time.time() // self.rate_limit_window)
        
        redis_key = f"rate_limit:{user_id}:{current_time_bucket}"
        
        try:
            # Increment the request count for this user in this bucket
            # Pipeline is used to execute both commands atomically
            pipeline = self.client.pipeline()
            pipeline.incr(redis_key)
            # Set expiration so Valkey cleans up old keys (window + 10s buffer)
            pipeline.expire(redis_key, self.rate_limit_window + 10)
            
            result = pipeline.execute()
            
            # The result of incr is the first item
            request_count = result[0]
            
            if request_count > self.rate_limit_requests:
                return JSONResponse(
                    status_code=429,
                    content={"detail": f"Rate limit exceeded. Maximum {self.rate_limit_requests} requests per {self.rate_limit_window} seconds."}
                )
                
        except valkey.exceptions.ConnectionError:
            # If Valkey is down, you might want to allow the request or fail open/closed
            # Here we fail open, logging could be added
            print("Valkey connection failed, bypassing rate limit")
            
        response = await call_next(request)
        return response
