import pandas as pd
from fastapi.testclient import TestClient

from app.agent import nodes
from app.agent.state import PortfolioSummary
from app.main import app

FAKE_PRICES = {
    "AAPL": [100.0, 110.0, 105.0, 120.0],
    "VWCE.DE": [50.0, 51.0, 49.0, 52.0],
}


class FakeTicker:
    """Stands in for yf.Ticker so tests don't depend on live market data or network access."""

    def __init__(self, symbol):
        self.symbol = symbol

    def history(self, period):
        return pd.DataFrame({"Close": FAKE_PRICES[self.symbol]})


class FakeMessage:
    """Stands in for the AIMessage returned by llm.invoke(...) on the v1 (free-text) path."""

    def __init__(self, content):
        self.content = content


class FakeLLMV1:
    """Stands in for ChatGoogleGenerativeAI on the v1 endpoint's plain-text path."""

    def __init__(self, *args, **kwargs):
        pass

    def invoke(self, prompt):
        return FakeMessage(content="fake v1 summary text")


class FakeLLMV2:
    """Stands in for ChatGoogleGenerativeAI on the v2 endpoint's structured-output path."""

    def __init__(self, *args, **kwargs):
        pass

    def with_structured_output(self, schema):
        return self

    def invoke(self, prompt):
        return PortfolioSummary(
            risk_rating="moderate",
            key_drivers=["fake driver"],
            confidence="high",
            explanation="fake v2 summary text",
        )


def test_analyze_portfolio_v1_endpoint(monkeypatch):
    monkeypatch.setattr(nodes.yf, "Ticker", FakeTicker)
    monkeypatch.setattr(nodes, "ChatGoogleGenerativeAI", FakeLLMV1)
    client = TestClient(app)

    response = client.post(
        "/v1/analyze-portfolio",
        json={"tickers": ["AAPL", "VWCE.DE"], "question": "How risky is this portfolio?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body["metrics"].keys()) == {"AAPL", "VWCE.DE"}
    assert body["summary"] == "fake v1 summary text"


def test_analyze_portfolio_v1_rejects_empty_tickers():
    client = TestClient(app)

    response = client.post("/v1/analyze-portfolio", json={"tickers": [], "question": "test"})

    assert response.status_code == 422


def test_analyze_portfolio_v2_endpoint(monkeypatch):
    monkeypatch.setattr(nodes.yf, "Ticker", FakeTicker)
    monkeypatch.setattr(nodes, "ChatGoogleGenerativeAI", FakeLLMV2)
    client = TestClient(app)

    response = client.post(
        "/v2/analyze-portfolio",
        json={"tickers": ["AAPL", "VWCE.DE"], "question": "How risky is this portfolio?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body["metrics"].keys()) == {"AAPL", "VWCE.DE"}
    assert body["summary"]["risk_rating"] == "moderate"
    assert body["summary"]["explanation"] == "fake v2 summary text"


def test_analyze_portfolio_v2_rejects_empty_tickers():
    client = TestClient(app)

    response = client.post("/v2/analyze-portfolio", json={"tickers": [], "question": "test"})

    assert response.status_code == 422
