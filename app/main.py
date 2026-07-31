from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.agent.graph import build_agent
from app.agent.state import TickerMetrics

# Load GOOGLE_API_KEY (and any other vars) from .env into the process environment.
# Must happen before build_agent()/summarize() run, since ChatGoogleGenerativeAI
# reads GOOGLE_API_KEY straight from os.environ.
load_dotenv()

app = FastAPI(title="Agentic Finance Assistant API")

# Compile the graph once at import time, not per-request — there's no reason
# to rebuild the same node/edge wiring on every call.
agent = build_agent()


class PortfolioRequest(BaseModel):
    tickers: list[str] = Field(
        ..., min_length=1, description="Ticker symbols, e.g. ['AAPL', 'VWCE.DE']"
    )
    question: str = Field(..., min_length=1, description="Natural-language question about the portfolio")


class PortfolioResponse(BaseModel):
    metrics: dict[str, TickerMetrics]
    summary: str


@app.post("/analyze-portfolio", response_model=PortfolioResponse)
def analyze_portfolio(request: PortfolioRequest) -> PortfolioResponse:
    result = agent.invoke({"tickers": request.tickers, "question": request.question})
    return PortfolioResponse(metrics=result["metrics"], summary=result["summary"])
