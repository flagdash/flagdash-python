"""FlagDash management-tier SDK for full CRUD on flags, configs, AI configs, and webhooks."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from flagdash.http_client import AsyncHttpClient, HttpClient
from flagdash.types import (
    ConfigEnvironment,
    FlagEnvironment,
    FlagScheduleDetail,
    FlagVariation,
    ManagedAiConfig,
    ManagedConfig,
    ManagedFlag,
    WebhookDelivery,
    WebhookEndpoint,
)

BASE = "/manage"


def _parse_managed_flag(data: dict[str, Any]) -> ManagedFlag:
    envs = [
        FlagEnvironment(
            id=e["id"],
            environment_id=e["environment_id"],
            enabled=e["enabled"],
            value=e.get("value"),
            rules=e.get("rules"),
            rollout_percentage=e.get("rollout_percentage", 100),
        )
        for e in data.get("environments", [])
    ]
    return ManagedFlag(
        id=data["id"],
        key=data["key"],
        name=data["name"],
        description=data.get("description", ""),
        flag_type=data["flag_type"],
        default_value=data.get("default_value"),
        tags=data.get("tags", []),
        is_archived=data.get("is_archived", False),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
        environments=envs,
    )


def _parse_managed_config(data: dict[str, Any]) -> ManagedConfig:
    envs = [
        ConfigEnvironment(
            id=e["id"],
            environment_id=e["environment_id"],
            value=e.get("value"),
            is_active=e.get("is_active", True),
        )
        for e in data.get("environments", [])
    ]
    return ManagedConfig(
        id=data["id"],
        key=data["key"],
        name=data["name"],
        description=data.get("description", ""),
        config_type=data["config_type"],
        default_value=data.get("default_value"),
        tags=data.get("tags", []),
        is_archived=data.get("is_archived", False),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
        environments=envs,
    )


def _parse_managed_ai_config(data: dict[str, Any]) -> ManagedAiConfig:
    return ManagedAiConfig(
        id=data["id"],
        file_name=data["file_name"],
        file_type=data["file_type"],
        content=data["content"],
        is_active=data["is_active"],
        metadata=data.get("metadata", {}),
        folder=data.get("folder"),
        project_id=data.get("project_id", ""),
        environment_id=data.get("environment_id", ""),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
    )


def _parse_webhook(data: dict[str, Any]) -> WebhookEndpoint:
    return WebhookEndpoint(
        id=data["id"],
        url=data["url"],
        description=data.get("description"),
        environment_id=data["environment_id"],
        event_types=data.get("event_types", []),
        is_active=data.get("is_active", True),
        consecutive_failures=data.get("consecutive_failures", 0),
        disabled_at=data.get("disabled_at"),
        disabled_reason=data.get("disabled_reason"),
        signing_secret=data.get("signing_secret"),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
    )


def _parse_delivery(data: dict[str, Any]) -> WebhookDelivery:
    return WebhookDelivery(
        id=data["id"],
        event_type=data["event_type"],
        status=data["status"],
        http_status=data.get("http_status"),
        error_message=data.get("error_message"),
        attempt_count=data.get("attempt_count", 0),
        max_attempts=data.get("max_attempts", 0),
        completed_at=data.get("completed_at"),
        created_at=data.get("created_at", ""),
    )


class FlagDashManagementClient:
    """Management-tier SDK using an ``sk_`` key with ``:write`` scopes, or a ``pat_`` token.

    Provides full CRUD for flags, configs, AI configs, and webhooks.

    Usage::

        with FlagDashManagementClient(sdk_key="sk_...") as mgmt:
            flag = mgmt.create_flag(
                project_id="prj_xxx",
                key="new-checkout",
                name="New Checkout",
                flag_type="boolean",
            )
    """

    def __init__(
        self,
        sdk_key: str,
        base_url: str = "https://flagdash.io",
        timeout: float = 10.0,
    ) -> None:
        if not sdk_key:
            raise ValueError("sdk_key is required")
        self._http = HttpClient(sdk_key=sdk_key, base_url=base_url, timeout=timeout)

    def __enter__(self) -> FlagDashManagementClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    # ── Flags ──────────────────────────────────────────────────────

    def list_flags(self, project_id: str) -> list[ManagedFlag]:
        """List all flags for a project."""
        data = self._http.get(f"{BASE}/flags", params={"project_id": project_id})
        return [_parse_managed_flag(f) for f in data.get("flags", [])]

    def get_flag(self, key: str, project_id: str) -> ManagedFlag:
        """Get a single flag by key."""
        data = self._http.get(
            f"{BASE}/flags/{quote(key, safe='')}",
            params={"project_id": project_id},
        )
        return _parse_managed_flag(data["flag"])

    def create_flag(
        self,
        project_id: str,
        key: str,
        name: str,
        flag_type: str = "boolean",
        description: str = "",
        tags: list[str] | None = None,
    ) -> ManagedFlag:
        """Create a new feature flag."""
        body: dict[str, Any] = {
            "project_id": project_id,
            "key": key,
            "name": name,
            "flag_type": flag_type,
            "description": description,
        }
        if tags:
            body["tags"] = tags
        data = self._http.post(f"{BASE}/flags", json=body)
        return _parse_managed_flag(data["flag"])

    def update_flag(
        self,
        key: str,
        project_id: str,
        **kwargs: Any,
    ) -> ManagedFlag:
        """Update a feature flag. Pass fields to update as keyword arguments."""
        body: dict[str, Any] = {"project_id": project_id, **kwargs}
        data = self._http.put(f"{BASE}/flags/{quote(key, safe='')}", json=body)
        return _parse_managed_flag(data["flag"])

    def delete_flag(self, key: str, project_id: str) -> None:
        """Delete a feature flag."""
        self._http.delete(
            f"{BASE}/flags/{quote(key, safe='')}",
            params={"project_id": project_id},
        )

    def toggle_flag(
        self,
        key: str,
        project_id: str,
        environment_id: str,
    ) -> dict[str, Any]:
        """Toggle a flag in a specific environment."""
        data = self._http.post(
            f"{BASE}/flags/{quote(key, safe='')}/toggle",
            json={
                "project_id": project_id,
                "environment_id": environment_id,
            },
        )
        return data.get("flag_environment", {})

    def set_rollout(
        self,
        key: str,
        project_id: str,
        environment_id: str,
        rollout_percentage: int,
    ) -> dict[str, Any]:
        """Set the rollout percentage for a flag in an environment."""
        data = self._http.put(
            f"{BASE}/flags/{quote(key, safe='')}/rollout",
            json={
                "project_id": project_id,
                "environment_id": environment_id,
                "rollout_percentage": rollout_percentage,
            },
        )
        return data.get("flag_environment", {})

    def update_rules(
        self,
        key: str,
        project_id: str,
        environment_id: str,
        rules: dict[str, Any],
    ) -> dict[str, Any]:
        """Update targeting rules for a flag in an environment."""
        data = self._http.put(
            f"{BASE}/flags/{quote(key, safe='')}/rules",
            json={
                "project_id": project_id,
                "environment_id": environment_id,
                "rules": rules,
            },
        )
        return data.get("flag_environment", {})

    def set_variations(
        self,
        key: str,
        project_id: str,
        environment_id: str,
        variations: list[dict[str, Any]],
    ) -> list[FlagVariation]:
        """Set A/B test variations for a flag. Weights must sum to 100."""
        data = self._http.put(
            f"{BASE}/flags/{quote(key, safe='')}/variations",
            json={
                "project_id": project_id,
                "environment_id": environment_id,
                "variations": variations,
            },
        )
        return [
            FlagVariation(
                id=v["id"], key=v["key"], name=v["name"], value=v["value"], weight=v["weight"]
            )
            for v in data.get("variations", [])
        ]

    def delete_variations(
        self,
        key: str,
        project_id: str,
        environment_id: str,
    ) -> None:
        """Remove all variations from a flag (revert to simple mode)."""
        self._http.delete(
            f"{BASE}/flags/{quote(key, safe='')}/variations",
            params={"project_id": project_id, "environment_id": environment_id},
        )

    # ── Schedules ──────────────────────────────────────────────────

    def list_schedules(
        self,
        key: str,
        project_id: str,
        environment_id: str,
    ) -> list[FlagScheduleDetail]:
        """List schedules for a flag in an environment."""
        data = self._http.get(
            f"{BASE}/flags/{quote(key, safe='')}/schedules",
            params={"project_id": project_id, "environment_id": environment_id},
        )
        return [
            FlagScheduleDetail(
                id=s["id"],
                action=s["action"],
                scheduled_at=s["scheduled_at"],
                status=s["status"],
                payload=s.get("payload", {}),
                executed_at=s.get("executed_at"),
                error_message=s.get("error_message"),
                created_at=s.get("created_at"),
            )
            for s in data.get("schedules", [])
        ]

    def create_schedule(
        self,
        key: str,
        project_id: str,
        environment_id: str,
        action: str,
        scheduled_at: str,
        payload: dict[str, Any] | None = None,
    ) -> FlagScheduleDetail:
        """Create a scheduled action for a flag."""
        body: dict[str, Any] = {
            "project_id": project_id,
            "environment_id": environment_id,
            "action": action,
            "scheduled_at": scheduled_at,
        }
        if payload:
            body["payload"] = payload
        data = self._http.post(
            f"{BASE}/flags/{quote(key, safe='')}/schedules",
            json=body,
        )
        s = data["schedule"]
        return FlagScheduleDetail(
            id=s["id"],
            action=s["action"],
            scheduled_at=s["scheduled_at"],
            status=s["status"],
            payload=s.get("payload", {}),
            created_at=s.get("created_at"),
        )

    def cancel_schedule(
        self,
        key: str,
        project_id: str,
        schedule_id: str,
    ) -> FlagScheduleDetail:
        """Cancel a pending schedule."""
        data = self._http.delete(
            f"{BASE}/flags/{quote(key, safe='')}/schedules/{schedule_id}",
            params={"project_id": project_id},
        )
        s = data["schedule"]
        return FlagScheduleDetail(
            id=s["id"],
            action=s["action"],
            scheduled_at=s["scheduled_at"],
            status=s["status"],
            payload=s.get("payload", {}),
            created_at=s.get("created_at"),
        )

    # ── Configs ────────────────────────────────────────────────────

    def list_configs(self, project_id: str) -> list[ManagedConfig]:
        """List all configs for a project."""
        data = self._http.get(f"{BASE}/configs", params={"project_id": project_id})
        return [_parse_managed_config(c) for c in data.get("configs", [])]

    def get_config(self, key: str, project_id: str) -> ManagedConfig:
        """Get a single config by key."""
        data = self._http.get(
            f"{BASE}/configs/{quote(key, safe='')}",
            params={"project_id": project_id},
        )
        return _parse_managed_config(data["config"])

    def create_config(
        self,
        project_id: str,
        key: str,
        name: str,
        config_type: str = "string",
        description: str = "",
        default_value: Any = None,
        tags: list[str] | None = None,
    ) -> ManagedConfig:
        """Create a new remote config."""
        body: dict[str, Any] = {
            "project_id": project_id,
            "key": key,
            "name": name,
            "config_type": config_type,
            "description": description,
        }
        if default_value is not None:
            body["default_value"] = default_value
        if tags:
            body["tags"] = tags
        data = self._http.post(f"{BASE}/configs", json=body)
        return _parse_managed_config(data["config"])

    def update_config(
        self,
        key: str,
        project_id: str,
        **kwargs: Any,
    ) -> ManagedConfig:
        """Update a remote config. Pass fields to update as keyword arguments."""
        body: dict[str, Any] = {"project_id": project_id, **kwargs}
        data = self._http.put(f"{BASE}/configs/{quote(key, safe='')}", json=body)
        return _parse_managed_config(data["config"])

    def delete_config(self, key: str, project_id: str) -> None:
        """Delete a remote config."""
        self._http.delete(
            f"{BASE}/configs/{quote(key, safe='')}",
            params={"project_id": project_id},
        )

    def update_config_value(
        self,
        key: str,
        project_id: str,
        environment_id: str,
        value: Any,
    ) -> dict[str, Any]:
        """Update a config's value for a specific environment."""
        data = self._http.put(
            f"{BASE}/configs/{quote(key, safe='')}/value",
            json={
                "project_id": project_id,
                "environment_id": environment_id,
                "value": value,
            },
        )
        return data.get("config_environment", {})

    # ── AI Configs ─────────────────────────────────────────────────

    def list_ai_configs(
        self,
        project_id: str,
        environment_id: str | None = None,
    ) -> list[ManagedAiConfig]:
        """List AI config files for a project (optionally filtered by environment)."""
        params: dict[str, str] = {"project_id": project_id}
        if environment_id:
            params["environment_id"] = environment_id
        data = self._http.get(f"{BASE}/ai-configs", params=params)
        return [_parse_managed_ai_config(ac) for ac in data.get("ai_configs", [])]

    def get_ai_config(
        self,
        file_name: str,
        project_id: str,
        environment_id: str,
    ) -> ManagedAiConfig:
        """Get a single AI config file by name."""
        data = self._http.get(
            f"{BASE}/ai-configs/{quote(file_name, safe='')}",
            params={"project_id": project_id, "environment_id": environment_id},
        )
        return _parse_managed_ai_config(data["ai_config"])

    def create_ai_config(
        self,
        project_id: str,
        environment_id: str,
        file_name: str,
        file_type: str,
        content: str,
        folder: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ManagedAiConfig:
        """Create a new AI config file."""
        body: dict[str, Any] = {
            "project_id": project_id,
            "environment_id": environment_id,
            "file_name": file_name,
            "file_type": file_type,
            "content": content,
        }
        if folder:
            body["folder"] = folder
        if metadata:
            body["metadata"] = metadata
        data = self._http.post(f"{BASE}/ai-configs", json=body)
        return _parse_managed_ai_config(data["ai_config"])

    def update_ai_config(
        self,
        file_name: str,
        project_id: str,
        environment_id: str,
        **kwargs: Any,
    ) -> ManagedAiConfig:
        """Update an AI config file. Pass fields to update as keyword arguments."""
        body: dict[str, Any] = {
            "project_id": project_id,
            "environment_id": environment_id,
            **kwargs,
        }
        data = self._http.put(
            f"{BASE}/ai-configs/{quote(file_name, safe='')}",
            json=body,
        )
        return _parse_managed_ai_config(data["ai_config"])

    def delete_ai_config(
        self,
        file_name: str,
        project_id: str,
        environment_id: str,
    ) -> None:
        """Delete an AI config file."""
        self._http.delete(
            f"{BASE}/ai-configs/{quote(file_name, safe='')}",
            params={"project_id": project_id, "environment_id": environment_id},
        )

    def initialize_ai_configs(
        self,
        project_id: str,
        environment_id: str,
    ) -> list[ManagedAiConfig]:
        """Initialize default AI config files for an environment."""
        data = self._http.post(
            f"{BASE}/ai-configs/initialize",
            json={"project_id": project_id, "environment_id": environment_id},
        )
        return [_parse_managed_ai_config(ac) for ac in data.get("ai_configs", [])]

    # ── Webhooks ───────────────────────────────────────────────────

    def list_webhooks(self, project_id: str) -> list[WebhookEndpoint]:
        """List all webhook endpoints for a project."""
        data = self._http.get(f"{BASE}/webhooks", params={"project_id": project_id})
        return [_parse_webhook(w) for w in data.get("endpoints", [])]

    def get_webhook(self, webhook_id: str) -> WebhookEndpoint:
        """Get a single webhook endpoint."""
        data = self._http.get(f"{BASE}/webhooks/{webhook_id}")
        return _parse_webhook(data["endpoint"])

    def create_webhook(
        self,
        project_id: str,
        environment_id: str,
        url: str,
        event_types: list[str],
        description: str | None = None,
    ) -> WebhookEndpoint:
        """Create a new webhook endpoint. The signing secret is returned only on creation."""
        body: dict[str, Any] = {
            "project_id": project_id,
            "environment_id": environment_id,
            "url": url,
            "event_types": event_types,
        }
        if description:
            body["description"] = description
        data = self._http.post(f"{BASE}/webhooks", json=body)
        return _parse_webhook(data["endpoint"])

    def update_webhook(
        self,
        webhook_id: str,
        **kwargs: Any,
    ) -> WebhookEndpoint:
        """Update a webhook endpoint."""
        data = self._http.put(f"{BASE}/webhooks/{webhook_id}", json=kwargs)
        return _parse_webhook(data["endpoint"])

    def delete_webhook(self, webhook_id: str) -> None:
        """Delete a webhook endpoint."""
        self._http.delete(f"{BASE}/webhooks/{webhook_id}")

    def regenerate_webhook_secret(self, webhook_id: str) -> WebhookEndpoint:
        """Regenerate the signing secret for a webhook endpoint."""
        data = self._http.post(f"{BASE}/webhooks/{webhook_id}/regenerate-secret")
        return _parse_webhook(data["endpoint"])

    def reactivate_webhook(self, webhook_id: str) -> WebhookEndpoint:
        """Reactivate a disabled webhook endpoint."""
        data = self._http.post(f"{BASE}/webhooks/{webhook_id}/reactivate")
        return _parse_webhook(data["endpoint"])

    def list_webhook_deliveries(
        self,
        webhook_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[WebhookDelivery]:
        """List delivery logs for a webhook endpoint."""
        data = self._http.get(
            f"{BASE}/webhooks/{webhook_id}/deliveries",
            params={"limit": str(limit), "offset": str(offset)},
        )
        return [_parse_delivery(d) for d in data.get("deliveries", [])]


class FlagDashAsyncManagementClient:
    """Async management-tier SDK using an ``sk_`` key with ``:write`` scopes, or a ``pat_`` token.

    Usage::

        async with FlagDashAsyncManagementClient(sdk_key="sk_...") as mgmt:
            flag = await mgmt.create_flag(project_id="prj_xxx", ...)
    """

    def __init__(
        self,
        sdk_key: str,
        base_url: str = "https://flagdash.io",
        timeout: float = 10.0,
    ) -> None:
        if not sdk_key:
            raise ValueError("sdk_key is required")
        self._http = AsyncHttpClient(sdk_key=sdk_key, base_url=base_url, timeout=timeout)

    async def __aenter__(self) -> FlagDashAsyncManagementClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self._http.close()

    # ── Flags ──────────────────────────────────────────────────────

    async def list_flags(self, project_id: str) -> list[ManagedFlag]:
        data = await self._http.get(f"{BASE}/flags", params={"project_id": project_id})
        return [_parse_managed_flag(f) for f in data.get("flags", [])]

    async def get_flag(self, key: str, project_id: str) -> ManagedFlag:
        data = await self._http.get(
            f"{BASE}/flags/{quote(key, safe='')}",
            params={"project_id": project_id},
        )
        return _parse_managed_flag(data["flag"])

    async def create_flag(
        self,
        project_id: str,
        key: str,
        name: str,
        flag_type: str = "boolean",
        description: str = "",
        tags: list[str] | None = None,
    ) -> ManagedFlag:
        body: dict[str, Any] = {
            "project_id": project_id,
            "key": key,
            "name": name,
            "flag_type": flag_type,
            "description": description,
        }
        if tags:
            body["tags"] = tags
        data = await self._http.post(f"{BASE}/flags", json=body)
        return _parse_managed_flag(data["flag"])

    async def update_flag(self, key: str, project_id: str, **kwargs: Any) -> ManagedFlag:
        body: dict[str, Any] = {"project_id": project_id, **kwargs}
        data = await self._http.put(f"{BASE}/flags/{quote(key, safe='')}", json=body)
        return _parse_managed_flag(data["flag"])

    async def delete_flag(self, key: str, project_id: str) -> None:
        await self._http.delete(
            f"{BASE}/flags/{quote(key, safe='')}",
            params={"project_id": project_id},
        )

    async def toggle_flag(self, key: str, project_id: str, environment_id: str) -> dict[str, Any]:
        data = await self._http.post(
            f"{BASE}/flags/{quote(key, safe='')}/toggle",
            json={"project_id": project_id, "environment_id": environment_id},
        )
        return data.get("flag_environment", {})

    async def set_rollout(
        self, key: str, project_id: str, environment_id: str, rollout_percentage: int
    ) -> dict[str, Any]:
        data = await self._http.put(
            f"{BASE}/flags/{quote(key, safe='')}/rollout",
            json={
                "project_id": project_id,
                "environment_id": environment_id,
                "rollout_percentage": rollout_percentage,
            },
        )
        return data.get("flag_environment", {})

    async def update_rules(
        self, key: str, project_id: str, environment_id: str, rules: dict[str, Any]
    ) -> dict[str, Any]:
        data = await self._http.put(
            f"{BASE}/flags/{quote(key, safe='')}/rules",
            json={
                "project_id": project_id,
                "environment_id": environment_id,
                "rules": rules,
            },
        )
        return data.get("flag_environment", {})

    async def set_variations(
        self,
        key: str,
        project_id: str,
        environment_id: str,
        variations: list[dict[str, Any]],
    ) -> list[FlagVariation]:
        data = await self._http.put(
            f"{BASE}/flags/{quote(key, safe='')}/variations",
            json={
                "project_id": project_id,
                "environment_id": environment_id,
                "variations": variations,
            },
        )
        return [
            FlagVariation(
                id=v["id"], key=v["key"], name=v["name"], value=v["value"], weight=v["weight"]
            )
            for v in data.get("variations", [])
        ]

    async def delete_variations(
        self, key: str, project_id: str, environment_id: str
    ) -> None:
        await self._http.delete(
            f"{BASE}/flags/{quote(key, safe='')}/variations",
            params={"project_id": project_id, "environment_id": environment_id},
        )

    # ── Schedules ──────────────────────────────────────────────────

    async def list_schedules(
        self, key: str, project_id: str, environment_id: str
    ) -> list[FlagScheduleDetail]:
        data = await self._http.get(
            f"{BASE}/flags/{quote(key, safe='')}/schedules",
            params={"project_id": project_id, "environment_id": environment_id},
        )
        return [
            FlagScheduleDetail(
                id=s["id"],
                action=s["action"],
                scheduled_at=s["scheduled_at"],
                status=s["status"],
                payload=s.get("payload", {}),
                executed_at=s.get("executed_at"),
                error_message=s.get("error_message"),
                created_at=s.get("created_at"),
            )
            for s in data.get("schedules", [])
        ]

    async def create_schedule(
        self,
        key: str,
        project_id: str,
        environment_id: str,
        action: str,
        scheduled_at: str,
        payload: dict[str, Any] | None = None,
    ) -> FlagScheduleDetail:
        body: dict[str, Any] = {
            "project_id": project_id,
            "environment_id": environment_id,
            "action": action,
            "scheduled_at": scheduled_at,
        }
        if payload:
            body["payload"] = payload
        data = await self._http.post(
            f"{BASE}/flags/{quote(key, safe='')}/schedules", json=body
        )
        s = data["schedule"]
        return FlagScheduleDetail(
            id=s["id"],
            action=s["action"],
            scheduled_at=s["scheduled_at"],
            status=s["status"],
            payload=s.get("payload", {}),
            created_at=s.get("created_at"),
        )

    async def cancel_schedule(
        self, key: str, project_id: str, schedule_id: str
    ) -> FlagScheduleDetail:
        data = await self._http.delete(
            f"{BASE}/flags/{quote(key, safe='')}/schedules/{schedule_id}",
            params={"project_id": project_id},
        )
        s = data["schedule"]
        return FlagScheduleDetail(
            id=s["id"],
            action=s["action"],
            scheduled_at=s["scheduled_at"],
            status=s["status"],
            payload=s.get("payload", {}),
            created_at=s.get("created_at"),
        )

    # ── Configs ────────────────────────────────────────────────────

    async def list_configs(self, project_id: str) -> list[ManagedConfig]:
        data = await self._http.get(f"{BASE}/configs", params={"project_id": project_id})
        return [_parse_managed_config(c) for c in data.get("configs", [])]

    async def get_config(self, key: str, project_id: str) -> ManagedConfig:
        data = await self._http.get(
            f"{BASE}/configs/{quote(key, safe='')}",
            params={"project_id": project_id},
        )
        return _parse_managed_config(data["config"])

    async def create_config(
        self,
        project_id: str,
        key: str,
        name: str,
        config_type: str = "string",
        description: str = "",
        default_value: Any = None,
        tags: list[str] | None = None,
    ) -> ManagedConfig:
        body: dict[str, Any] = {
            "project_id": project_id,
            "key": key,
            "name": name,
            "config_type": config_type,
            "description": description,
        }
        if default_value is not None:
            body["default_value"] = default_value
        if tags:
            body["tags"] = tags
        data = await self._http.post(f"{BASE}/configs", json=body)
        return _parse_managed_config(data["config"])

    async def update_config(self, key: str, project_id: str, **kwargs: Any) -> ManagedConfig:
        body: dict[str, Any] = {"project_id": project_id, **kwargs}
        data = await self._http.put(f"{BASE}/configs/{quote(key, safe='')}", json=body)
        return _parse_managed_config(data["config"])

    async def delete_config(self, key: str, project_id: str) -> None:
        await self._http.delete(
            f"{BASE}/configs/{quote(key, safe='')}",
            params={"project_id": project_id},
        )

    async def update_config_value(
        self, key: str, project_id: str, environment_id: str, value: Any
    ) -> dict[str, Any]:
        data = await self._http.put(
            f"{BASE}/configs/{quote(key, safe='')}/value",
            json={
                "project_id": project_id,
                "environment_id": environment_id,
                "value": value,
            },
        )
        return data.get("config_environment", {})

    # ── AI Configs ─────────────────────────────────────────────────

    async def list_ai_configs(
        self, project_id: str, environment_id: str | None = None
    ) -> list[ManagedAiConfig]:
        params: dict[str, str] = {"project_id": project_id}
        if environment_id:
            params["environment_id"] = environment_id
        data = await self._http.get(f"{BASE}/ai-configs", params=params)
        return [_parse_managed_ai_config(ac) for ac in data.get("ai_configs", [])]

    async def get_ai_config(
        self, file_name: str, project_id: str, environment_id: str
    ) -> ManagedAiConfig:
        data = await self._http.get(
            f"{BASE}/ai-configs/{quote(file_name, safe='')}",
            params={"project_id": project_id, "environment_id": environment_id},
        )
        return _parse_managed_ai_config(data["ai_config"])

    async def create_ai_config(
        self,
        project_id: str,
        environment_id: str,
        file_name: str,
        file_type: str,
        content: str,
        folder: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ManagedAiConfig:
        body: dict[str, Any] = {
            "project_id": project_id,
            "environment_id": environment_id,
            "file_name": file_name,
            "file_type": file_type,
            "content": content,
        }
        if folder:
            body["folder"] = folder
        if metadata:
            body["metadata"] = metadata
        data = await self._http.post(f"{BASE}/ai-configs", json=body)
        return _parse_managed_ai_config(data["ai_config"])

    async def update_ai_config(
        self, file_name: str, project_id: str, environment_id: str, **kwargs: Any
    ) -> ManagedAiConfig:
        body: dict[str, Any] = {
            "project_id": project_id,
            "environment_id": environment_id,
            **kwargs,
        }
        data = await self._http.put(
            f"{BASE}/ai-configs/{quote(file_name, safe='')}", json=body
        )
        return _parse_managed_ai_config(data["ai_config"])

    async def delete_ai_config(
        self, file_name: str, project_id: str, environment_id: str
    ) -> None:
        await self._http.delete(
            f"{BASE}/ai-configs/{quote(file_name, safe='')}",
            params={"project_id": project_id, "environment_id": environment_id},
        )

    async def initialize_ai_configs(
        self, project_id: str, environment_id: str
    ) -> list[ManagedAiConfig]:
        data = await self._http.post(
            f"{BASE}/ai-configs/initialize",
            json={"project_id": project_id, "environment_id": environment_id},
        )
        return [_parse_managed_ai_config(ac) for ac in data.get("ai_configs", [])]

    # ── Webhooks ───────────────────────────────────────────────────

    async def list_webhooks(self, project_id: str) -> list[WebhookEndpoint]:
        data = await self._http.get(f"{BASE}/webhooks", params={"project_id": project_id})
        return [_parse_webhook(w) for w in data.get("endpoints", [])]

    async def get_webhook(self, webhook_id: str) -> WebhookEndpoint:
        data = await self._http.get(f"{BASE}/webhooks/{webhook_id}")
        return _parse_webhook(data["endpoint"])

    async def create_webhook(
        self,
        project_id: str,
        environment_id: str,
        url: str,
        event_types: list[str],
        description: str | None = None,
    ) -> WebhookEndpoint:
        body: dict[str, Any] = {
            "project_id": project_id,
            "environment_id": environment_id,
            "url": url,
            "event_types": event_types,
        }
        if description:
            body["description"] = description
        data = await self._http.post(f"{BASE}/webhooks", json=body)
        return _parse_webhook(data["endpoint"])

    async def update_webhook(self, webhook_id: str, **kwargs: Any) -> WebhookEndpoint:
        data = await self._http.put(f"{BASE}/webhooks/{webhook_id}", json=kwargs)
        return _parse_webhook(data["endpoint"])

    async def delete_webhook(self, webhook_id: str) -> None:
        await self._http.delete(f"{BASE}/webhooks/{webhook_id}")

    async def regenerate_webhook_secret(self, webhook_id: str) -> WebhookEndpoint:
        data = await self._http.post(f"{BASE}/webhooks/{webhook_id}/regenerate-secret")
        return _parse_webhook(data["endpoint"])

    async def reactivate_webhook(self, webhook_id: str) -> WebhookEndpoint:
        data = await self._http.post(f"{BASE}/webhooks/{webhook_id}/reactivate")
        return _parse_webhook(data["endpoint"])

    async def list_webhook_deliveries(
        self, webhook_id: str, limit: int = 20, offset: int = 0
    ) -> list[WebhookDelivery]:
        data = await self._http.get(
            f"{BASE}/webhooks/{webhook_id}/deliveries",
            params={"limit": str(limit), "offset": str(offset)},
        )
        return [_parse_delivery(d) for d in data.get("deliveries", [])]
