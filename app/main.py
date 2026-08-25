from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.agent.graph import build_agent_v1, build_agent_v2
from app.agent.state import PortfolioSummary, TickerMetrics

# Load GOOGLE_API_KEY (and any other vars) from .env into the process environment.
# Must happen before build_agent_v1()/build_agent_v2() run, since ChatGoogleGenerativeAI
# reads GOOGLE_API_KEY straight from os.environ.
load_dotenv()

app = FastAPI(title="Agentic Finance Assistant API")

# Compile both graphs once at import time, not per-request. Both versions stay live
# simultaneously — v2 doesn't replace v1, it's a separate endpoint hitting separate code.
agent_v1 = build_agent_v1()
agent_v2 = build_agent_v2()


class PortfolioRequest(BaseModel):
    """Same request shape for both versions — only the response differs."""

    tickers: list[str] = Field(
        ..., min_length=1, description="Ticker symbols, e.g. ['AAPL', 'VWCE.DE']"
    )
    question: str = Field(..., min_length=1, description="Natural-language question about the portfolio")


class PortfolioResponseV1(BaseModel):
    metrics: dict[str, TickerMetrics]
    summary: str


class PortfolioResponseV2(BaseModel):
    metrics: dict[str, TickerMetrics]
    summary: PortfolioSummary


@app.post("/v1/analyze-portfolio", response_model=PortfolioResponseV1)
def analyze_portfolio_v1(request: PortfolioRequest) -> PortfolioResponseV1:
    result = agent_v1.invoke({"tickers": request.tickers, "question": request.question})
    return PortfolioResponseV1(metrics=result["metrics"], summary=result["summary"])


@app.post("/v2/analyze-portfolio", response_model=PortfolioResponseV2)
def analyze_portfolio_v2(request: PortfolioRequest) -> PortfolioResponseV2:
    result = agent_v2.invoke({"tickers": request.tickers, "question": request.question})
    return PortfolioResponseV2(metrics=result["metrics"], summary=result["summary"])
