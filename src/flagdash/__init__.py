"""FlagDash Python SDK — Feature Flags, Remote Config & AI Config Management."""

from flagdash.client import FlagDashAsyncClient, FlagDashClient
from flagdash.exceptions import (
    AuthenticationError,
    FlagDashError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
from flagdash.management import (
    FlagDashAsyncManagementClient,
    FlagDashManagementClient,
)
from flagdash.replay import FlagDashBackendReplay
from flagdash.server_client import (
    FlagDashAsyncServerClient,
    FlagDashServerClient,
)
from flagdash.types import (
    AiConfigReleaseResult,
    AiConfig,
    Config,
    ConfigEnvironment,
    ConfigValue,
    EvaluationContext,
    ExperimentAssignment,
    Flag,
    FlagDetailResult,
    FlagEnvironment,
    FlagSchedule,
    FlagScheduleDetail,
    FlagValue,
    FlagVariation,
    ManagedAiConfig,
    ManagedConfig,
    ManagedFlag,
    Secret,
    ServerAiConfig,
    TargetingRule,
    WebhookDelivery,
    WebhookEndpoint,
)

__all__ = [
    # Clients
    "FlagDashClient",
    "FlagDashAsyncClient",
    "FlagDashServerClient",
    "FlagDashAsyncServerClient",
    "FlagDashManagementClient",
    "FlagDashAsyncManagementClient",
    "FlagDashBackendReplay",
    # Types
    "AiConfigReleaseResult",
    "AiConfig",
    "Config",
    "ConfigEnvironment",
    "ConfigValue",
    "EvaluationContext",
    "ExperimentAssignment",
    "Flag",
    "FlagDetailResult",
    "FlagEnvironment",
    "FlagSchedule",
    "FlagScheduleDetail",
    "FlagValue",
    "FlagVariation",
    "ManagedAiConfig",
    "ManagedConfig",
    "ManagedFlag",
    "Secret",
    "ServerAiConfig",
    "TargetingRule",
    "WebhookDelivery",
    "WebhookEndpoint",
    # Exceptions
    "FlagDashError",
    "AuthenticationError",
    "ForbiddenError",
    "NotFoundError",
    "RateLimitError",
    "TimeoutError",
    "ValidationError",
]

__version__ = "0.1.0"
