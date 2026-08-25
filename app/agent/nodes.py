import math
import statistics

import yfinance as yf
from langchain_google_genai import ChatGoogleGenerativeAI

from app.agent.state import AgentStateV1, AgentStateV2, PortfolioSummary, TickerMetrics

# 252 is the global average number of trading days per year (accounting for weekends/holidays).
# It's the industry-standard approximation, used the same way across exchanges (NYSE, Xetra,
# LSE, ...) rather than computed per-market, so volatility stays comparable across tickers.
TRADING_DAYS_PER_YEAR = 252

# gemini-flash-lite-latest (not gemini-flash-latest): the full flash alias was observed
# repeatedly timing out on structured-output/function-calling requests specifically, while
# the lite variant returned correct results reliably. Used by both v1 and v2 — this is a
# reliability fix, not a versioned behavior difference.
GEMINI_MODEL = "gemini-flash-lite-latest"

# Response latency for this model varies widely in practice (observed 0.7s-23s across
# otherwise-identical calls with the same prompt) — 20s was too tight and occasionally cut
# off responses that would have succeeded. 30s comfortably covers the observed range while
# still failing within a reasonable time if something is genuinely wrong (worst case with
# retries: ~= GEMINI_TIMEOUT_SECONDS * (GEMINI_MAX_RETRIES + 1) = 60s).
GEMINI_TIMEOUT_SECONDS = 30
GEMINI_MAX_RETRIES = 1


def fetch_data(state: AgentStateV1 | AgentStateV2) -> dict:
    """Pull 5 years of daily closing prices for each ticker (shared window for return + volatility).

    Identical for v1 and v2 — only reads `tickers`, which has the same shape in both state
    versions, so one implementation serves both graphs.
    """
    price_data: dict[str, list[float]] = {}

    for ticker in state["tickers"]:
        history = yf.Ticker(ticker).history(period="5y")
        price_data[ticker] = history["Close"].tolist()

    return {"price_data": price_data}


def calculate_metrics(state: AgentStateV1 | AgentStateV2) -> dict:
    """Compute simple total return and annualized volatility for each ticker.

    Identical for v1 and v2 — same reasoning as fetch_data above.
    """
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


def summarize_v1(state: AgentStateV1) -> dict:
    """v1: turn computed metrics into a free-text answer to the user's question via Gemini.

    Kept as-is (not modified when v2 was built) so the original behavior stays demoable
    and comparable against v2's structured-output version.
    """
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
    # no need to pass it explicitly, as long as it's set (via .env + load_dotenv()). timeout/
    # max_retries are set so a slow/stalled response fails fast instead of hanging indefinitely
    # (this was a real bug found while building v2 — see summarize_v2 — fixed here too since
    # it's a reliability issue, not part of what v1 vs v2 is meant to demonstrate).
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL, timeout=GEMINI_TIMEOUT_SECONDS, max_retries=GEMINI_MAX_RETRIES
    )
    content = llm.invoke(prompt).content

    # This model can return a list of content blocks (text + reasoning metadata) rather than
    # a plain string, so pull out just the "text" blocks and join them.
    if isinstance(content, list):
        summary = "".join(block["text"] for block in content if block.get("type") == "text")
    else:
        summary = content

    return {"summary": summary}


def summarize_v2(state: AgentStateV2) -> dict:
    """v2: turn computed metrics into a structured explanation of the user's question via Gemini."""
    metrics_text = "\n".join(
        f"- {ticker}: {m.total_return_pct:+.1f}% total return, "
        f"{m.annualized_volatility_pct:.1f}% annualized volatility (5yr)"
        for ticker, m in state["metrics"].items()
    )

    prompt = (
        f'A retail investor asked: "{state["question"]}"\n\n'
        f"Portfolio metrics:\n{metrics_text}\n\n"
        "Assess this portfolio for a retail investor with no finance background."
    )

    # timeout/max_retries: without them, a slow or stalled Gemini response can hang the
    # request indefinitely instead of failing fast with a clear error.
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL, timeout=GEMINI_TIMEOUT_SECONDS, max_retries=GEMINI_MAX_RETRIES
    )

    # with_structured_output sends the PortfolioSummary schema — including every field's
    # description — to Gemini as a function-calling constraint. The response comes back
    # already validated and parsed into a PortfolioSummary instance, so there's no manual
    # JSON parsing or content-block extraction to do (unlike summarize_v1 above).
    structured_llm = llm.with_structured_output(PortfolioSummary)
    summary = structured_llm.invoke(prompt)

    return {"summary": summary}
