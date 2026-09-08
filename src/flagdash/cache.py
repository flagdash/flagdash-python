"""Thread-safe TTL cache for FlagDash SDK."""

from __future__ import annotations

import threading
import time
from typing import Any


class TTLCache:
    """Thread-safe in-memory cache with per-entry TTL expiration.

    Args:
        default_ttl: Default time-to-live in seconds. Set to 0 to disable caching.
    """

    def __init__(self, default_ttl: float = 60.0) -> None:
        self._ttl = default_ttl
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()

    @property
    def ttl(self) -> float:
        return self._ttl

    def get(self, key: str) -> Any | None:
        """Get a cached value, returning None if missing or expired."""
        if self._ttl <= 0:
            return None

        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None

            value, expires_at = entry
            if time.monotonic() >= expires_at:
                del self._store[key]
                return None

            return value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        """Store a value with optional custom TTL."""
        effective_ttl = ttl if ttl is not None else self._ttl
        if effective_ttl <= 0:
            return

        with self._lock:
            self._store[key] = (value, time.monotonic() + effective_ttl)

    def delete(self, key: str) -> None:
        """Remove a key from the cache."""
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        """Remove all entries from the cache."""
        with self._lock:
            self._store.clear()
