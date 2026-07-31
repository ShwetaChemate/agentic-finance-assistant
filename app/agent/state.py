from typing import TypedDict

from pydantic import BaseModel


class TickerMetrics(BaseModel):
    """Computed metrics for a single ticker (produced by calculate_metrics)."""

    total_return_pct: float
    annualized_volatility_pct: float


class AgentState(TypedDict):
    """Shared state passed between LangGraph nodes: fetch_data -> calculate_metrics -> summarize."""

    tickers: list[str]  # input: e.g. ["AAPL", "VWCE.DE"]
    question: str  # input: the user's natural-language question
    price_data: dict[str, list[float]]  # set by fetch_data: ticker -> closing prices
    metrics: dict[str, TickerMetrics]  # set by calculate_metrics: ticker -> return/volatility
    summary: str  # set by summarize: final LLM-generated answer


# Example of a fully populated state (after all three nodes have run):
#
# example_state: AgentState = {
#     "tickers": ["AAPL", "VWCE.DE"],
#     "question": "How risky is this portfolio?",
#     "price_data": {
#         "AAPL": [189.50, 190.20, 187.30, 193.10],       # closing prices, oldest -> newest
#         "VWCE.DE": [102.40, 102.80, 101.90, 103.50],
#     },
#     "metrics": {
#         "AAPL": TickerMetrics(total_return_pct=1.9, annualized_volatility_pct=22.4),
#         "VWCE.DE": TickerMetrics(total_return_pct=1.07, annualized_volatility_pct=14.8),
#     },
#     "summary": "Your portfolio shows moderate risk: AAPL is significantly more "
#                "volatile (22.4% annualized) than VWCE.DE (14.8%)...",
# }
#
# At the start of a graph run, only "tickers" and "question" are populated;
# the rest fill in progressively as fetch_data -> calculate_metrics -> summarize run.
