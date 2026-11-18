import time
from collections import defaultdict
from typing import Dict, List
from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    """Sliding-window in-memory rate limiter.
    Provides protection against brute-force authentication and denial-of-service
    without requiring external infrastructure dependencies.
    """

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        # Maps client_key -> list of request timestamps
        self.history: Dict[str, List[float]] = defaultdict(list)

    def is_rate_limited(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds

        # Prune timestamps older than window
        timestamps = [ts for ts in self.history[key] if ts > window_start]
        self.history[key] = timestamps

        if len(timestamps) >= self.requests_per_minute:
            return True

        self.history[key].append(now)
        return False

    def reset(self):
        """Clears all tracked request timestamps for test isolation."""
        self.history.clear()


# Standard limiters
auth_limiter = InMemoryRateLimiter(requests_per_minute=20)  # Brute-force guard for login/register
general_limiter = InMemoryRateLimiter(requests_per_minute=120)  # General API guard


async def rate_limit_auth(request: Request):
    """Dependency applying strict rate limits on authentication endpoints."""
    client_ip = request.client.host if request.client else "unknown"
    if auth_limiter.is_rate_limited(f"auth:{client_ip}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please try again in 60 seconds.",
            headers={"Retry-After": "60"},
        )


async def rate_limit_general(request: Request):
    """Dependency applying rate limits on heavy computation endpoints."""
    client_ip = request.client.host if request.client else "unknown"
    if general_limiter.is_rate_limited(f"gen:{client_ip}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please throttle requests.",
            headers={"Retry-After": "60"},
        )
