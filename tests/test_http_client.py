"""Tests for the HTTP client wrapper."""

from __future__ import annotations

import httpx
import pytest

from flagdash.exceptions import (
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from flagdash.http_client import HttpClient


class TestHttpClient:
    def test_get_success(self, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://flagdash.io/api/v1/flags",
            json={"flags": {"dark-mode": True}},
        )
        client = HttpClient(sdk_key="client_test", base_url="https://flagdash.io")
        try:
            data = client.get("/flags")
            assert data == {"flags": {"dark-mode": True}}
        finally:
            client.close()

    def test_auth_header(self, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://flagdash.io/api/v1/flags",
            json={},
        )
        client = HttpClient(sdk_key="client_mykey", base_url="https://flagdash.io")
        try:
            client.get("/flags")
            request = httpx_mock.get_requests()[0]
            assert request.headers["authorization"] == "Bearer client_mykey"
        finally:
            client.close()

    def test_401_raises_auth_error(self, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://flagdash.io/api/v1/flags",
            status_code=401,
            json={"error": "Invalid API key"},
        )
        client = HttpClient(sdk_key="bad_key", base_url="https://flagdash.io")
        try:
            with pytest.raises(AuthenticationError, match="Invalid API key"):
                client.get("/flags")
        finally:
            client.close()

    def test_403_raises_forbidden(self, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://flagdash.io/api/v1/manage/flags",
            status_code=403,
            json={"error": "Requires management key"},
        )
        client = HttpClient(sdk_key="client_key", base_url="https://flagdash.io")
        try:
            with pytest.raises(ForbiddenError):
                client.get("/manage/flags")
        finally:
            client.close()

    def test_404_raises_not_found(self, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://flagdash.io/api/v1/flags/missing",
            status_code=404,
            json={"error": "Not found"},
        )
        client = HttpClient(sdk_key="client_key", base_url="https://flagdash.io")
        try:
            with pytest.raises(NotFoundError):
                client.get("/flags/missing")
        finally:
            client.close()

    def test_422_raises_validation_error(self, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://flagdash.io/api/v1/manage/flags",
            status_code=422,
            json={"error": "Validation failed", "errors": {"key": ["is required"]}},
        )
        client = HttpClient(sdk_key="mgmt_key", base_url="https://flagdash.io")
        try:
            with pytest.raises(ValidationError) as exc_info:
                client.post("/manage/flags", json={})
            assert exc_info.value.errors == {"key": ["is required"]}
        finally:
            client.close()

    def test_429_raises_rate_limit(self, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://flagdash.io/api/v1/flags",
            status_code=429,
            json={"error": "Rate limit exceeded"},
            headers={"retry-after": "60"},
        )
        client = HttpClient(sdk_key="client_key", base_url="https://flagdash.io")
        try:
            with pytest.raises(RateLimitError) as exc_info:
                client.get("/flags")
            assert exc_info.value.retry_after == 60
        finally:
            client.close()

    def test_post_json(self, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://flagdash.io/api/v1/manage/flags",
            status_code=201,
            json={"flag": {"id": "flg_1", "key": "new"}},
        )
        client = HttpClient(sdk_key="mgmt_key", base_url="https://flagdash.io")
        try:
            data = client.post("/manage/flags", json={"key": "new", "name": "New"})
            assert data["flag"]["key"] == "new"
        finally:
            client.close()

    def test_delete_204(self, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://flagdash.io/api/v1/manage/flags/my-flag",
            status_code=204,
        )
        client = HttpClient(sdk_key="mgmt_key", base_url="https://flagdash.io")
        try:
            result = client.delete("/manage/flags/my-flag")
            assert result is None
        finally:
            client.close()


@pytest.fixture
def httpx_mock(monkeypatch):
    """Simple httpx mock fixture."""
    return HttpxMock(monkeypatch)


class HttpxMock:
    """Lightweight mock for httpx.Client and httpx.AsyncClient requests."""

    def __init__(self, monkeypatch) -> None:
        self._responses: list[dict] = []
        self._requests: list[httpx.Request] = []
        self._monkeypatch = monkeypatch
        self._patch()

    def add_response(
        self,
        url: str = "",
        status_code: int = 200,
        json: dict | None = None,
        headers: dict | None = None,
    ) -> None:
        self._responses.append({
            "url": url,
            "status_code": status_code,
            "json": json,
            "headers": headers or {},
        })

    def get_requests(self) -> list[httpx.Request]:
        return self._requests

    def _patch(self) -> None:
        mock = self

        original_init = httpx.Client.__init__

        def patched_init(client_self, **kwargs):
            original_init(client_self, **kwargs)
            client_self._mock = mock

        def patched_send(client_self, request, **kwargs):
            mock._requests.append(request)
            url = str(request.url)
            for resp_def in mock._responses:
                if resp_def["url"] in url:
                    import json as json_mod
                    content = (
                        json_mod.dumps(resp_def["json"]).encode()
                        if resp_def["json"] is not None
                        else b""
                    )
                    headers_list = [(k.lower(), v) for k, v in resp_def["headers"].items()]
                    if resp_def["json"] is not None:
                        headers_list.append(("content-type", "application/json"))
                    return httpx.Response(
                        status_code=resp_def["status_code"],
                        request=request,
                        content=content,
                        headers=headers_list,
                    )
            return httpx.Response(
                status_code=404, request=request, content=b'{"error":"not mocked"}'
            )

        self._monkeypatch.setattr(httpx.Client, "__init__", patched_init)
        self._monkeypatch.setattr(httpx.Client, "send", patched_send)
