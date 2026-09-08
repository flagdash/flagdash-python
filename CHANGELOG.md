# Changelog

## 0.1.0 (2026-02-17)

### Added

- `FlagDashClient` — Client-tier SDK for evaluating flags, configs, and AI configs
- `FlagDashServerClient` — Server-tier SDK with TTL caching and full metadata
- `FlagDashManagementClient` — Management-tier SDK with full CRUD for flags, configs, AI configs, and webhooks
- `FlagDashAsyncClient` — Async client-tier SDK
- `FlagDashAsyncServerClient` — Async server-tier SDK
- `FlagDashAsyncManagementClient` — Async management-tier SDK
- Thread-safe TTL cache for server-tier caching
- Typed dataclasses for all API responses
- Exception hierarchy: `FlagDashError`, `AuthenticationError`, `NotFoundError`, `ValidationError`, `RateLimitError`, `TimeoutError`
- Context managers for all client classes
- Full test suite with pytest
- Examples for all tiers (sync and async)
- GitHub Actions workflows for testing and PyPI publishing
