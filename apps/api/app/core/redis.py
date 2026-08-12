import redis.asyncio as redis
from app.core.config import settings

redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=settings.REDIS_MAX_CONNECTIONS,
    decode_responses=True
)

async def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=redis_pool)
