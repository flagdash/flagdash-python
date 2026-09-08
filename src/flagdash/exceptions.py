"""FlagDash exception hierarchy."""

from __future__ import annotations


class FlagDashError(Exception):
    """Base exception for all FlagDash errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class AuthenticationError(FlagDashError):
    """Raised when the API key is invalid or missing (401)."""

    def __init__(self, message: str = "Invalid or missing API key") -> None:
        super().__init__(message, status_code=401)


class ForbiddenError(FlagDashError):
    """Raised when the API key lacks permissions for the endpoint (403)."""

    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message, status_code=403)


class NotFoundError(FlagDashError):
    """Raised when the requested resource does not exist (404)."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status_code=404)


class ValidationError(FlagDashError):
    """Raised when the request body fails validation (422)."""

    def __init__(self, message: str = "Validation failed", errors: dict | None = None) -> None:
        super().__init__(message, status_code=422)
        self.errors = errors or {}


class RateLimitError(FlagDashError):
    """Raised when the rate limit is exceeded (429)."""

    def __init__(
        self, message: str = "Rate limit exceeded", retry_after: int | None = None
    ) -> None:
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class TimeoutError(FlagDashError):
    """Raised when a request times out."""

    def __init__(self, message: str = "Request timed out") -> None:
        super().__init__(message)
