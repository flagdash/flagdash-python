"""FlagDash client-tier SDK for evaluating flags, configs, and AI configs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote
from uuid import uuid4

from flagdash.http_client import AsyncHttpClient, HttpClient
from flagdash.region import merge_region_params, resolve_region
from flagdash.translation import format_translation
from flagdash.types import AiConfigReleaseResult
from flagdash.types import (
    AiConfig,
    ConfigValue,
    EvaluationContext,
    ExperimentAssignment,
    FlagDetailResult,
)


class FlagDashClient:
    """Client-tier SDK using an ``sk_`` API key.

    Provides read-only access to evaluated flag values, config values,
    and active AI config files. Context can be passed for server-side evaluation.

    The key needs the read scopes for the resources you touch (``flags:read``,
    ``configs:read``, ``ai_configs:read``); the project and environment come
    from the key itself. Responses carry evaluated values only — never the
    targeting rules behind them — so this tier is the one to use from
    untrusted clients.

    Usage::

        client = FlagDashClient(sdk_key="sk_...")
        value = client.flag("my-flag", default=False)
        client.close()

    Or as a context manager::

        with FlagDashClient(sdk_key="sk_...") as client:
            value = client.flag("my-flag")
    """

    def __init__(
        self,
        sdk_key: str,
        base_url: str = "https://flagdash.io",
        timeout: float = 5.0,
        region: str | None = None,
        auto_detect_region: bool = True,
    ) -> None:
        if not sdk_key:
            raise ValueError("sdk_key is required")
        self._http = HttpClient(sdk_key=sdk_key, base_url=base_url, timeout=timeout)
        self._region = resolve_region(region, auto_detect_region)
        self._experiment_events: list[dict[str, Any]] = []

    def __enter__(self) -> FlagDashClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP connection."""
        self.flush_experiment_events()
        self._http.close()

    # ── Flags ──────────────────────────────────────────────────────

    def flag(
        self,
        key: str,
        default: Any = None,
        context: EvaluationContext | None = None,
    ) -> Any:
        """Evaluate a single feature flag.

        Args:
            key: The flag key.
            default: Value to return if the flag is not found or on error.
            context: Optional evaluation context for targeting.

        Returns:
            The evaluated flag value, or *default* on error.
        """
        try:
            params = merge_region_params(self._region, context)
            data = self._http.get(f"/flags/{quote(key, safe='')}", params=params)
            return data.get("value", default)
        except Exception:
            return default

    def flag_detail(
        self,
        key: str,
        context: EvaluationContext | None = None,
        default: Any = None,
    ) -> FlagDetailResult:
        """Evaluate a single feature flag and return the full evaluation detail.

        Args:
            key: The flag key.
            context: Optional evaluation context for targeting.
            default: Value to return in the result if the flag is not found or on error.

        Returns:
            A FlagDetailResult with the evaluated value, reason, and optional variation key.
        """
        try:
            params = merge_region_params(self._region, context)
            data = self._http.get(f"/flags/{quote(key, safe='')}", params=params)
            return FlagDetailResult(
                key=data.get("key", key),
                value=data.get("value", default),
                reason=data.get("reason", "default"),
                variation_key=data.get("variation_key"),
            )
        except Exception:
            return FlagDetailResult(
                key=key,
                value=default,
                reason="default",
                variation_key=None,
            )

    def all_flags(
        self,
        context: EvaluationContext | None = None,
    ) -> dict[str, Any]:
        """Get all flag values as a key→value dict.

        Args:
            context: Optional evaluation context for targeting.

        Returns:
            Dict mapping flag keys to their evaluated values.
        """
        params = merge_region_params(self._region, context)
        data = self._http.get("/flags", params=params)
        return data.get("flags", {})

    def experiment(
        self, key: str, context: EvaluationContext
    ) -> ExperimentAssignment | None:
        """Resolve a stable experiment assignment for a required user identity."""
        if not context.user_id:
            return None
        try:
            data = self._http.get(
                f"/experiments/{quote(key, safe='')}",
                params=merge_region_params(self._region, context),
            )["experiment"]
            return ExperimentAssignment(
                key=data["key"],
                status=data["status"],
                variant_key=data["variant_key"],
                parameters=data.get("parameters", {}),
            )
        except Exception:
            return None

    def track_experiment_metric(
        self,
        experiment_key: str,
        event_name: str,
        context: EvaluationContext,
        *,
        value: float | None = None,
        properties: dict[str, Any] | None = None,
        event_id: str | None = None,
        occurred_at: str | None = None,
    ) -> None:
        """Queue an outcome metric without performing network I/O."""
        if not context.user_id or len(self._experiment_events) >= 1000:
            return
        self._experiment_events.append({
            "event_id": event_id or f"evt_{uuid4()}",
            "experiment_key": experiment_key,
            "event_name": event_name,
            "user_id": context.user_id,
            "value": value,
            "properties": properties or {},
            "occurred_at": occurred_at or datetime.now(timezone.utc).isoformat(),
        })

    def flush_experiment_events(self) -> None:
        """Send queued metrics in bounded batches; failed batches remain queued."""
        while self._experiment_events:
            batch = self._experiment_events[:100]
            try:
                self._http.post("/experiment-events/batch", json={"events": batch})
            except Exception:
                return
            del self._experiment_events[:len(batch)]

    # ── Configs ────────────────────────────────────────────────────

    def config(self, key: str, default: Any = None) -> Any:
        """Get a remote config value.

        Args:
            key: The config key.
            default: Value to return if the config is not found.

        Returns:
            The config value, or *default* on error.
        """
        try:
            data = self._http.get(f"/configs/{quote(key, safe='')}")
            return data.get("value", default)
        except Exception:
            return default

    def all_configs(self) -> list[ConfigValue]:
        """Get all config values.

        Returns:
            List of ConfigValue objects.
        """
        data = self._http.get("/configs")
        return [
            ConfigValue(key=c["key"], value=c["value"])
            for c in data.get("configs", [])
        ]

    def translation(
        self,
        key: str,
        *,
        locale: str,
        default: str | None = None,
        variables: dict[str, Any] | None = None,
    ) -> str:
        """Resolve and locally format a published translation."""
        namespace, separator, message_key = key.partition(".")
        if not separator:
            return default or key
        try:
            path = f"/translations/{quote(locale, safe='')}/{quote(namespace, safe='')}"
            data = self._http.get(path)
            catalog = data.get("catalog", {})
            pattern = catalog.get("messages", {}).get(message_key)
            return default or key if pattern is None else format_translation(pattern, variables)
        except Exception:
            return default or key

    # ── AI Configs ─────────────────────────────────────────────────

    def ai_config_release(self, key: str, user_id: str = "anonymous") -> AiConfigReleaseResult | None:
        """Evaluate a release without caching or resolving secret references."""
        try:
            data = self._http.get(
                f"/ai-config-releases/{quote(key, safe='')}", params={"user_id": user_id}
            )
            return AiConfigReleaseResult(**data["ai_config"])
        except Exception:
            return None

    def ai_config(self, file_name: str) -> AiConfig | None:
        """Get a single AI config file by name.

        Args:
            file_name: The file name (e.g. ``"agent.md"``).

        Returns:
            AiConfig or None if not found.
        """
        try:
            data = self._http.get(f"/ai-configs/{quote(file_name, safe='')}")
            ac = data.get("ai_config", {})
            return AiConfig(
                file_name=ac["file_name"],
                file_type=ac["file_type"],
                content=ac["content"],
                folder=ac.get("folder"),
            )
        except Exception:
            return None

    def list_ai_configs(self) -> list[AiConfig]:
        """List all active AI config files.

        Returns:
            List of AiConfig objects.
        """
        data = self._http.get("/ai-configs")
        return [
            AiConfig(
                file_name=ac["file_name"],
                file_type=ac["file_type"],
                content=ac["content"],
                folder=ac.get("folder"),
            )
            for ac in data.get("ai_configs", [])
        ]


class FlagDashAsyncClient:
    """Async client-tier SDK using an ``sk_`` API key.

    Usage::

        async with FlagDashAsyncClient(sdk_key="sk_...") as client:
            value = await client.flag("my-flag")
    """

    def __init__(
        self,
        sdk_key: str,
        base_url: str = "https://flagdash.io",
        timeout: float = 5.0,
        region: str | None = None,
        auto_detect_region: bool = True,
    ) -> None:
        if not sdk_key:
            raise ValueError("sdk_key is required")
        self._http = AsyncHttpClient(sdk_key=sdk_key, base_url=base_url, timeout=timeout)
        self._region = resolve_region(region, auto_detect_region)
        self._experiment_events: list[dict[str, Any]] = []

    async def __aenter__(self) -> FlagDashAsyncClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self.flush_experiment_events()
        await self._http.close()

    async def flag(
        self,
        key: str,
        default: Any = None,
        context: EvaluationContext | None = None,
    ) -> Any:
        try:
            params = merge_region_params(self._region, context)
            data = await self._http.get(f"/flags/{quote(key, safe='')}", params=params)
            return data.get("value", default)
        except Exception:
            return default

    async def flag_detail(
        self,
        key: str,
        context: EvaluationContext | None = None,
        default: Any = None,
    ) -> FlagDetailResult:
        """Evaluate a single feature flag and return the full evaluation detail.

        Args:
            key: The flag key.
            context: Optional evaluation context for targeting.
            default: Value to return in the result if the flag is not found or on error.

        Returns:
            A FlagDetailResult with the evaluated value, reason, and optional variation key.
        """
        try:
            params = merge_region_params(self._region, context)
            data = await self._http.get(f"/flags/{quote(key, safe='')}", params=params)
            return FlagDetailResult(
                key=data.get("key", key),
                value=data.get("value", default),
                reason=data.get("reason", "default"),
                variation_key=data.get("variation_key"),
            )
        except Exception:
            return FlagDetailResult(
                key=key,
                value=default,
                reason="default",
                variation_key=None,
            )

    async def all_flags(
        self,
        context: EvaluationContext | None = None,
    ) -> dict[str, Any]:
        params = merge_region_params(self._region, context)
        data = await self._http.get("/flags", params=params)
        return data.get("flags", {})

    async def experiment(
        self, key: str, context: EvaluationContext
    ) -> ExperimentAssignment | None:
        """Resolve a stable experiment assignment for a required user identity."""
        if not context.user_id:
            return None
        try:
            data = (
                await self._http.get(
                    f"/experiments/{quote(key, safe='')}",
                    params=merge_region_params(self._region, context),
                )
            )["experiment"]
            return ExperimentAssignment(
                key=data["key"],
                status=data["status"],
                variant_key=data["variant_key"],
                parameters=data.get("parameters", {}),
            )
        except Exception:
            return None

    def track_experiment_metric(
        self,
        experiment_key: str,
        event_name: str,
        context: EvaluationContext,
        *,
        value: float | None = None,
        properties: dict[str, Any] | None = None,
        event_id: str | None = None,
        occurred_at: str | None = None,
    ) -> None:
        if not context.user_id or len(self._experiment_events) >= 1000:
            return
        self._experiment_events.append({
            "event_id": event_id or f"evt_{uuid4()}",
            "experiment_key": experiment_key,
            "event_name": event_name,
            "user_id": context.user_id,
            "value": value,
            "properties": properties or {},
            "occurred_at": occurred_at or datetime.now(timezone.utc).isoformat(),
        })

    async def flush_experiment_events(self) -> None:
        while self._experiment_events:
            batch = self._experiment_events[:100]
            try:
                await self._http.post("/experiment-events/batch", json={"events": batch})
            except Exception:
                return
            del self._experiment_events[:len(batch)]

    async def config(self, key: str, default: Any = None) -> Any:
        try:
            data = await self._http.get(f"/configs/{quote(key, safe='')}")
            return data.get("value", default)
        except Exception:
            return default

    async def all_configs(self) -> list[ConfigValue]:
        data = await self._http.get("/configs")
        return [
            ConfigValue(key=c["key"], value=c["value"])
            for c in data.get("configs", [])
        ]

    async def translation(
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
        try:
            path = f"/translations/{quote(locale, safe='')}/{quote(namespace, safe='')}"
            data = await self._http.get(path)
            catalog = data.get("catalog", {})
            pattern = catalog.get("messages", {}).get(message_key)
            return default or key if pattern is None else format_translation(pattern, variables)
        except Exception:
            return default or key

    async def ai_config_release(self, key: str, user_id: str = "anonymous") -> AiConfigReleaseResult | None:
        """Evaluate a release without caching or resolving secret references."""
        try:
            data = await self._http.get(
                f"/ai-config-releases/{quote(key, safe='')}", params={"user_id": user_id}
            )
            return AiConfigReleaseResult(**data["ai_config"])
        except Exception:
            return None

    async def ai_config(self, file_name: str) -> AiConfig | None:
        try:
            data = await self._http.get(f"/ai-configs/{quote(file_name, safe='')}")
            ac = data.get("ai_config", {})
            return AiConfig(
                file_name=ac["file_name"],
                file_type=ac["file_type"],
                content=ac["content"],
                folder=ac.get("folder"),
            )
        except Exception:
            return None

    async def list_ai_configs(self) -> list[AiConfig]:
        data = await self._http.get("/ai-configs")
        return [
            AiConfig(
                file_name=ac["file_name"],
                file_type=ac["file_type"],
                content=ac["content"],
                folder=ac.get("folder"),
            )
            for ac in data.get("ai_configs", [])
        ]
