# Agentic Finance Assistant API

A lightweight, production-styled backend service that uses **LangGraph** to orchestrate an AI agent capable of answering natural-language portfolio questions. Built to demonstrate skills relevant to AI/LLM integration, agentic workflow orchestration, and cloud-native backend engineering.

## Problem Statement

Retail investors often need quick, contextual answers about their portfolio (e.g., "How has my ETF basket performed this year?" or "What's the volatility of these three stocks?") rather than raw numbers requiring manual interpretation. Manually fetching market data, computing financial metrics, and translating them into plain-language insights is slow and doesn't scale. This project builds an agentic AI service that accepts a natural-language financial query, autonomously orchestrates data retrieval and calculation steps, and returns a clear, LLM-generated explanation — demonstrating how AI can be integrated into a production-style backend rather than used as a standalone chatbot.

## Architecture

```
Client Request (ticker list + question)
        |
        v
   FastAPI Endpoint (/analyze-portfolio)
        |
        v
   LangGraph Agent
     ├── fetch_data        (pulls market data via yfinance)
     ├── calculate_metrics (returns, volatility)
     └── summarize         (LLM call -> plain-language explanation)
        |
        v
   JSON Response (metrics + summary)
```

### Agent State Flow

Each LangGraph node reads specific fields from the shared state and writes new ones back; the state accumulates as it moves through the graph:

```
Initial state:
  { tickers, question }
        |
        v
  ┌─────────────┐
  │ fetch_data  │  reads: tickers
  └─────────────┘  writes: price_data
        |
        v
  { tickers, question, price_data }
        |
        v
  ┌───────────────────┐
  │ calculate_metrics │  reads: price_data
  └───────────────────┘  writes: metrics
        |
        v
  { tickers, question, price_data, metrics }
        |
        v
  ┌─────────────┐
  │ summarize   │  reads: question, metrics
  └─────────────┘  writes: summary
        |
        v
  Final state:
  { tickers, question, price_data, metrics, summary }
```

## Tech Stack

- **Backend:** Python, FastAPI, Pydantic
- **AI Orchestration:** LangGraph
- **LLM Provider:** Google Gemini API (free tier)
- **Data:** yfinance (market data)
- **Testing:** pytest
- **Containerization:** Docker, docker-compose
- **Infrastructure as Code:** Terraform (ECS/Lambda + API Gateway + Secrets Manager)
- **CI/CD:** GitHub Actions

## Setup

```bash
git clone <repo-url>
cd agentic-finance-assistant
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your LLM API key
uvicorn app.main:app --reload
```

## Example Request

```bash
curl -X POST http://localhost:8000/analyze-portfolio \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["VWCE.DE", "AAPL"], "question": "How risky is this portfolio?"}'
```

## Running Tests

```bash
pytest -v
```

## Running with Docker

```bash
docker-compose up --build
```

## Infrastructure (Terraform)

Terraform under `infra/` defines (but is not applied by default) a full deployment: an ECR repository, an ECS Fargate service behind an Application Load Balancer, an HTTP API Gateway proxying to the ALB, and a Secrets Manager entry for the Gemini API key. `terraform plan` has been run and validated against a real AWS account — it correctly resolves the account's default VPC/subnets and shows a clean 18-resource create plan — but nothing has been applied.

```bash
cd infra
terraform init
terraform plan -var="container_image=placeholder" -var="google_api_key=placeholder"
```

### To actually deploy this for real

1. Copy `infra/terraform.tfvars.example` to `infra/terraform.tfvars` and fill in your real Gemini key (gitignored, never committed)
2. `terraform apply -target=aws_ecr_repository.app` — creates just the ECR repository
3. `terraform output ecr_repository_url` — get its URL
4. Build and push the Docker image there (see comments in `terraform.tfvars.example` for the exact `docker build`/`docker push` commands)
5. Set `container_image` in `terraform.tfvars` to the pushed image's URI
6. `terraform apply` — creates everything else
7. **`terraform destroy` when done** — this stack costs real money if left running (mainly the ALB, roughly $16-20/month)

## Roadmap

This project is being built in versioned stages, each one deepening the LLM/agentic side rather than just adding features.

### v1 — Fixed pipeline ✅ Done

A deterministic, linear graph: `fetch_data → calculate_metrics → summarize`, always in that exact order. The LLM's only role is turning pre-computed metrics into plain-language prose at the very end. One-shot, stateless, free-text output.

### v2 — Structured, well-prompted output 🚧 In Progress

Goal: master prompt engineering and output control before adding graph complexity.

- **Structured output** — `summarize` returns a Pydantic-validated JSON shape (risk rating, key drivers, confidence) instead of free prose
- **Real prompt engineering** — few-shot examples, explicit tone/format constraints, proper system vs. user message separation
- **Question classification + conditional routing** — a new node classifies the question type (risk / performance / comparison) and routes to different prompt strategies via LangGraph's conditional edges — the graph's first real decision point, not just sequential execution

### v3 — True agentic behavior 📋 Planned

Goal: the core skill LangGraph is built around — the LLM deciding what to do, not just how to phrase it.

- **Tool-calling agent** — replace the fixed pipeline with an LLM that decides which tools to invoke and when (e.g., skip volatility for a pure performance question, or call `fetch_data` twice for a comparison question) — a ReAct-style pattern
- **Multi-turn memory** — LangGraph checkpointing so follow-up questions don't require restating context

### Later / optional polish

- Evaluation harness — score summary quality/consistency across prompt variants
- RAG — pull in real news/filings context alongside price metrics
- Streaming responses (Server-Sent Events) for the LLM summary
- Monitoring/tracing for LLM latency and token cost per request
- Deploy Terraform to a live AWS environment

## License

MIT
