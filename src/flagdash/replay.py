"""Privacy-safe chronological event replay for trusted Python backends."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from time import monotonic
from typing import Any

import httpx

_SENSITIVE = re.compile(
    r"pass(word)?|secret|token|authorization|cookie|session|api[-_]?key|credit|card|cvv|cvc|otp|ssn",
    re.IGNORECASE,
)


class FlagDashBackendReplay:
    """Collect actions, breadcrumbs, errors, and decisions as an ordered timeline."""

    def __init__(
        self,
        sdk_key: str,
        *,
        base_url: str = "https://flagdash.io",
        identity: str | None = None,
        release: str | None = None,
        metadata: dict[str, Any] | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._key = sdk_key
        self._base_url = base_url.rstrip("/")
        self._identity = identity
        self._release = release
        self._metadata = metadata or {}
        self._client = httpx.Client(timeout=timeout)
        self._id: str | None = None
        self._sequence = 0
        self._started_at = datetime.now(timezone.utc)
        self._started_clock = monotonic()
        self._events: list[dict[str, Any]] = []

    def start(self) -> bool:
        response = self._api(
            "/api/v1/replay-sessions/start",
            {
                "type": "trace",
                "platform": "python",
                "sdk_name": "flagdash-python",
                "sdk_version": "0.1.0",
                "started_at": self._started_at.isoformat(),
                "identity": self._identity,
                "release": self._release,
                "metadata": _sanitize(self._metadata),
            },
        )
        if not response.is_success or response.status_code == 204:
            return False
        self._id = str(response.json()["id"])
        return True

    def event(
        self,
        name: str,
        *,
        category: str = "action",
        attributes: dict[str, Any] | None = None,
    ) -> None:
        if not self._id or not name or len(self._events) >= 1_000:
            return
        self._events.append(
            {
                "name": name[:100],
                "category": category[:40],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "attributes": _sanitize(attributes or {}),
            }
        )

    def breadcrumb(self, message: str, attributes: dict[str, Any] | None = None) -> None:
        self.event(message, category="breadcrumb", attributes=attributes)

    def capture_exception(
        self, error: BaseException, attributes: dict[str, Any] | None = None
    ) -> None:
        self.event(type(error).__name__, category="exception", attributes=attributes)

    def context_headers(self) -> dict[str, str]:
        return {"x-flagdash-replay-id": self._id} if self._id else {}

    def flush(self) -> None:
        while self._id and self._events:
            events, self._events = self._events[:100], self._events[100:]
            raw = json.dumps(events).encode()
            response = self._api(
                f"/api/v1/replay-sessions/{self._id}/chunks/presign",
                {
                    "sequence": self._sequence,
                    "byte_size": len(raw),
                    "event_count": len(events),
                    "content_encoding": "identity",
                },
            )
            self._sequence += 1
            if not response.is_success:
                return
            upload = response.json()["upload"]
            uploaded = self._client.put(upload["url"], headers=upload["headers"], content=raw)
            uploaded.raise_for_status()

    def stop(self) -> None:
        self.flush()
        if self._id:
            self._api(
                f"/api/v1/replay-sessions/{self._id}/complete",
                {
                    "ended_at": datetime.now(timezone.utc).isoformat(),
                    "duration_ms": int((monotonic() - self._started_clock) * 1_000),
                },
            )
        self._client.close()

    def _api(self, path: str, body: dict[str, Any]) -> httpx.Response:
        return self._client.post(
            self._base_url + path,
            headers={"Authorization": f"Bearer {self._key}"},
            json=body,
        )


def _sanitize(value: Any, depth: int = 0) -> Any:
    if depth > 8:
        return "[REDACTED]"
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if _SENSITIVE.search(str(key)) else _sanitize(item, depth + 1)
            for key, item in list(value.items())[:500]
        }
    if isinstance(value, (list, tuple)):
        return [_sanitize(item, depth + 1) for item in value[:500]]
    if isinstance(value, str):
        return value[:2_000]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return "[REDACTED]"
