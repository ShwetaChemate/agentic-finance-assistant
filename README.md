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

## Development Time Breakdown

Total build time: **~9.5 hours**, scoped intentionally to stay under a 10-hour budget by skipping live AWS deployment (Terraform written but not applied).

| # | Task | Estimated Hours |
|---|------|------------------|
| 1 | Project setup (repo, venv, dependencies) | 0.5 |
| 2 | LangGraph agent design (state + 3 nodes: fetch_data, calculate_metrics, summarize) | 2.25 |
| 3 | FastAPI endpoint + Pydantic request/response models | 1.25 |
| 4 | Unit + integration tests (pytest) | 1.0 |
| 5 | Dockerfile + docker-compose setup | 1.0 |
| 6 | Terraform skeleton (ECS/Lambda, API Gateway, Secrets Manager) | 1.25 |
| 7 | CI pipeline (GitHub Actions: lint + test) | 0.75 |
| 8 | README, architecture diagram, demo GIF | 1.0 |
| **Total** | | **~9.5 hours** |

### Time Calculation Notes

- Hours are based on focused, uninterrupted work sessions; add a 15-20% buffer if working in shorter evening sessions around a full-time job or thesis writing.
- LangGraph orchestration (step 2) and Terraform (step 6) are the largest line items since they involve the most new-to-you tooling; budget extra time here if this is your first LangGraph or Terraform project.
- Skipping live AWS deployment (writing Terraform without `terraform apply`) saves roughly 3-4 additional hours and avoids cloud costs while still demonstrating IaC competency.
- If time-constrained, steps 6 and 7 (Terraform + CI) can be deferred to a v2 iteration without weakening the core demo of agentic orchestration.

## Future Improvements

- Deploy Terraform to a live AWS environment (ECS Fargate or Lambda)
- Add streaming responses (Server-Sent Events) for the LLM summary
- Add monitoring/tracing for LLM latency and token cost per request
- Expand agent with a "compare portfolios" node

## License

MIT
