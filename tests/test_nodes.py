from app.agent.nodes import calculate_metrics, summarize
from app.agent.state import TickerMetrics


def test_calculate_metrics_computes_return_and_volatility():
    # Hand-checkable price series: starts at 100, ends at 200 -> exactly 100% return.
    state = {"price_data": {"TEST": [100.0, 120.0, 90.0, 200.0]}}

    result = calculate_metrics(state)

    metrics = result["metrics"]["TEST"]
    assert metrics.total_return_pct == 100.0
    assert metrics.annualized_volatility_pct > 0  # prices moved, so volatility is nonzero


def test_summarize_includes_question_and_metrics():
    state = {
        "question": "How risky is this?",
        "metrics": {
            "TEST": TickerMetrics(total_return_pct=10.0, annualized_volatility_pct=20.0),
        },
    }

    result = summarize(state)

    assert "How risky is this?" in result["summary"]
    assert "TEST" in result["summary"]
    assert "10.0%" in result["summary"]
