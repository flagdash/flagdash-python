"""Tests for type definitions."""

from flagdash.types import AiConfig, ConfigValue, EvaluationContext, FlagDetailResult, FlagValue


class TestEvaluationContext:
    def test_empty_context(self) -> None:
        ctx = EvaluationContext()
        assert ctx.to_query_params() == {}

    def test_user_id_only(self) -> None:
        ctx = EvaluationContext(user_id="alice")
        assert ctx.to_query_params() == {"user_id": "alice"}

    def test_with_attributes(self) -> None:
        ctx = EvaluationContext(
            user_id="alice",
            attributes={"country": "US", "plan": "pro"},
        )
        params = ctx.to_query_params()
        assert params["user_id"] == "alice"
        assert params["country"] == "US"
        assert params["plan"] == "pro"


class TestFlagValue:
    def test_basic(self) -> None:
        fv = FlagValue(key="my-flag", value=True)
        assert fv.key == "my-flag"
        assert fv.value is True
        assert fv.variation_key is None


class TestFlagDetailResult:
    def test_basic(self) -> None:
        fdr = FlagDetailResult(key="my-flag", value=True, reason="rollout")
        assert fdr.key == "my-flag"
        assert fdr.value is True
        assert fdr.reason == "rollout"
        assert fdr.variation_key is None

    def test_with_variation_key(self) -> None:
        fdr = FlagDetailResult(key="ab-test", value="blue", reason="variation", variation_key="b")
        assert fdr.key == "ab-test"
        assert fdr.value == "blue"
        assert fdr.reason == "variation"
        assert fdr.variation_key == "b"

    def test_disabled_reason(self) -> None:
        fdr = FlagDetailResult(key="off-flag", value=False, reason="disabled")
        assert fdr.reason == "disabled"

    def test_rule_match_reason(self) -> None:
        fdr = FlagDetailResult(key="targeted", value=True, reason="rule_match")
        assert fdr.reason == "rule_match"

    def test_default_reason(self) -> None:
        fdr = FlagDetailResult(key="fallback", value=None, reason="default")
        assert fdr.reason == "default"


class TestConfigValue:
    def test_basic(self) -> None:
        cv = ConfigValue(key="api-url", value="https://example.com")
        assert cv.key == "api-url"
        assert cv.value == "https://example.com"


class TestAiConfig:
    def test_basic(self) -> None:
        ac = AiConfig(
            file_name="agent.md",
            file_type="agent",
            content="# Agent",
            folder="agents",
        )
        assert ac.file_name == "agent.md"
        assert ac.folder == "agents"
