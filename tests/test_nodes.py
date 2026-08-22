from app.agent import nodes
from app.agent.nodes import calculate_metrics, summarize
from app.agent.state import TickerMetrics


class FakeMessage:
    """Stands in for the AIMessage returned by llm.invoke(...)."""

    def __init__(self, content):
        self.content = content


class FakeLLM:
    """Stands in for ChatGoogleGenerativeAI so tests don't call the real Gemini API —
    keeps tests fast, free, deterministic, and focused on our code, not the model's wording."""

    def __init__(self, *args, **kwargs):
        pass

    def invoke(self, prompt):
        # Stored on the class (not self) since the test never gets a handle on the
        # instance summarize() creates internally.
        FakeLLM.last_prompt = prompt
        return FakeMessage(content="fake summary text")


def test_calculate_metrics_computes_return_and_volatility():
    # Hand-checkable price series: starts at 100, ends at 200 -> exactly 100% return.
    state = {"price_data": {"TEST": [100.0, 120.0, 90.0, 200.0]}}

    result = calculate_metrics(state)

    metrics = result["metrics"]["TEST"]
    assert metrics.total_return_pct == 100.0
    assert metrics.annualized_volatility_pct > 0  # prices moved, so volatility is nonzero


def test_summarize_builds_prompt_and_extracts_plain_text(monkeypatch):
    monkeypatch.setattr(nodes, "ChatGoogleGenerativeAI", FakeLLM)
    state = {
        "question": "How risky is this?",
        "metrics": {
            "TEST": TickerMetrics(total_return_pct=10.0, annualized_volatility_pct=20.0),
        },
    }

    result = summarize(state)

    # Our code's job is to build a prompt containing the question + metrics, and to
    # return whatever the LLM says — not to control the LLM's wording.
    assert "How risky is this?" in FakeLLM.last_prompt
    assert "TEST" in FakeLLM.last_prompt
    assert "10.0%" in FakeLLM.last_prompt
    assert result["summary"] == "fake summary text"


def test_summarize_extracts_text_from_structured_content(monkeypatch):
    # Some Gemini models return a list of content blocks (text + reasoning metadata)
    # instead of a plain string — verify we pull out just the text blocks correctly.
    class StructuredContentLLM(FakeLLM):
        def invoke(self, prompt):
            return FakeMessage(
                content=[
                    {"type": "text", "text": "Part one. "},
                    {"type": "text", "text": "Part two."},
                    {"type": "reasoning", "signature": "ignored-non-text-block"},
                ]
            )

    monkeypatch.setattr(nodes, "ChatGoogleGenerativeAI", StructuredContentLLM)
    state = {"question": "test", "metrics": {}}

    result = summarize(state)

    assert result["summary"] == "Part one. Part two."
