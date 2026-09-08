"""Tests for the management-tier SDK."""

from __future__ import annotations

import pytest

from flagdash.management import FlagDashManagementClient


class TestFlagDashManagementClient:
    def test_requires_sdk_key(self) -> None:
        with pytest.raises(ValueError, match="sdk_key is required"):
            FlagDashManagementClient(sdk_key="")

    def test_list_flags(self, mock_mgmt_http) -> None:
        mock_mgmt_http.register("GET", "/manage/flags", {
            "flags": [{
                "id": "flg_1",
                "key": "checkout-v2",
                "name": "Checkout V2",
                "description": "New checkout",
                "flag_type": "boolean",
                "default_value": None,
                "tags": [],
                "is_archived": False,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "environments": [],
            }]
        })
        with FlagDashManagementClient(sdk_key="management_test") as mgmt:
            flags = mgmt.list_flags("prj_1")
            assert len(flags) == 1
            assert flags[0].key == "checkout-v2"

    def test_create_flag(self, mock_mgmt_http) -> None:
        mock_mgmt_http.register("POST", "/manage/flags", {
            "flag": {
                "id": "flg_2",
                "key": "new-feature",
                "name": "New Feature",
                "description": "",
                "flag_type": "boolean",
                "default_value": None,
                "tags": ["beta"],
                "is_archived": False,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            }
        })
        with FlagDashManagementClient(sdk_key="management_test") as mgmt:
            flag = mgmt.create_flag(
                project_id="prj_1",
                key="new-feature",
                name="New Feature",
                tags=["beta"],
            )
            assert flag.key == "new-feature"
            assert flag.tags == ["beta"]

    def test_delete_flag(self, mock_mgmt_http) -> None:
        mock_mgmt_http.register("DELETE", "/manage/flags/old-flag", None)
        with FlagDashManagementClient(sdk_key="management_test") as mgmt:
            mgmt.delete_flag("old-flag", "prj_1")

    def test_list_configs(self, mock_mgmt_http) -> None:
        mock_mgmt_http.register("GET", "/manage/configs", {
            "configs": [{
                "id": "cfg_1",
                "key": "api-url",
                "name": "API URL",
                "description": "",
                "config_type": "string",
                "default_value": {"value": "https://api.example.com"},
                "tags": [],
                "is_archived": False,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "environments": [],
            }]
        })
        with FlagDashManagementClient(sdk_key="management_test") as mgmt:
            configs = mgmt.list_configs("prj_1")
            assert len(configs) == 1
            assert configs[0].key == "api-url"

    def test_list_ai_configs(self, mock_mgmt_http) -> None:
        mock_mgmt_http.register("GET", "/manage/ai-configs", {
            "ai_configs": [{
                "id": "aic_1",
                "file_name": "agent.md",
                "file_type": "agent",
                "content": "# Agent",
                "is_active": True,
                "metadata": {},
                "folder": None,
                "project_id": "prj_1",
                "environment_id": "env_1",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            }]
        })
        with FlagDashManagementClient(sdk_key="management_test") as mgmt:
            configs = mgmt.list_ai_configs("prj_1", "env_1")
            assert len(configs) == 1
            assert configs[0].file_name == "agent.md"

    def test_list_webhooks(self, mock_mgmt_http) -> None:
        mock_mgmt_http.register("GET", "/manage/webhooks", {
            "endpoints": [{
                "id": "wh_1",
                "url": "https://example.com/webhook",
                "description": "Test",
                "environment_id": "env_1",
                "event_types": ["flag.updated"],
                "is_active": True,
                "consecutive_failures": 0,
                "disabled_at": None,
                "disabled_reason": None,
                "signing_secret": "whsec_test...",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            }]
        })
        with FlagDashManagementClient(sdk_key="management_test") as mgmt:
            webhooks = mgmt.list_webhooks("prj_1")
            assert len(webhooks) == 1
            assert webhooks[0].url == "https://example.com/webhook"


@pytest.fixture
def mock_mgmt_http(monkeypatch):
    return MockMgmtHttp(monkeypatch)


class MockMgmtHttp:
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
                key = f"POST:{path}"
                entry = mock._registry.get(key)
                if entry is None:
                    for k, v in mock._registry.items():
                        registered_path = k.split(":", 1)[1]
                        if k.startswith("POST:") and path.startswith(registered_path):
                            entry = v
                            break
                if entry:
                    return entry["response"]
                return {}

            def put(self, path, json=None):
                key = f"PUT:{path}"
                entry = mock._registry.get(key)
                if entry:
                    return entry["response"]
                return {}

            def delete(self, path, params=None):
                key = f"DELETE:{path}"
                entry = mock._registry.get(key)
                if entry is None:
                    for k, v in mock._registry.items():
                        registered_path = k.split(":", 1)[1]
                        if k.startswith("DELETE:") and path.startswith(registered_path):
                            entry = v
                            break
                if entry:
                    return entry["response"]
                return None

            def close(self):
                pass

        self._monkeypatch.setattr(hc, "HttpClient", FakeHttpClient)
        import flagdash.management as mgmt_mod
        self._monkeypatch.setattr(mgmt_mod, "HttpClient", FakeHttpClient)
