"""FlagDash server-tier SDK with TTL caching."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from flagdash.cache import TTLCache
from flagdash.http_client import AsyncHttpClient, HttpClient
from flagdash.region import merge_region_params, resolve_region
from flagdash.translation import format_translation
from flagdash.types import AiConfigReleaseResult
from flagdash.types import (
    Config,
    EvaluationContext,
    Flag,
    FlagSchedule,
    FlagVariation,
    Secret,
    ServerAiConfig,
)

DEFAULT_CACHE_TTL = 60.0


def _parse_flag(data: dict[str, Any]) -> Flag:
    variations = [
        FlagVariation(
            id=v["id"], key=v["key"], name=v["name"], value=v["value"], weight=v["weight"]
        )
        for v in data.get("variations", [])
    ]
    schedules = [
        FlagSchedule(
            id=s["id"],
            action=s["action"],
            scheduled_at=s["scheduled_at"],
            status=s["status"],
            payload=s.get("payload", {}),
        )
        for s in data.get("pending_schedules", [])
    ]
    return Flag(
        key=data["key"],
        name=data["name"],
        description=data.get("description", ""),
        flag_type=data["flag_type"],
        default_value=data.get("default_value"),
        tags=data.get("tags", []),
        enabled=data["enabled"],
        value=data.get("value"),
        rules=data.get("rules"),
        rollout_percentage=data.get("rollout_percentage", 100),
        evaluated_value=data.get("evaluated_value"),
        variation_key=data.get("variation_key"),
        evaluation_path=data.get("evaluation_path"),
        variations=variations,
        pending_schedules=schedules,
    )


def _parse_config(data: dict[str, Any]) -> Config:
    return Config(
        key=data["key"],
        name=data["name"],
        description=data.get("description", ""),
        config_type=data["config_type"],
        default_value=data.get("default_value"),
        tags=data.get("tags", []),
        value=data.get("value"),
        is_active=data.get("is_active", True),
    )


def _parse_secret(data: dict[str, Any]) -> Secret:
    return Secret(
        key=data["key"],
        format=data["format"],
        value=data["value"],
        version_id=data["version_id"],
        created_at=data["created_at"],
        created_by_id=data["created_by_id"],
    )


def _parse_server_ai_config(data: dict[str, Any]) -> ServerAiConfig:
    return ServerAiConfig(
        id=data["id"],
        file_name=data["file_name"],
        file_type=data["file_type"],
        content=data["content"],
        is_active=data["is_active"],
        metadata=data.get("metadata", {}),
        folder=data.get("folder"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )


class FlagDashServerClient:
    """Server-tier SDK using an ``sk_`` API key held server-side.

    Includes TTL caching, full flag/config metadata, and evaluation context support.

    Usage::

        with FlagDashServerClient(sdk_key="sk_...") as client:
            value = client.flag("checkout-v2", default=False)
            flags = client.list_flags()
    """

    def __init__(
        self,
        sdk_key: str,
        base_url: str = "https://flagdash.io",
        timeout: float = 5.0,
        cache_ttl: float = DEFAULT_CACHE_TTL,
        region: str | None = None,
        auto_detect_region: bool = True,
    ) -> None:
        if not sdk_key:
            raise ValueError("sdk_key is required")

        self._http = HttpClient(sdk_key=sdk_key, base_url=base_url, timeout=timeout)
        self._cache = TTLCache(default_ttl=cache_ttl)
        self._region = resolve_region(region, auto_detect_region)

    def __enter__(self) -> FlagDashServerClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    def clear_cache(self) -> None:
        """Clear all cached values."""
        self._cache.clear()

    # ── Flags ──────────────────────────────────────────────────────

    def flag(
        self,
        key: str,
        default: Any = None,
        context: EvaluationContext | None = None,
    ) -> Any:
        """Evaluate a single flag with optional context.

        Context-based evaluations bypass the cache.
        """
        if context:
            try:
                params = merge_region_params(self._region, context)
                data = self._http.get(f"/server/flags/{quote(key, safe='')}", params=params)
                flag_data = data.get("flag", {})
                return flag_data.get("evaluated_value", default)
            except Exception:
                return default

        # Try cache
        cache_key = f"flag:{key}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch all flags and cache
        evaluated = self._fetch_all_flag_values()
        return evaluated.get(key, default)

    def all_flags(
        self,
        context: EvaluationContext | None = None,
    ) -> dict[str, Any]:
        """Get all evaluated flag values."""
        if context:
            params = merge_region_params(self._region, context)
            data = self._http.get("/server/flags", params=params)
            return data.get("evaluated", {})

        cached = self._cache.get("all_flags")
        if cached is not None:
            return dict(cached)

        return self._fetch_all_flag_values()

    def get_flag(self, key: str) -> Flag | None:
        """Get a flag with full metadata."""
        cache_key = f"flag_detail:{key}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            data = self._http.get(f"/server/flags/{quote(key, safe='')}")
            flag = _parse_flag(data["flag"])
            self._cache.set(cache_key, flag)
            return flag
        except Exception:
            return None

    def list_flags(self) -> list[Flag]:
        """List all flags with full metadata."""
        data = self._http.get("/server/flags")
        return [_parse_flag(f) for f in data.get("flags", [])]

    # ── Configs ────────────────────────────────────────────────────

    def config(self, key: str, default: Any = None) -> Any:
        """Get a config value by key."""
        cache_key = f"config:{key}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            data = self._http.get(f"/server/configs/{quote(key, safe='')}")
            config_data = data.get("config", {})
            value = config_data.get("value", default)
            self._cache.set(cache_key, value)
            return value
        except Exception:
            return default

    def get_config(self, key: str) -> Config | None:
        """Get a config with full metadata."""
        try:
            data = self._http.get(f"/server/configs/{quote(key, safe='')}")
            return _parse_config(data["config"])
        except Exception:
            return None

    def list_configs(self) -> list[Config]:
        """List all configs with full metadata."""
        data = self._http.get("/server/configs")
        return [_parse_config(c) for c in data.get("configs", [])]

    def resolve_config(self, key: str) -> dict[str, Any]:
        """Explicit backend fetch requiring configs:read and secrets:read.

        Never cached and never defaulted.
        """
        data = self._http.post(f"/server/configs/{quote(key, safe='')}/resolve", json={})
        return data["config"]

    def ai_config_release(self, key: str, user_id: str = "anonymous") -> AiConfigReleaseResult | None:
        """Evaluate a release without caching or resolving secret references."""
        try:
            data = self._http.get(
                f"/ai-config-releases/{quote(key, safe='')}", params={"user_id": user_id}
            )
            return AiConfigReleaseResult(**data["ai_config"])
        except Exception:
            return None

    def resolve_ai_release(self, key: str, user_id: str = "anonymous") -> dict[str, Any]:
        """Evaluate a release and resolve its credentials. Never cached/defaulted."""
        data = self._http.post(
            f"/server/ai-config-releases/{quote(key, safe='')}/resolve",
            json={"user_id": user_id},
        )
        return data["ai_config"]

    def get_secret(self, key: str) -> Secret:
        """Fetch a decrypted secret by key.

        Deliberately unlike :meth:`config`: the value is never cached, no default
        is substituted, and a failure raises. Returning a stale or default
        credential is worse than failing loudly — a rotated key must take effect
        on the next call, and a silent fallback would send the wrong credential
        to a payment provider or a database.

        Requires an ``sk_`` key carrying the ``secrets:read`` scope. There is no
        browser or mobile equivalent: call your own backend instead.
        """
        data = self._http.get(f"/server/secrets/{quote(key, safe='')}")
        return _parse_secret(data["secret"])

    def secret(self, key: str) -> Any:
        """Return just the decrypted value. Raises for the same reasons as
        :meth:`get_secret`."""
        return self.get_secret(key).value

    def translation(
        self,
        key: str,
        *,
        locale: str,
        default: str | None = None,
        variables: dict[str, Any] | None = None,
    ) -> str:
        namespace, separator, message_key = key.partition(".")
        if not separator:
            return default or key
        cache_key = f"translation:{locale}:{namespace}"
        catalog = self._cache.get(cache_key)
        try:
            if catalog is None:
                path = (
                    f"/server/translations/{quote(locale, safe='')}"
                    f"/{quote(namespace, safe='')}"
                )
                catalog = self._http.get(path).get("catalog", {})
                self._cache.set(cache_key, catalog)
            pattern = catalog.get("messages", {}).get(message_key)
            return default or key if pattern is None else format_translation(pattern, variables)
        except Exception:
            return default or key

    # ── AI Configs ─────────────────────────────────────────────────

    def ai_config(self, file_name: str) -> ServerAiConfig | None:
        """Get an AI config file with full metadata."""
        cache_key = f"ai_config:{file_name}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            data = self._http.get(f"/server/ai-configs/{quote(file_name, safe='')}")
            result = _parse_server_ai_config(data["ai_config"])
            self._cache.set(cache_key, result)
            return result
        except Exception:
            return None

    def list_ai_configs(self) -> list[ServerAiConfig]:
        """List all AI config files with full metadata."""
        data = self._http.get("/server/ai-configs")
        return [_parse_server_ai_config(ac) for ac in data.get("ai_configs", [])]

    # ── Internal ───────────────────────────────────────────────────

    def _fetch_all_flag_values(self) -> dict[str, Any]:
        data = self._http.get("/server/flags", params=merge_region_params(self._region, None))
        evaluated = data.get("evaluated", {})
        self._cache.set("all_flags", evaluated)
        for key, value in evaluated.items():
            self._cache.set(f"flag:{key}", value)
        return evaluated


class FlagDashAsyncServerClient:
    """Async server-tier SDK using an ``sk_`` API key held server-side.

    Usage::

        async with FlagDashAsyncServerClient(sdk_key="sk_...") as client:
            value = await client.flag("checkout-v2", default=False)
    """

    def __init__(
        self,
        sdk_key: str,
        base_url: str = "https://flagdash.io",
        timeout: float = 5.0,
        cache_ttl: float = DEFAULT_CACHE_TTL,
        region: str | None = None,
        auto_detect_region: bool = True,
    ) -> None:
        if not sdk_key:
            raise ValueError("sdk_key is required")

        self._http = AsyncHttpClient(sdk_key=sdk_key, base_url=base_url, timeout=timeout)
        self._cache = TTLCache(default_ttl=cache_ttl)
        self._region = resolve_region(region, auto_detect_region)

    async def __aenter__(self) -> FlagDashAsyncServerClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self._http.close()

    def clear_cache(self) -> None:
        self._cache.clear()

    async def flag(
        self,
        key: str,
        default: Any = None,
        context: EvaluationContext | None = None,
    ) -> Any:
        if context:
            try:
                params = merge_region_params(self._region, context)
                data = await self._http.get(f"/server/flags/{quote(key, safe='')}", params=params)
                flag_data = data.get("flag", {})
                return flag_data.get("evaluated_value", default)
            except Exception:
                return default

        cache_key = f"flag:{key}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        evaluated = await self._fetch_all_flag_values()
        return evaluated.get(key, default)

    async def all_flags(
        self,
        context: EvaluationContext | None = None,
    ) -> dict[str, Any]:
        if context:
            params = merge_region_params(self._region, context)
            data = await self._http.get("/server/flags", params=params)
            return data.get("evaluated", {})

        cached = self._cache.get("all_flags")
        if cached is not None:
            return dict(cached)

        return await self._fetch_all_flag_values()

    async def get_flag(self, key: str) -> Flag | None:
        cache_key = f"flag_detail:{key}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            data = await self._http.get(f"/server/flags/{quote(key, safe='')}")
            flag = _parse_flag(data["flag"])
            self._cache.set(cache_key, flag)
            return flag
        except Exception:
            return None

    async def list_flags(self) -> list[Flag]:
        data = await self._http.get("/server/flags")
        return [_parse_flag(f) for f in data.get("flags", [])]

    async def config(self, key: str, default: Any = None) -> Any:
        cache_key = f"config:{key}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            data = await self._http.get(f"/server/configs/{quote(key, safe='')}")
            config_data = data.get("config", {})
            value = config_data.get("value", default)
            self._cache.set(cache_key, value)
            return value
        except Exception:
            return default

    async def get_config(self, key: str) -> Config | None:
        try:
            data = await self._http.get(f"/server/configs/{quote(key, safe='')}")
            return _parse_config(data["config"])
        except Exception:
            return None

    async def list_configs(self) -> list[Config]:
        data = await self._http.get("/server/configs")
        return [_parse_config(c) for c in data.get("configs", [])]

    async def resolve_config(self, key: str) -> dict[str, Any]:
        """Explicit backend fetch requiring configs:read and secrets:read.

        Never cached and never defaulted.
        """
        data = await self._http.post(f"/server/configs/{quote(key, safe='')}/resolve", json={})
        return data["config"]

    async def ai_config_release(self, key: str, user_id: str = "anonymous") -> AiConfigReleaseResult | None:
        """Evaluate a release without caching or resolving secret references."""
        try:
            data = await self._http.get(
                f"/ai-config-releases/{quote(key, safe='')}", params={"user_id": user_id}
            )
            return AiConfigReleaseResult(**data["ai_config"])
        except Exception:
            return None

    async def resolve_ai_release(self, key: str, user_id: str = "anonymous") -> dict[str, Any]:
        """Evaluate a release and resolve its credentials. Never cached/defaulted."""
        data = await self._http.post(
            f"/server/ai-config-releases/{quote(key, safe='')}/resolve",
            json={"user_id": user_id},
        )
        return data["ai_config"]

    async def get_secret(self, key: str) -> Secret:
        """Fetch a decrypted secret by key. Never cached, never defaulted."""
        data = await self._http.get(f"/server/secrets/{quote(key, safe='')}")
        return _parse_secret(data["secret"])

    async def secret(self, key: str) -> Any:
        """Return just the decrypted value."""
        return (await self.get_secret(key)).value

    async def ai_config(self, file_name: str) -> ServerAiConfig | None:
        cache_key = f"ai_config:{file_name}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            data = await self._http.get(f"/server/ai-configs/{quote(file_name, safe='')}")
            result = _parse_server_ai_config(data["ai_config"])
            self._cache.set(cache_key, result)
            return result
        except Exception:
            return None

    async def list_ai_configs(self) -> list[ServerAiConfig]:
        data = await self._http.get("/server/ai-configs")
        return [_parse_server_ai_config(ac) for ac in data.get("ai_configs", [])]

    async def _fetch_all_flag_values(self) -> dict[str, Any]:
        data = await self._http.get(
            "/server/flags", params=merge_region_params(self._region, None)
        )
        evaluated = data.get("evaluated", {})
        self._cache.set("all_flags", evaluated)
        for key, value in evaluated.items():
            self._cache.set(f"flag:{key}", value)
        return evaluated
