from __future__ import annotations

import redis
from functools import lru_cache
from app.core.config import settings


@lru_cache(maxsize=1)
def get_redis() -> "redis.Redis[bytes]":
    return redis.Redis.from_url(settings.redis_url)
