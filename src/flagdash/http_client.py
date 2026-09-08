"""HTTP client wrapper for FlagDash API with auth, error handling, and JSON."""

from __future__ import annotations

from typing import Any

import httpx

from flagdash.exceptions import (
    AuthenticationError,
    FlagDashError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)

DEFAULT_TIMEOUT = 5.0
DEFAULT_BASE_URL = "https://flagdash.io"


class HttpClient:
    """Synchronous HTTP client for the FlagDash API."""

    def __init__(
        self,
        sdk_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {sdk_key}",
                "Content-Type": "application/json",
                "User-Agent": "flagdash-python/0.1.0",
            },
            timeout=timeout,
        )

    def get(self, path: str, params: dict[str, str] | None = None) -> Any:
        """Send a GET request and return the parsed JSON body."""
        try:
            response = self._client.get(f"/api/v1{path}", params=params)
        except httpx.TimeoutException as exc:
            raise TimeoutError() from exc
        except httpx.HTTPError as exc:
            raise FlagDashError(f"HTTP error: {exc}") from exc

        return self._handle_response(response)

    def post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Send a POST request and return the parsed JSON body."""
        try:
            response = self._client.post(f"/api/v1{path}", json=json)
        except httpx.TimeoutException as exc:
            raise TimeoutError() from exc
        except httpx.HTTPError as exc:
            raise FlagDashError(f"HTTP error: {exc}") from exc

        return self._handle_response(response)

    def put(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Send a PUT request and return the parsed JSON body."""
        try:
            response = self._client.put(f"/api/v1{path}", json=json)
        except httpx.TimeoutException as exc:
            raise TimeoutError() from exc
        except httpx.HTTPError as exc:
            raise FlagDashError(f"HTTP error: {exc}") from exc

        return self._handle_response(response)

    def delete(self, path: str, params: dict[str, str] | None = None) -> Any:
        """Send a DELETE request. Returns None for 204 responses."""
        try:
            response = self._client.delete(f"/api/v1{path}", params=params)
        except httpx.TimeoutException as exc:
            raise TimeoutError() from exc
        except httpx.HTTPError as exc:
            raise FlagDashError(f"HTTP error: {exc}") from exc

        if response.status_code == 204:
            return None

        return self._handle_response(response)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def _handle_response(self, response: httpx.Response) -> Any:
        if response.is_success:
            if response.status_code == 204:
                return None
            return response.json()

        body = {}
        try:
            body = response.json()
        except Exception:
            pass

        message = body.get("error", response.reason_phrase or "Unknown error")

        if response.status_code == 401:
            raise AuthenticationError(message)
        elif response.status_code == 403:
            raise ForbiddenError(message)
        elif response.status_code == 404:
            raise NotFoundError(message)
        elif response.status_code == 422:
            raise ValidationError(message, errors=body.get("errors"))
        elif response.status_code == 429:
            retry_after = response.headers.get("retry-after")
            raise RateLimitError(
                message,
                retry_after=int(retry_after) if retry_after else None,
            )
        else:
            raise FlagDashError(message, status_code=response.status_code)


class AsyncHttpClient:
    """Asynchronous HTTP client for the FlagDash API."""

    def __init__(
        self,
        sdk_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {sdk_key}",
                "Content-Type": "application/json",
                "User-Agent": "flagdash-python/0.1.0",
            },
            timeout=timeout,
        )

    async def get(self, path: str, params: dict[str, str] | None = None) -> Any:
        try:
            response = await self._client.get(f"/api/v1{path}", params=params)
        except httpx.TimeoutException as exc:
            raise TimeoutError() from exc
        except httpx.HTTPError as exc:
            raise FlagDashError(f"HTTP error: {exc}") from exc

        return self._handle_response(response)

    async def post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        try:
            response = await self._client.post(f"/api/v1{path}", json=json)
        except httpx.TimeoutException as exc:
            raise TimeoutError() from exc
        except httpx.HTTPError as exc:
            raise FlagDashError(f"HTTP error: {exc}") from exc

        return self._handle_response(response)

    async def put(self, path: str, json: dict[str, Any] | None = None) -> Any:
        try:
            response = await self._client.put(f"/api/v1{path}", json=json)
        except httpx.TimeoutException as exc:
            raise TimeoutError() from exc
        except httpx.HTTPError as exc:
            raise FlagDashError(f"HTTP error: {exc}") from exc

        return self._handle_response(response)

    async def delete(self, path: str, params: dict[str, str] | None = None) -> Any:
        try:
            response = await self._client.delete(f"/api/v1{path}", params=params)
        except httpx.TimeoutException as exc:
            raise TimeoutError() from exc
        except httpx.HTTPError as exc:
            raise FlagDashError(f"HTTP error: {exc}") from exc

        if response.status_code == 204:
            return None

        return self._handle_response(response)

    async def close(self) -> None:
        await self._client.aclose()

    def _handle_response(self, response: httpx.Response) -> Any:
        if response.is_success:
            if response.status_code == 204:
                return None
            return response.json()

        body = {}
        try:
            body = response.json()
        except Exception:
            pass

        message = body.get("error", response.reason_phrase or "Unknown error")

        if response.status_code == 401:
            raise AuthenticationError(message)
        elif response.status_code == 403:
            raise ForbiddenError(message)
        elif response.status_code == 404:
            raise NotFoundError(message)
        elif response.status_code == 422:
            raise ValidationError(message, errors=body.get("errors"))
        elif response.status_code == 429:
            retry_after = response.headers.get("retry-after")
            raise RateLimitError(
                message,
                retry_after=int(retry_after) if retry_after else None,
            )
        else:
            raise FlagDashError(message, status_code=response.status_code)
