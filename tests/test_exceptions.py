"""Tests for exception types."""

from flagdash.exceptions import (
    AuthenticationError,
    FlagDashError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)


class TestExceptions:
    def test_base_error(self) -> None:
        err = FlagDashError("something broke", status_code=500)
        assert str(err) == "something broke"
        assert err.status_code == 500

    def test_authentication_error(self) -> None:
        err = AuthenticationError()
        assert err.status_code == 401
        assert "API key" in str(err)

    def test_forbidden_error(self) -> None:
        err = ForbiddenError("Nope")
        assert err.status_code == 403

    def test_not_found_error(self) -> None:
        err = NotFoundError()
        assert err.status_code == 404

    def test_validation_error(self) -> None:
        err = ValidationError("Bad input", errors={"key": ["required"]})
        assert err.status_code == 422
        assert err.errors == {"key": ["required"]}

    def test_rate_limit_error(self) -> None:
        err = RateLimitError(retry_after=30)
        assert err.status_code == 429
        assert err.retry_after == 30

    def test_timeout_error(self) -> None:
        err = TimeoutError()
        assert err.status_code is None

    def test_inheritance(self) -> None:
        assert issubclass(AuthenticationError, FlagDashError)
        assert issubclass(ForbiddenError, FlagDashError)
        assert issubclass(NotFoundError, FlagDashError)
        assert issubclass(ValidationError, FlagDashError)
        assert issubclass(RateLimitError, FlagDashError)
        assert issubclass(TimeoutError, FlagDashError)
