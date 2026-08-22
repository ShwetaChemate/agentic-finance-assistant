import pandas as pd
from fastapi.testclient import TestClient

from app.agent import nodes
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
    def __init__(self, content):
        self.content = content


class FakeLLM:
    """Stands in for ChatGoogleGenerativeAI so tests don't call the real Gemini API."""

    def __init__(self, *args, **kwargs):
        pass

    def invoke(self, prompt):
        return FakeMessage(content="fake summary text")


def test_analyze_portfolio_endpoint(monkeypatch):
    monkeypatch.setattr(nodes.yf, "Ticker", FakeTicker)
    monkeypatch.setattr(nodes, "ChatGoogleGenerativeAI", FakeLLM)
    client = TestClient(app)

    response = client.post(
        "/analyze-portfolio",
        json={"tickers": ["AAPL", "VWCE.DE"], "question": "How risky is this portfolio?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body["metrics"].keys()) == {"AAPL", "VWCE.DE"}
    assert body["summary"] == "fake summary text"


def test_analyze_portfolio_rejects_empty_tickers():
    client = TestClient(app)

    response = client.post("/analyze-portfolio", json={"tickers": [], "question": "test"})

    assert response.status_code == 422
