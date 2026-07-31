import pandas as pd
from fastapi.testclient import TestClient

import app.agent.nodes as nodes
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


def test_analyze_portfolio_endpoint(monkeypatch):
    monkeypatch.setattr(nodes.yf, "Ticker", FakeTicker)
    client = TestClient(app)

    response = client.post(
        "/analyze-portfolio",
        json={"tickers": ["AAPL", "VWCE.DE"], "question": "How risky is this portfolio?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body["metrics"].keys()) == {"AAPL", "VWCE.DE"}
    assert "How risky is this portfolio?" in body["summary"]


def test_analyze_portfolio_rejects_empty_tickers():
    client = TestClient(app)

    response = client.post("/analyze-portfolio", json={"tickers": [], "question": "test"})

    assert response.status_code == 422
