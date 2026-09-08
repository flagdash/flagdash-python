from __future__ import annotations

import json
from typing import Any

import httpx

from flagdash import FlagDashBackendReplay


def test_backend_replay_uploads_sanitized_timeline(monkeypatch: Any) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/start"):
            return httpx.Response(201, json={"id": "rpl_python"})
        if request.url.path.endswith("/presign"):
            return httpx.Response(
                200, json={"upload": {"url": "https://storage.test/chunk", "headers": {}}}
            )
        return httpx.Response(200)

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: real_client(transport=transport))

    replay = FlagDashBackendReplay("sk_test", base_url="https://api.test")
    assert replay.start()
    replay.event("checkout_started", attributes={"password": "hidden", "cart_size": 2})
    replay.breadcrumb("payment requested", {"token": "hidden"})
    assert replay.context_headers() == {"x-flagdash-replay-id": "rpl_python"}
    replay.stop()

    uploaded = next(request.content for request in requests if request.url.host == "storage.test")
    assert b"checkout_started" in uploaded
    assert b"payment requested" in uploaded
    assert b"hidden" not in uploaded
    assert json.loads(uploaded)[0]["attributes"]["password"] == "[REDACTED]"
