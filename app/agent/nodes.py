import math
import statistics

import yfinance as yf
from langchain_google_genai import ChatGoogleGenerativeAI

from app.agent.state import AgentState, TickerMetrics

# 252 is the global average number of trading days per year (accounting for weekends/holidays).
# It's the industry-standard approximation, used the same way across exchanges (NYSE, Xetra,
# LSE, ...) rather than computed per-market, so volatility stays comparable across tickers.
TRADING_DAYS_PER_YEAR = 252


def fetch_data(state: AgentState) -> dict:
    """Pull 5 years of daily closing prices for each ticker (shared window for return + volatility)."""
    price_data: dict[str, list[float]] = {}

    for ticker in state["tickers"]:
        history = yf.Ticker(ticker).history(period="5y")
        price_data[ticker] = history["Close"].tolist()

    return {"price_data": price_data}


def calculate_metrics(state: AgentState) -> dict:
    """Compute simple total return and annualized volatility for each ticker."""
    metrics: dict[str, TickerMetrics] = {}

    for ticker, prices in state["price_data"].items():
        # Simple return: how much the price moved from the first to the last day in the window.
        total_return_pct = (prices[-1] - prices[0]) / prices[0] * 100

        # Day-over-day % changes. Needed because volatility measures how much the price
        # swings around day to day, not just where it ended up (that's what total_return covers).
        daily_returns = [
            (prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))
        ]

        # Standard deviation of daily returns, scaled up ("annualized") by sqrt(trading days/year).
        # sqrt(252) rather than 252 because variance scales linearly with time, but standard
        # deviation is the square root of variance — this is the standard convention for
        # comparing volatility figures across tickers/timeframes.
        annualized_volatility_pct = (
            statistics.stdev(daily_returns) * math.sqrt(TRADING_DAYS_PER_YEAR) * 100
        )

        metrics[ticker] = TickerMetrics(
            total_return_pct=round(total_return_pct, 2),
            annualized_volatility_pct=round(annualized_volatility_pct, 2),
        )

    return {"metrics": metrics}


def summarize(state: AgentState) -> dict:
    """Turn computed metrics into a plain-language answer to the user's question via Gemini."""
    metrics_text = "\n".join(
        f"- {ticker}: {m.total_return_pct:+.1f}% total return, "
        f"{m.annualized_volatility_pct:.1f}% annualized volatility (5yr)"
        for ticker, m in state["metrics"].items()
    )

    prompt = (
        f'A retail investor asked: "{state["question"]}"\n\n'
        f"Portfolio metrics:\n{metrics_text}\n\n"
        "Explain this in plain, non-technical language, directly answering their question. "
        "Keep it to a short paragraph."
    )

    # ChatGoogleGenerativeAI reads the GOOGLE_API_KEY environment variable automatically —
    # no need to pass it explicitly, as long as it's set (via .env + load_dotenv()).
    llm = ChatGoogleGenerativeAI(model="gemini-flash-latest")
    content = llm.invoke(prompt).content

    # This model returns a list of content blocks (text + reasoning metadata) rather than
    # a plain string, so pull out just the "text" blocks and join them.
    if isinstance(content, list):
        summary = "".join(block["text"] for block in content if block.get("type") == "text")
    else:
        summary = content

    return {"summary": summary}
