"""Tests for the client-tier SDK."""

from __future__ import annotations

import pytest

from flagdash.client import FlagDashClient


class TestFlagDashClient:
    def test_requires_sdk_key(self) -> None:
        with pytest.raises(ValueError, match="sdk_key is required"):
            FlagDashClient(sdk_key="")

    def test_context_manager(self, mock_http) -> None:
        with FlagDashClient(sdk_key="client_test") as client:
            assert client is not None

    def test_flag_returns_value(self, mock_http) -> None:
        mock_http.register("GET", "/flags/dark-mode", {"key": "dark-mode", "value": True})
        client = FlagDashClient(sdk_key="client_test")
        try:
            assert client.flag("dark-mode") is True
        finally:
            client.close()

    def test_flag_returns_default_on_error(self, mock_http) -> None:
        mock_http.register("GET", "/flags/missing", error=True)
        client = FlagDashClient(sdk_key="client_test")
        try:
            assert client.flag("missing", default=False) is False
        finally:
            client.close()

    def test_all_flags(self, mock_http) -> None:
        mock_http.register("GET", "/flags", {"flags": {"a": True, "b": "v1"}})
        client = FlagDashClient(sdk_key="client_test")
        try:
            flags = client.all_flags()
            assert flags == {"a": True, "b": "v1"}
        finally:
            client.close()

    def test_experiment_returns_assignment(self, mock_http) -> None:
        mock_http.register("GET", "/experiments/checkout-flow", {
            "experiment": {
                "key": "checkout-flow",
                "status": "running",
                "variant_key": "treatment",
                "parameters": {"button_color": "violet"},
            }
        })
        from flagdash.types import EvaluationContext

        client = FlagDashClient(sdk_key="client_test")
        try:
            assignment = client.experiment(
                "checkout-flow", EvaluationContext(user_id="user-123")
            )
            assert assignment is not None
            assert assignment.variant_key == "treatment"
            assert assignment.parameters == {"button_color": "violet"}
        finally:
            client.close()

    def test_experiment_requires_stable_identity(self, mock_http) -> None:
        from flagdash.types import EvaluationContext

        client = FlagDashClient(sdk_key="client_test")
        try:
            assert client.experiment("checkout-flow", EvaluationContext()) is None
        finally:
            client.close()

    def test_experiment_metric_batch(self, mock_http) -> None:
        from flagdash.types import EvaluationContext
        mock_http.register("POST", "/experiment-events/batch", {"accepted": 1})
        client = FlagDashClient(sdk_key="client_test")
        client.track_experiment_metric(
            "checkout-flow",
            "checkout_completed",
            EvaluationContext(user_id="user-123"),
            event_id="evt-fixed",
        )
        client.flush_experiment_events()
        client.close()

    def test_config_returns_value(self, mock_http) -> None:
        mock_http.register("GET", "/configs/api-url", {"key": "api-url", "value": "https://api.example.com"})
        client = FlagDashClient(sdk_key="client_test")
        try:
            assert client.config("api-url") == "https://api.example.com"
        finally:
            client.close()

    def test_all_configs(self, mock_http) -> None:
        mock_http.register("GET", "/configs", {
            "configs": [
                {"key": "k1", "value": "v1"},
                {"key": "k2", "value": 42},
            ]
        })
        client = FlagDashClient(sdk_key="client_test")
        try:
            configs = client.all_configs()
            assert len(configs) == 2
            assert configs[0].key == "k1"
        finally:
            client.close()

    def test_ai_config(self, mock_http) -> None:
        mock_http.register("GET", "/ai-configs/agent.md", {
            "ai_config": {
                "file_name": "agent.md",
                "file_type": "agent",
                "content": "# Agent",
                "folder": None,
            }
        })
        client = FlagDashClient(sdk_key="client_test")
        try:
            ac = client.ai_config("agent.md")
            assert ac is not None
            assert ac.file_name == "agent.md"
            assert ac.content == "# Agent"
        finally:
            client.close()

    def test_flag_detail_returns_full_result(self, mock_http) -> None:
        mock_http.register("GET", "/flags/my-flag", {
            "key": "my-flag", "value": True, "reason": "rollout", "variation_key": None,
        })
        client = FlagDashClient(sdk_key="client_test")
        try:
            result = client.flag_detail("my-flag")
            assert result.key == "my-flag"
            assert result.value is True
            assert result.reason == "rollout"
            assert result.variation_key is None
        finally:
            client.close()

    def test_flag_detail_with_variation(self, mock_http) -> None:
        mock_http.register("GET", "/flags/ab-test", {
            "key": "ab-test", "value": "blue", "reason": "variation", "variation_key": "b",
        })
        client = FlagDashClient(sdk_key="client_test")
        try:
            result = client.flag_detail("ab-test")
            assert result.key == "ab-test"
            assert result.value == "blue"
            assert result.reason == "variation"
            assert result.variation_key == "b"
        finally:
            client.close()

    def test_flag_detail_returns_default_on_error(self, mock_http) -> None:
        mock_http.register("GET", "/flags/missing", error=True)
        client = FlagDashClient(sdk_key="client_test")
        try:
            result = client.flag_detail("missing", default=False)
            assert result.key == "missing"
            assert result.value is False
            assert result.reason == "default"
            assert result.variation_key is None
        finally:
            client.close()

    def test_flag_detail_with_context(self, mock_http) -> None:
        mock_http.register("GET", "/flags/targeted", {
            "key": "targeted", "value": True, "reason": "rule_match",
        })
        from flagdash.types import EvaluationContext
        ctx = EvaluationContext(user_id="alice", attributes={"country": "US"})
        client = FlagDashClient(sdk_key="client_test")
        try:
            result = client.flag_detail("targeted", context=ctx)
            assert result.key == "targeted"
            assert result.value is True
            assert result.reason == "rule_match"
            assert result.variation_key is None
        finally:
            client.close()

    def test_list_ai_configs(self, mock_http) -> None:
        mock_http.register("GET", "/ai-configs", {
            "ai_configs": [
                {
                    "file_name": "agent.md",
                    "file_type": "agent",
                    "content": "# Agent",
                    "folder": None,
                },
                {
                    "file_name": "debug.md",
                    "file_type": "skill",
                    "content": "# Debug",
                    "folder": "skills",
                },
            ]
        })
        client = FlagDashClient(sdk_key="client_test")
        try:
            configs = client.list_ai_configs()
            assert len(configs) == 2
            assert configs[1].folder == "skills"
        finally:
            client.close()


@pytest.fixture
def mock_http(monkeypatch):
    """Mock the HttpClient to avoid real HTTP calls."""
    return MockHttp(monkeypatch)


class MockHttp:
    def __init__(self, monkeypatch) -> None:
        self._registry: dict[str, dict] = {}
        self._monkeypatch = monkeypatch
        self._patch()

    def register(
        self, method: str, path: str, response: dict | None = None, error: bool = False
    ) -> None:
        self._registry[f"{method}:{path}"] = {"response": response, "error": error}

    def _patch(self) -> None:
        mock = self
        from flagdash import http_client as hc

        class FakeHttpClient:
            def __init__(self, **kwargs):
                pass

            def get(self, path, params=None):
                key = f"GET:{path}"
                entry = mock._registry.get(key)
                if entry is None:
                    for k, v in mock._registry.items():
                        if k.startswith("GET:") and path.startswith(k.split(":", 1)[1]):
                            entry = v
                            break
                if entry and entry.get("error"):
                    raise Exception("mock error")
                if entry:
                    return entry["response"]
                raise Exception(f"No mock for {key}")

            def post(self, path, json=None):
                return mock._registry.get(f"POST:{path}", {}).get("response", {})

            def put(self, path, json=None):
                return mock._registry.get(f"PUT:{path}", {}).get("response", {})

            def delete(self, path, params=None):
                return mock._registry.get(f"DELETE:{path}", {}).get("response")

            def close(self):
                pass

        self._monkeypatch.setattr(hc, "HttpClient", FakeHttpClient)
        import flagdash.client as client_mod
        self._monkeypatch.setattr(client_mod, "HttpClient", FakeHttpClient)
