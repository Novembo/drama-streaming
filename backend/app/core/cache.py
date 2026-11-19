import json
import logging

try:
    from redis import Redis
    from redis.exceptions import RedisError
except ImportError:  # allows API development without Redis installed
    Redis = None

    class RedisError(Exception):
        pass


from app.core.config import settings

logger = logging.getLogger(__name__)
_client = None


def client():
    global _client
    if Redis is None:
        raise RedisError("redis package not installed")
    if _client is None:
        _client = Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=0.25,
            socket_timeout=0.25,
            decode_responses=True,
        )
    return _client


def get_json(key: str):
    try:
        value = client().get(key)
        return json.loads(value) if value else None
    except (RedisError, ValueError):
        logger.warning("redis_cache_read_failed", exc_info=True)
        return None


def set_json(key: str, value, ttl: int = 60):
    try:
        client().setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))
    except RedisError:
        logger.warning("redis_cache_write_failed", exc_info=True)


def invalidate(prefix: str):
    try:
        r = client()
        for key in r.scan_iter(match=f"{prefix}*", count=100):
            r.delete(key)
    except RedisError:
        logger.warning("redis_cache_invalidate_failed", exc_info=True)
