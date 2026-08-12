"""
Rate limiting middleware using Redis sorted sets (sliding window algorithm).

Limits requests per IP address per minute. Gracefully degrades
when Redis is unavailable (allows all requests through).
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.config import settings
import time


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter backed by Redis sorted sets."""

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)

        try:
            from app.core.redis import get_redis
            redis = await get_redis()

            client_ip = request.client.host if request.client else "unknown"
            key = f"rate_limit:{client_ip}"

            current_time = int(time.time() * 1000)  # millisecond precision
            window_start = current_time - 60_000  # 60 second window

            pipeline = redis.pipeline()
            pipeline.zremrangebyscore(key, 0, window_start)
            pipeline.zcard(key)
            pipeline.zadd(key, {str(current_time): current_time})
            pipeline.expire(key, 120)  # TTL slightly longer than window
            results = await pipeline.execute()

            request_count = results[1]

            if request_count >= settings.RATE_LIMIT_PER_MINUTE:
                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": f"Rate limit exceeded. Maximum {settings.RATE_LIMIT_PER_MINUTE} requests per minute.",
                        },
                    },
                )
        except Exception:
            # If Redis is unavailable, allow the request through
            pass

        return await call_next(request)

