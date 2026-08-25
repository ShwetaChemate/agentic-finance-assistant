from app.agent import nodes
from app.agent.nodes import calculate_metrics, summarize_v1, summarize_v2
from app.agent.state import PortfolioSummary, TickerMetrics


class FakeMessage:
    """Stands in for the AIMessage returned by llm.invoke(...) on summarize_v1's plain-text path."""

    def __init__(self, content):
        self.content = content


class FakeLLMV1:
    """Stands in for ChatGoogleGenerativeAI in summarize_v1 (plain .invoke(prompt).content)."""

    def __init__(self, *args, **kwargs):
        pass

    def invoke(self, prompt):
        # Stored on the class (not self) since the test never gets a handle on the
        # instance summarize_v1() creates internally.
        FakeLLMV1.last_prompt = prompt
        return FakeMessage(content="fake v1 summary text")


class FakeLLMV2:
    """Stands in for ChatGoogleGenerativeAI in summarize_v2 (with_structured_output path)."""

    def __init__(self, *args, **kwargs):
        pass

    def with_structured_output(self, schema):
        FakeLLMV2.last_schema = schema
        return self

    def invoke(self, prompt):
        FakeLLMV2.last_prompt = prompt
        return PortfolioSummary(
            risk_rating="moderate",
            key_drivers=["fake driver"],
            confidence="high",
            explanation="fake explanation",
        )


def test_calculate_metrics_computes_return_and_volatility():
    # Hand-checkable price series: starts at 100, ends at 200 -> exactly 100% return.
    # Shared by v1 and v2 (calculate_metrics has no version-specific behavior).
    state = {"price_data": {"TEST": [100.0, 120.0, 90.0, 200.0]}}

    result = calculate_metrics(state)

    metrics = result["metrics"]["TEST"]
    assert metrics.total_return_pct == 100.0
    assert metrics.annualized_volatility_pct > 0  # prices moved, so volatility is nonzero


def test_summarize_v1_builds_prompt_and_returns_free_text(monkeypatch):
    monkeypatch.setattr(nodes, "ChatGoogleGenerativeAI", FakeLLMV1)
    state = {
        "question": "How risky is this?",
        "metrics": {
            "TEST": TickerMetrics(total_return_pct=10.0, annualized_volatility_pct=20.0),
        },
    }

    result = summarize_v1(state)

    assert "How risky is this?" in FakeLLMV1.last_prompt
    assert "TEST" in FakeLLMV1.last_prompt
    assert "10.0%" in FakeLLMV1.last_prompt
    assert result["summary"] == "fake v1 summary text"


def test_summarize_v2_builds_prompt_and_returns_structured_output(monkeypatch):
    monkeypatch.setattr(nodes, "ChatGoogleGenerativeAI", FakeLLMV2)
    state = {
        "question": "How risky is this?",
        "metrics": {
            "TEST": TickerMetrics(total_return_pct=10.0, annualized_volatility_pct=20.0),
        },
    }

    result = summarize_v2(state)

    # Our code's job is to build a prompt containing the question + metrics, request
    # PortfolioSummary as the structured output schema, and return whatever the LLM
    # produces — not to control the LLM's wording.
    assert "How risky is this?" in FakeLLMV2.last_prompt
    assert "TEST" in FakeLLMV2.last_prompt
    assert "10.0%" in FakeLLMV2.last_prompt
    assert FakeLLMV2.last_schema is PortfolioSummary
    assert result["summary"].risk_rating == "moderate"
    assert result["summary"].explanation == "fake explanation"
