"""Type definitions for FlagDash SDK responses and inputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

# ── Evaluation context ─────────────────────────────────────────────

@dataclass
class EvaluationContext:
    """Context passed to flag evaluation for targeting and rollout."""

    user_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_query_params(self) -> dict[str, str]:
        """Convert context to query parameters for API requests."""
        params: dict[str, str] = {}
        if self.user_id:
            params["user_id"] = self.user_id
        for key, value in self.attributes.items():
            params[key] = str(value)
        return params


# ── Client-tier types ──────────────────────────────────────────────

@dataclass
class AiConfigReleaseResult:
    """Selected release configuration; secret references remain unresolved."""

    key: str
    version: int
    config: dict[str, Any]
    reason: str
    variation_key: str | None
    rollout_percentage: int


@dataclass
class FlagValue:
    """Evaluated flag value from the client API."""

    key: str
    value: Any
    variation_key: str | None = None


@dataclass
class FlagDetailResult:
    """Detailed flag evaluation result including reason and variation info."""

    key: str
    value: Any
    reason: Literal["disabled", "rule_match", "variation", "rollout", "default"]
    variation_key: str | None = None


@dataclass
class ExperimentAssignment:
    """Stable assignment returned by the experimentation API."""

    key: str
    status: Literal["testing", "running", "paused"]
    variant_key: str
    parameters: dict[str, Any]
    reason: Literal["experiment"] = "experiment"


@dataclass
class ConfigValue:
    """Config value from the client API."""

    key: str
    value: Any


@dataclass
class AiConfig:
    """AI config file from the client API."""

    file_name: str
    file_type: Literal["agent", "skill", "rule"]
    content: str
    folder: str | None = None


# ── Server-tier types ──────────────────────────────────────────────

@dataclass
class TargetingRule:
    """A targeting rule on a flag."""

    id: str
    attribute: str
    operator: str
    value: Any
    flag_value: Any


@dataclass
class FlagVariation:
    """A variation for A/B testing."""

    id: str
    key: str
    name: str
    value: Any
    weight: int


@dataclass
class FlagSchedule:
    """A pending schedule for a flag."""

    id: str
    action: str
    scheduled_at: str
    status: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class Flag:
    """Full flag with rules and metadata (server tier)."""

    key: str
    name: str
    description: str
    flag_type: Literal["boolean", "string", "number", "json"]
    default_value: Any
    tags: list[str]
    enabled: bool
    value: Any
    rules: Any
    rollout_percentage: int
    evaluated_value: Any
    variation_key: str | None = None
    evaluation_path: str | None = None
    variations: list[FlagVariation] = field(default_factory=list)
    pending_schedules: list[FlagSchedule] = field(default_factory=list)


@dataclass
class Config:
    """Full config with metadata (server tier)."""

    key: str
    name: str
    description: str
    config_type: Literal["json", "string", "number", "boolean"]
    default_value: Any
    tags: list[str]
    value: Any
    is_active: bool


@dataclass
class Secret:
    """An encrypted secret, decrypted for one response.

    Secrets are a separate resource from Remote Config: server tier only, never
    cached by this SDK, and never served to a browser or mobile client.
    """

    key: str
    format: Literal["string", "json"]
    value: Any
    version_id: str
    created_at: str
    created_by_id: str


@dataclass
class ServerAiConfig:
    """AI config with full metadata (server tier)."""

    id: str
    file_name: str
    file_type: Literal["agent", "skill", "rule"]
    content: str
    is_active: bool
    metadata: dict[str, Any]
    folder: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


# ── Management-tier types ──────────────────────────────────────────

@dataclass
class ManagedFlag:
    """Flag returned by management API (includes environments)."""

    id: str
    key: str
    name: str
    description: str
    flag_type: str
    default_value: Any
    tags: list[str]
    is_archived: bool
    created_at: str
    updated_at: str
    environments: list[FlagEnvironment] = field(default_factory=list)


@dataclass
class FlagEnvironment:
    """Flag environment settings."""

    id: str
    environment_id: str
    enabled: bool
    value: Any
    rules: Any
    rollout_percentage: int


@dataclass
class ManagedConfig:
    """Config returned by management API (includes environments)."""

    id: str
    key: str
    name: str
    description: str
    config_type: str
    default_value: Any
    tags: list[str]
    is_archived: bool
    created_at: str
    updated_at: str
    environments: list[ConfigEnvironment] = field(default_factory=list)


@dataclass
class ConfigEnvironment:
    """Config environment settings."""

    id: str
    environment_id: str
    value: Any
    is_active: bool


@dataclass
class ManagedAiConfig:
    """AI config returned by management API."""

    id: str
    file_name: str
    file_type: str
    content: str
    is_active: bool
    metadata: dict[str, Any]
    folder: str | None
    project_id: str
    environment_id: str
    created_at: str
    updated_at: str


@dataclass
class WebhookEndpoint:
    """Webhook endpoint returned by management API."""

    id: str
    url: str
    description: str | None
    environment_id: str
    event_types: list[str]
    is_active: bool
    consecutive_failures: int
    disabled_at: str | None
    disabled_reason: str | None
    signing_secret: str | None
    created_at: str
    updated_at: str


@dataclass
class WebhookDelivery:
    """Webhook delivery log entry."""

    id: str
    event_type: str
    status: str
    http_status: int | None
    error_message: str | None
    attempt_count: int
    max_attempts: int
    completed_at: str | None
    created_at: str


@dataclass
class FlagScheduleDetail:
    """Schedule entry from the management API."""

    id: str
    action: str
    scheduled_at: str
    status: str
    payload: dict[str, Any]
    executed_at: str | None = None
    error_message: str | None = None
    created_at: str | None = None
