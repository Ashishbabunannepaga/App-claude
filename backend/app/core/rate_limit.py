import threading
import time
import uuid
from collections import defaultdict, deque

from app.core.config import get_settings
from app.core.errors import RateLimited


class SlidingWindowLimiter:
    """In-process sliding-window limiter (development / single process)."""

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int, window_seconds: int) -> None:
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and q[0] <= now - window_seconds:
                q.popleft()
            if len(q) >= limit:
                raise RateLimited()
            q.append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


class RedisLimiter:
    """Sliding-window limiter shared by all API replicas (sorted set per key)."""

    def __init__(self, url: str) -> None:
        import redis

        self._redis = redis.Redis.from_url(url)

    def hit(self, key: str, limit: int, window_seconds: int) -> None:
        now = time.time()
        rkey = f"rl:{key}"
        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(rkey, 0, now - window_seconds)
        pipe.zcard(rkey)
        _, count = pipe.execute()
        if count >= limit:
            raise RateLimited()
        pipe = self._redis.pipeline()
        pipe.zadd(rkey, {f"{now}:{uuid.uuid4().hex}": now})
        pipe.expire(rkey, window_seconds)
        pipe.execute()

    def reset(self) -> None:  # tests only
        pass


def _make_limiter() -> SlidingWindowLimiter | RedisLimiter:
    s = get_settings()
    return RedisLimiter(s.redis_url) if s.rate_limit_backend == "redis" else SlidingWindowLimiter()


limiter = _make_limiter()
