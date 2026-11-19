"""Fixed-window rate limiting on Redis. Fails open (and logs) if Redis is unavailable."""

import logging

from fastapi import HTTPException, Request

from app.core import cache

log = logging.getLogger(__name__)


def hit(name: str, ident: str, limit: int, window: int) -> bool:
    """Count one attempt; return True while the caller is still under the limit."""
    key = f"rl:{name}:{ident}"
    try:
        r = cache.client()
        count = r.incr(key)
        if r.ttl(key) < 0:
            r.expire(key, window)
        return count <= limit
    except Exception:
        log.warning("rate limiter unavailable, failing open", exc_info=True)
        return True


def too_many() -> HTTPException:
    return HTTPException(
        429,
        "Trop de tentatives. Réessayez dans une minute.",
        headers={"Retry-After": "60"},
    )


def rate_limit(name: str, limit: int, window: int):
    def dependency(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        if not hit(name, ip, limit, window):
            raise too_many()

    return dependency
