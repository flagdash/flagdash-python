"""Tests for the server-tier SDK."""

from __future__ import annotations

import pytest

from flagdash.server_client import FlagDashServerClient


class TestFlagDashServerClient:
    def test_requires_sdk_key(self) -> None:
        with pytest.raises(ValueError, match="sdk_key is required"):
            FlagDashServerClient(sdk_key="")

    def test_flag_uses_cache(self, mock_server_http) -> None:
        mock_server_http.register("GET", "/server/flags", {
            "flags": [],
            "evaluated": {"checkout-v2": True, "beta": False},
        })
        client = FlagDashServerClient(
            sdk_key="server_test", cache_ttl=60.0
        )
        try:
            assert client.flag("checkout-v2") is True
            assert client.flag("checkout-v2") is True
            assert client.flag("beta") is False
        finally:
            client.close()

    def test_flag_default_on_miss(self, mock_server_http) -> None:
        mock_server_http.register("GET", "/server/flags", {
            "flags": [],
            "evaluated": {},
        })
        client = FlagDashServerClient(
            sdk_key="server_test"
        )
        try:
            assert client.flag("missing", default="fallback") == "fallback"
        finally:
            client.close()

    def test_all_flags(self, mock_server_http) -> None:
        mock_server_http.register("GET", "/server/flags", {
            "flags": [],
            "evaluated": {"a": 1, "b": 2},
        })
        client = FlagDashServerClient(
            sdk_key="server_test"
        )
        try:
            flags = client.all_flags()
            assert flags == {"a": 1, "b": 2}
        finally:
            client.close()

    def test_list_flags(self, mock_server_http) -> None:
        mock_server_http.register("GET", "/server/flags", {
            "flags": [{
                "key": "test",
                "name": "Test",
                "description": "",
                "flag_type": "boolean",
                "default_value": None,
                "tags": [],
                "enabled": True,
                "value": None,
                "rules": None,
                "rollout_percentage": 100,
                "evaluated_value": True,
                "variations": [],
                "pending_schedules": [],
            }],
            "evaluated": {"test": True},
        })
        client = FlagDashServerClient(
            sdk_key="server_test"
        )
        try:
            flags = client.list_flags()
            assert len(flags) == 1
            assert flags[0].key == "test"
            assert flags[0].enabled is True
        finally:
            client.close()

    def test_clear_cache(self, mock_server_http) -> None:
        mock_server_http.register("GET", "/server/flags", {
            "flags": [],
            "evaluated": {"x": True},
        })
        client = FlagDashServerClient(
            sdk_key="server_test", cache_ttl=60.0
        )
        try:
            client.flag("x")
            client.clear_cache()
            assert client._cache.get("flag:x") is None
        finally:
            client.close()

    def test_list_configs(self, mock_server_http) -> None:
        mock_server_http.register("GET", "/server/configs", {
            "configs": [{
                "key": "api-url",
                "name": "API URL",
                "description": "",
                "config_type": "string",
                "default_value": None,
                "tags": [],
                "value": {"value": "https://api.example.com"},
                "is_active": True,
            }]
        })
        client = FlagDashServerClient(
            sdk_key="server_test"
        )
        try:
            configs = client.list_configs()
            assert len(configs) == 1
            assert configs[0].key == "api-url"
        finally:
            client.close()

    def test_list_ai_configs(self, mock_server_http) -> None:
        mock_server_http.register("GET", "/server/ai-configs", {
            "ai_configs": [{
                "id": "aic_1",
                "file_name": "agent.md",
                "file_type": "agent",
                "content": "# Agent",
                "is_active": True,
                "metadata": {},
                "folder": None,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            }]
        })
        client = FlagDashServerClient(
            sdk_key="server_test"
        )
        try:
            configs = client.list_ai_configs()
            assert len(configs) == 1
            assert configs[0].file_name == "agent.md"
        finally:
            client.close()


@pytest.fixture
def mock_server_http(monkeypatch):
    return MockServerHttp(monkeypatch)


class MockServerHttp:
    def __init__(self, monkeypatch) -> None:
        self._registry: dict[str, dict] = {}
        self._monkeypatch = monkeypatch
        self._patch()

    def register(self, method: str, path: str, response: dict | None = None) -> None:
        self._registry[f"{method}:{path}"] = {"response": response}

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
                        registered_path = k.split(":", 1)[1]
                        if k.startswith("GET:") and path.startswith(registered_path):
                            entry = v
                            break
                if entry:
                    return entry["response"]
                raise Exception(f"No mock for GET:{path}")

            def post(self, path, json=None):
                return mock._registry.get(f"POST:{path}", {}).get("response", {})

            def put(self, path, json=None):
                return mock._registry.get(f"PUT:{path}", {}).get("response", {})

            def delete(self, path, params=None):
                return mock._registry.get(f"DELETE:{path}", {}).get("response")

            def close(self):
                pass

        self._monkeypatch.setattr(hc, "HttpClient", FakeHttpClient)
        import flagdash.server_client as sc_mod
        self._monkeypatch.setattr(sc_mod, "HttpClient", FakeHttpClient)
