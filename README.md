# FlagDash Python SDK

Official Python SDK for [FlagDash](https://flagdash.io) — Feature Flags, Remote Config & AI Config Management.

## Installation

```bash
pip install flagdash
```

## Quick Start

### Client SDK (Browser / Edge)

Use a `client_` API key for read-only access to evaluated values:

```python
from flagdash import FlagDashClient, EvaluationContext

client = FlagDashClient(
    sdk_key="client_your_key_here",
)

# Evaluate a feature flag
dark_mode = client.flag("dark-mode", default=False)

# Evaluate with user context
ctx = EvaluationContext(user_id="alice", attributes={"plan": "pro"})
value = client.flag("premium-features", default=False, context=ctx)

# Get a remote config
api_url = client.config("api-url", default="https://api.default.com")

# Get AI config files
agent = client.ai_config("agent.md")

client.close()
```

### Server SDK (Backend)

Use a `server_` API key for full flag metadata and built-in TTL caching:

```python
from flagdash import FlagDashServerClient, EvaluationContext

with FlagDashServerClient(
    sdk_key="server_your_key_here",
    cache_ttl=60.0,  # Cache for 60 seconds (default)
) as client:
    # Evaluate a flag (cached)
    enabled = client.flag("checkout-v2", default=False)

    # Evaluate with context (bypasses cache)
    ctx = EvaluationContext(user_id="alice", attributes={"country": "US"})
    value = client.flag("checkout-v2", default=False, context=ctx)

    # Get full flag details
    flag = client.get_flag("checkout-v2")
    print(flag.name, flag.rollout_percentage, flag.variations)

    # List all configs with metadata
    configs = client.list_configs()
```

### Management SDK

Use a `management_` API key for full CRUD operations:

```python
from flagdash import FlagDashManagementClient

with FlagDashManagementClient(sdk_key="sk_your_key") as mgmt:
    # Create a flag
    flag = mgmt.create_flag(
        project_id="prj_xxx",
        key="new-checkout",
        name="New Checkout",
        flag_type="boolean",
        tags=["checkout"],
    )

    # Toggle it on
    mgmt.toggle_flag("new-checkout", "prj_xxx", "env_xxx")

    # Set rollout to 50%
    mgmt.set_rollout("new-checkout", "prj_xxx", "env_xxx", 50)

    # Set A/B variations
    mgmt.set_variations("new-checkout", "prj_xxx", "env_xxx", [
        {"key": "control", "name": "Control", "value": {"value": False}, "weight": 50},
        {"key": "variant", "name": "Variant", "value": {"value": True}, "weight": 50},
    ])

    # Manage configs
    mgmt.create_config(project_id="prj_xxx", key="api-url", name="API URL", config_type="string")

    # Manage AI configs
    mgmt.create_ai_config(
        project_id="prj_xxx",
        environment_id="env_xxx",
        file_name="agent.md",
        file_type="agent",
        content="# My Agent\n\nYou are a helpful assistant.",
    )

    # Manage webhooks
    webhook = mgmt.create_webhook(
        project_id="prj_xxx",
        environment_id="env_xxx",
        url="https://your-app.com/hooks",
        event_types=["flag.updated", "config.updated"],
    )
```

## Async Support

All clients have async variants:

```python
import asyncio
from flagdash import FlagDashAsyncClient, FlagDashAsyncServerClient

async def main():
    async with FlagDashAsyncClient(sdk_key="client_xxx") as client:
        value = await client.flag("dark-mode", default=False)
        configs = await client.list_ai_configs()

    async with FlagDashAsyncServerClient(
        sdk_key="server_xxx",
    ) as server:
        flag = await server.get_flag("checkout-v2")

asyncio.run(main())
```

## API Reference

### FlagDashClient

| Method | Description |
|--------|-------------|
| `flag(key, default, context)` | Evaluate a feature flag |
| `all_flags(context)` | Get all flags as key→value dict |
| `config(key, default)` | Get a config value |
| `all_configs()` | Get all config values |
| `ai_config(file_name)` | Get an AI config file |
| `list_ai_configs()` | List all active AI configs |

### FlagDashServerClient

| Method | Description |
|--------|-------------|
| `flag(key, default, context)` | Evaluate a flag (cached) |
| `all_flags(context)` | Get all evaluated values |
| `get_flag(key)` | Get flag with full metadata |
| `list_flags()` | List all flags with metadata |
| `config(key, default)` | Get a config value (cached) |
| `get_config(key)` | Get config with metadata |
| `list_configs()` | List all configs |
| `ai_config(file_name)` | Get AI config with metadata |
| `list_ai_configs()` | List all AI configs |
| `clear_cache()` | Clear TTL cache |

### FlagDashManagementClient

#### Flags
| Method | Description |
|--------|-------------|
| `list_flags(project_id)` | List all flags |
| `get_flag(key, project_id)` | Get a flag |
| `create_flag(project_id, key, name, ...)` | Create a flag |
| `update_flag(key, project_id, **kwargs)` | Update a flag |
| `delete_flag(key, project_id)` | Delete a flag |
| `toggle_flag(key, project_id, env_id)` | Toggle on/off |
| `set_rollout(key, project_id, env_id, pct)` | Set rollout % |
| `update_rules(key, project_id, env_id, rules)` | Update targeting rules |
| `set_variations(key, project_id, env_id, vars)` | Set A/B variations |
| `delete_variations(key, project_id, env_id)` | Remove variations |

#### Schedules
| Method | Description |
|--------|-------------|
| `list_schedules(key, project_id, env_id)` | List schedules |
| `create_schedule(key, project_id, env_id, action, scheduled_at)` | Create schedule |
| `cancel_schedule(key, project_id, schedule_id)` | Cancel schedule |

#### Configs
| Method | Description |
|--------|-------------|
| `list_configs(project_id)` | List all configs |
| `get_config(key, project_id)` | Get a config |
| `create_config(project_id, key, name, ...)` | Create a config |
| `update_config(key, project_id, **kwargs)` | Update a config |
| `delete_config(key, project_id)` | Delete a config |
| `update_config_value(key, project_id, env_id, value)` | Set env value |

#### AI Configs
| Method | Description |
|--------|-------------|
| `list_ai_configs(project_id, env_id?)` | List AI configs |
| `get_ai_config(file_name, project_id, env_id)` | Get AI config |
| `create_ai_config(project_id, env_id, file_name, ...)` | Create AI config |
| `update_ai_config(file_name, project_id, env_id, ...)` | Update AI config |
| `delete_ai_config(file_name, project_id, env_id)` | Delete AI config |
| `initialize_ai_configs(project_id, env_id)` | Initialize defaults |

#### Webhooks
| Method | Description |
|--------|-------------|
| `list_webhooks(project_id)` | List endpoints |
| `get_webhook(webhook_id)` | Get endpoint |
| `create_webhook(project_id, env_id, url, events)` | Create endpoint |
| `update_webhook(webhook_id, **kwargs)` | Update endpoint |
| `delete_webhook(webhook_id)` | Delete endpoint |
| `regenerate_webhook_secret(webhook_id)` | New signing secret |
| `reactivate_webhook(webhook_id)` | Reactivate disabled endpoint |
| `list_webhook_deliveries(webhook_id, limit, offset)` | Delivery logs |

## Session replay

Backend replay records an explicit timeline — only the actions you name. It never
captures request bodies, logs, or input values on its own.

```python
import os
from flagdash import FlagDashBackendReplay

replay = FlagDashBackendReplay(
    os.environ["FLAGDASH_REPLAY_KEY"],   # needs the `replays:write` scope
    release="2026.08",
    metadata={"service": "checkout"},
)

if replay.start():
    replay.event("checkout_started", attributes={"items": 2})
    replay.breadcrumb("coupon applied")
    replay.capture_exception(error, attributes={"stage": "authorise"})

# Correlate a browser recording with this backend timeline
headers.update(replay.context_headers())

replay.stop()
```

Attribute keys that look sensitive — `password`, `token`, `authorization`,
`api_key`, `card`, and similar — are redacted before the event is buffered.

## Exception Handling

```python
from flagdash import FlagDashClient
from flagdash.exceptions import (
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    TimeoutError,
    FlagDashError,
)

try:
    client = FlagDashClient(sdk_key="client_xxx")
    client.all_flags()
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
except FlagDashError as e:
    print(f"API error: {e} (status={e.status_code})")
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `sdk_key` | (required) | API key (`client_`, `server_`, or `management_` prefix) |
| `base_url` | `https://flagdash.io` | FlagDash instance URL |
| `timeout` | `5.0` (client/server), `10.0` (management) | Request timeout in seconds |
| `cache_ttl` | `60.0` | Cache TTL in seconds (server only, 0 to disable) |

## Requirements

- Python 3.9+
- httpx >= 0.24.0

## License

MIT

## AI releases

Create a release in **Manage → AI Releases**, select the environment, then set
a baseline, candidate and rollout. With your initialized client, evaluate it using
an environment-bound key with `ai_configs:read`:

```python
release = client.ai_config_release("support-agent", user_id="usr_123")
# Async clients: release = await client.ai_config_release(...)
```

The result includes `key`, `version`, `config`, `reason`, `variation_key`, and
`rollout_percentage` (idiomatic field names for typed SDKs). Pass a stable user
identity. Decisions are fetched afresh; verify baseline, rollout and paused
behavior in development before ramping production. Your backend calls the AI
provider. Ordinary evaluation leaves secret references unresolved; never put
provider credentials in a configuration delivered to browsers or mobile apps.
See the [release guide](../../docs/ai-config-releases.md) for lifecycle and cleanup.
