"""Tests for the TTL cache."""

import time

from flagdash.cache import TTLCache


class TestTTLCache:
    def test_set_and_get(self) -> None:
        cache = TTLCache(default_ttl=10.0)
        cache.set("key", "value")
        assert cache.get("key") == "value"

    def test_get_missing_key(self) -> None:
        cache = TTLCache(default_ttl=10.0)
        assert cache.get("missing") is None

    def test_expiration(self) -> None:
        cache = TTLCache(default_ttl=0.05)
        cache.set("key", "value")
        assert cache.get("key") == "value"
        time.sleep(0.06)
        assert cache.get("key") is None

    def test_custom_ttl(self) -> None:
        cache = TTLCache(default_ttl=10.0)
        cache.set("key", "value", ttl=0.05)
        assert cache.get("key") == "value"
        time.sleep(0.06)
        assert cache.get("key") is None

    def test_clear(self) -> None:
        cache = TTLCache(default_ttl=10.0)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_delete(self) -> None:
        cache = TTLCache(default_ttl=10.0)
        cache.set("key", "value")
        cache.delete("key")
        assert cache.get("key") is None

    def test_disabled_cache(self) -> None:
        cache = TTLCache(default_ttl=0)
        cache.set("key", "value")
        assert cache.get("key") is None

    def test_overwrite(self) -> None:
        cache = TTLCache(default_ttl=10.0)
        cache.set("key", "v1")
        cache.set("key", "v2")
        assert cache.get("key") == "v2"
