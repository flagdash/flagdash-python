"""Tests for deployment-region detection and injection."""

from __future__ import annotations

import pytest

from flagdash.client import FlagDashClient
from flagdash.region import detect_region, merge_region_params, resolve_region
from flagdash.types import EvaluationContext


@pytest.fixture(autouse=True)
def _clear_region_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in (
        "FLAGDASH_REGION",
        "FLY_REGION",
        "AWS_REGION",
        "AWS_DEFAULT_REGION",
        "GOOGLE_CLOUD_REGION",
        "RAILWAY_REPLICA_REGION",
        "RENDER_REGION",
    ):
        monkeypatch.delenv(var, raising=False)


class TestDetectRegion:
    def test_returns_none_when_nothing_is_set(self) -> None:
        assert detect_region() is None

    def test_reads_platform_variables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FLY_REGION", "gru")
        assert detect_region() == "gru"

    def test_flagdash_region_wins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FLY_REGION", "gru")
        monkeypatch.setenv("FLAGDASH_REGION", "override")
        assert detect_region() == "override"

    def test_ignores_empty_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FLAGDASH_REGION", "")
        monkeypatch.setenv("AWS_REGION", "us-east-1")
        assert detect_region() == "us-east-1"


class TestResolveRegion:
    def test_explicit_region_wins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FLY_REGION", "gru")
        assert resolve_region("explicit", True) == "explicit"

    def test_detection_can_be_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FLY_REGION", "gru")
        assert resolve_region(None, False) is None

    def test_falls_back_to_detection(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FLY_REGION", "gru")
        assert resolve_region(None, True) == "gru"


class TestMergeRegionParams:
    def test_no_region_and_no_context_is_none(self) -> None:
        assert merge_region_params(None, None) is None

    def test_region_alone_becomes_a_param(self) -> None:
        assert merge_region_params("eu-west-1", None) == {"region": "eu-west-1"}

    def test_region_merges_with_context(self) -> None:
        context = EvaluationContext(user_id="alice")
        assert merge_region_params("eu-west-1", context) == {
            "region": "eu-west-1",
            "user_id": "alice",
        }

    def test_context_region_wins(self) -> None:
        context = EvaluationContext(user_id="alice", attributes={"region": "us-east-1"})
        assert merge_region_params("eu-west-1", context)["region"] == "us-east-1"

    def test_context_without_region_is_untouched(self) -> None:
        context = EvaluationContext(user_id="alice")
        assert merge_region_params(None, context) == {"user_id": "alice"}


class TestClientRegion:
    def test_client_auto_detects(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FLY_REGION", "gru")
        client = FlagDashClient(sdk_key="sk_test")
        assert client._region == "gru"

    def test_client_accepts_an_explicit_region(self) -> None:
        client = FlagDashClient(sdk_key="sk_test", region="eu-west-1")
        assert client._region == "eu-west-1"

    def test_detection_can_be_turned_off(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FLY_REGION", "gru")
        client = FlagDashClient(sdk_key="sk_test", auto_detect_region=False)
        assert client._region is None
