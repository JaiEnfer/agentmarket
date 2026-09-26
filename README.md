# ⚡ AgentMarket

**An autonomous capability marketplace where AI agents discover, evaluate, select, and pay for services using x402 on Monad.**

AgentMarket is a prototype marketplace for machine-to-machine commerce.

Instead of requiring a human to create accounts, manage subscriptions, purchase credits, and configure API keys, an autonomous agent can:

1. discover available capabilities;
2. evaluate services against its task;
3. compare relevance, price, and availability;
4. enforce a spending budget;
5. select an appropriate service;
6. encounter an HTTP `402 Payment Required`;
7. autonomously authorize an x402 payment;
8. receive the purchased capability after settlement.

Built at **Monad Blitz Berlin**.

---

## The Idea

AI agents can call APIs, use tools, and interact with other agents, but access to paid capabilities is still usually designed around humans.

A developer normally needs to:

```text
Create account
      ↓
Add billing method
      ↓
Buy credits / subscription
      ↓
Generate API key
      ↓
Give API key to agent
```

AgentMarket explores a different model:

> **What if capabilities could advertise a price, and autonomous agents could decide what is worth buying?**

With AgentMarket:

```text
Task
  ↓
Discover marketplace
  ↓
Evaluate capabilities
  ↓
Select service
  ↓
HTTP 402 Payment Required
  ↓
x402 payment
  ↓
Monad settlement
  ↓
Capability unlocked
```

The payment becomes part of the machine-to-machine protocol rather than a separate human checkout flow.

---

## What Makes AgentMarket Different?

x402 provides the payment primitive.

AgentMarket experiments with the **economic decision layer above that primitive**.

The agent does not simply pay a predefined API.

It first asks:

```text
Which services are available?

Which ones are relevant to my task?

Which ones are actually live?

Which ones fit my budget?

Which suitable service should I purchase?
```

Only after making those decisions does it authorize a payment.

This turns:

```text
Agent → Paid API
```

into:

```text
Agent
  ↓
Capability Marketplace
  ↓
Discovery
  ↓
Evaluation
  ↓
Economic Decision
  ↓
Service Selection
  ↓
x402 Payment
  ↓
Purchased Capability
```

---

## Live Demo

Example task:

```text
Research ETH market sentiment
```

Agent budget:

```text
0.010 USDC
```

AgentMarket currently exposes a marketplace containing:

| Service | Capability | Price | Status |
|---|---|---:|---|
| Quick Research Agent | Market sentiment | 0.001 USDC | 🟢 Live x402 service |
| Risk Analysis Agent | Risk analysis | 0.002 USDC | ⚪ Marketplace listing |
| Deep Research Agent | Detailed research | 0.003 USDC | ⚪ Marketplace listing |

The agent evaluates the marketplace:

```text
[DISCOVER]

3 marketplace services discovered.

        ↓

[EVALUATE]

Quick Research Agent
Price:     0.001 USDC
Relevance: High
Status:    Candidate

Risk Analysis Agent
Price:     0.002 USDC
Relevance: Lower
Status:    Listed / unavailable

Deep Research Agent
Price:     0.003 USDC
Relevance: Lower
Status:    Listed / unavailable

        ↓

[SELECT]

Quick Research Agent
Price: 0.001 USDC

        ↓

[REQUEST]

GET /api/research

        ↓

HTTP 402 Payment Required

        ↓

[PAY]

0.001 USDC via x402 on Monad

        ↓

[SETTLE]

Payment verified and settled

        ↓

[UNLOCK]

HTTP 200

        ↓

Purchased intelligence
```

Example purchased result:

```text
Asset:      ETH
Sentiment:  Bullish
Confidence: 82%

Selected:   Quick Research Agent
Spent:      0.001 USDC
Budget:     0.010 USDC
Remaining:  0.009 USDC
Network:    eip155:10143
```

---

## Autonomous Spending Constraints

AgentMarket does not equate autonomous payments with unrestricted payments.

For example, with:

```text
Budget: 0.000 USDC
```

the same marketplace evaluation produces:

```text
Quick Research Agent  → Over budget
Risk Analysis Agent   → Over budget
Deep Research Agent   → Over budget

        ↓

No suitable service fits the task and spending budget.

        ↓

NO PAYMENT
```

This demonstrates an important property of autonomous commerce:

> **The agent can decide not to transact.**

---

## Architecture

```text
                         ┌──────────────────────┐
                         │        User          │
                         │ Task + max budget    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     Python Agent     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │    Agent Service Marketplace │
                    │                              │
                    │ Quick Research    $0.001     │
                    │ Risk Analysis     $0.002     │
                    │ Deep Research     $0.003     │
                    └──────────────┬───────────────┘
                                   │
                         evaluate + select
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   Quick Research selected    │
                    │         $0.001 USDC          │
                    └──────────────┬───────────────┘
                                   │
                                   │ GET /api/research
                                   ▼
                    ┌──────────────────────────────┐
                    │    Public Paid Service       │
                    │                              │
                    │  HTTP 402 Payment Required   │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │        x402 Payer            │
                    │                              │
                    │ Spending controls            │
                    │ Wallet authorization         │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │        Monad Testnet         │
                    │          USDC                │
                    └──────────────┬───────────────┘
                                   │
                             settlement
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │    Public Paid Service       │
                    │                              │
                    │ HTTP 200 + purchased result  │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │        Python Agent          │
                    │                              │
                    │ Result + economics           │
                    └──────────────────────────────┘
```

---

## Repository Structure

```text
agentmarket/
│
├── agent/
│   ├── agent.py
│   ├── app.py
│   ├── marketplace.py
│   └── requirements.txt
│
├── payer/
│   ├── src/
│   │   └── pay.ts
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   └── .env.example
│
├── services/
│   └── api/
│       ├── src/
│       │   └── server.ts
│       ├── package.json
│       ├── package-lock.json
│       ├── tsconfig.json
│       └── .env.example
│
├── Dockerfile
├── .gitignore
└── README.md
```

---

## Components

### `agent/marketplace.py`

Defines the marketplace and autonomous service-selection policy.

Each marketplace service describes properties such as:

```text
ID
Name
Capability
Description
Price
Keywords
Availability
```

The current selection policy:

1. compares the task with service capabilities;
2. calculates deterministic relevance;
3. filters services that do not fit the budget;
4. filters services that are not currently purchasable;
5. selects the highest-relevance suitable service;
6. uses price as a tie-breaker.

The deterministic policy keeps the hackathon prototype inspectable and reproducible.

It can later be replaced or supplemented with an LLM planner, semantic search, reputation system, auction mechanism, or another agent policy.

---

### `agent/app.py`

The Streamlit application and primary demo interface.

It coordinates:

```text
Task input
    ↓
Marketplace discovery
    ↓
Service evaluation
    ↓
Budget enforcement
    ↓
Service selection
    ↓
x402 purchase
    ↓
Purchased result
    ↓
Agent economics
```

It also validates that the amount reported by the payment adapter matches the price of the service selected by the marketplace.

---

### `agent/agent.py`

A command-line version of the agent workflow.

It demonstrates the payment orchestration independently of the Streamlit interface.

---

### `payer/`

The TypeScript x402 payment adapter.

It is responsible for:

- managing the agent wallet signer;
- handling the HTTP 402 payment challenge;
- creating the x402 payment authorization;
- restricting permitted payment assets;
- enforcing maximum payment amounts;
- retrying the protected request with payment;
- returning a machine-readable result to Python.

The private key stays server-side and is never sent to the browser.

---

### `services/api/`

The paid resource server.

It exposes:

```http
GET /health
```

and the protected resource:

```http
GET /api/research
```

Without valid payment:

```text
HTTP 402 Payment Required
```

After successful x402 verification and settlement:

```text
HTTP 200
```

with the purchased resource.

---

## Why x402?

HTTP already defines:

```text
402 Payment Required
```

x402 turns that concept into a machine-readable payment flow.

A software agent can:

```text
Request resource
      ↓
Receive payment requirements
      ↓
Authorize payment
      ↓
Retry request with payment
      ↓
Receive resource
```

This enables machine-to-machine commerce without requiring a human checkout interaction for every purchase.

AgentMarket builds marketplace discovery and autonomous economic decision-making on top of that payment primitive.

---

## Why Monad?

AgentMarket currently uses:

```text
Network:  Monad Testnet
Chain ID: 10143
CAIP-2:   eip155:10143
Asset:    USDC
Protocol: x402
```

The prototype uses the Monad x402 facilitator for payment verification and settlement.

---

## Spending Controls

Autonomous payment systems need controls below the reasoning layer.

AgentMarket therefore uses multiple boundaries.

### 1. Task budget

The Python agent receives a maximum spending budget.

A service exceeding that budget is rejected before payment.

### 2. Marketplace availability

A listed service is not automatically considered purchasable.

Only services explicitly marked as live can become payment candidates.

### 3. x402 payer controls

The TypeScript payment layer restricts permitted network/assets and enforces payment limits independently of the Python decision layer.

### 4. Price consistency

After payment, the Python application verifies that:

```text
amount paid == selected marketplace price
```

This provides another check between marketplace decision-making and payment execution.

---

## Current Marketplace Status

The current hackathon prototype contains three marketplace listings.

Only **Quick Research Agent** currently has a live x402-backed implementation.

The other services demonstrate capability discovery and marketplace evaluation but are deliberately marked unavailable.

This is intentional.

The project does **not** pretend that placeholder marketplace listings are deployed paid services.

The next logical evolution is allowing independent providers to register their own live x402 endpoints.

---

## Prerequisites

Install:

- Python 3.12+
- Node.js 20+
- npm
- Git
- an EVM-compatible development wallet
- Monad Testnet funds
- Monad Testnet USDC

Use a dedicated development wallet with limited funds.

---

## Local Setup

### 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/agentmarket.git
cd agentmarket
```

Replace `YOUR_USERNAME` with the GitHub account hosting the repository.

---

### 2. Configure the paid API

```bash
cd services/api
npm install
```

Create the environment file.

macOS/Linux:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Configure:

```env
PAY_TO_ADDRESS=0xYOUR_RECEIVER_WALLET_ADDRESS
```

Start:

```bash
npm start
```

By default:

```text
http://localhost:4021
```

Health check:

```text
GET http://localhost:4021/health
```

Expected:

```json
{
  "status": "ok",
  "service": "agentmarket-api"
}
```

The protected endpoint:

```text
GET http://localhost:4021/api/research
```

should return an x402 payment requirement when called without payment.

---

### 3. Configure the payer

In another terminal:

```bash
cd payer
npm install
```

Create `.env`.

macOS/Linux:

```bash
cp .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

Configure:

```env
PRIVATE_KEY=0xYOUR_DEVELOPMENT_WALLET_PRIVATE_KEY
AGENTMARKET_API_URL=http://localhost:4021/api/research
```

Never commit this file.

Test:

```bash
npm run start --silent
```

A successful invocation returns machine-readable JSON similar to:

```json
{
  "success": true,
  "status": 200,
  "network": "eip155:10143",
  "amount": "0.001",
  "currency": "USDC",
  "payer": "0x...",
  "data": {
    "service": "research-agent",
    "result": {
      "asset": "ETH",
      "sentiment": "bullish",
      "confidence": 0.82
    }
  }
}
```

> This command performs an actual Monad Testnet payment.

---

### 4. Configure Python

```bash
cd agent
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install:

```bash
pip install -r requirements.txt
```

---

## Run the Command-Line Agent

```bash
cd agent
python agent.py
```

---

## Run the Marketplace UI

Make sure the paid API is running and the payer environment is configured.

Then:

```bash
cd agent
streamlit run app.py
```

Open the URL printed by Streamlit.

### Test 1 — economic refusal

Task:

```text
Research ETH market sentiment
```

Budget:

```text
0.000 USDC
```

Expected:

```text
3 marketplace services discovered

Quick Research Agent → Over budget
Risk Analysis Agent  → Over budget
Deep Research Agent  → Over budget

No suitable service matches the task and spending budget.

NO PAYMENT
```

### Test 2 — autonomous purchase

Budget:

```text
0.010 USDC
```

Expected:

```text
Discover 3 services
       ↓
Evaluate relevance + price + availability
       ↓
Select Quick Research Agent
       ↓
HTTP 402 Payment Required
       ↓
Pay 0.001 USDC via x402
       ↓
Monad settlement
       ↓
Unlock service
       ↓
ETH / Bullish / 82%
       ↓
Remaining budget: 0.009 USDC
```

> The successful path performs a real Monad Testnet USDC payment.

---

## Environment Variables

### Paid API

`services/api/.env`

```env
PAY_TO_ADDRESS=0x...
```

### Agent / payer

`payer/.env`

```env
PRIVATE_KEY=0x...
AGENTMARKET_API_URL=http://localhost:4021/api/research
```

For deployment, configure these through the hosting provider's environment-variable or secret-management interface rather than committing them to Git.

---

## Deployment Architecture

The hackathon deployment separates the public UI from the paid service.

```text
Public AgentMarket UI
Python + Streamlit
        │
        │ service selection
        ▼
x402 payer
        │
        │ Internet
        ▼
Public Paid API
        │
        ├── 402 Payment Required
        │
        ▼
x402 / Monad
        │
        │ settlement
        ▼
Public Paid API
        │
        └── 200 + resource
        ▼
AgentMarket UI
```

The repository includes a root `Dockerfile` for deploying the mixed Python + Node agent application.

Runtime secrets are injected through deployment environment variables.

---

## Security

This is a hackathon prototype, not production payment infrastructure.

If you reuse it:

1. Use a dedicated wallet containing limited funds.
2. Never expose private keys in the browser.
3. Never commit `.env` files.
4. Keep payment authorization server-side.
5. Enforce spending limits independently of agent reasoning.
6. Restrict permitted networks and assets.
7. Validate payment requirements before signing.
8. Verify paid amounts against marketplace expectations.
9. Add authentication and rate limiting before exposing privileged payment operations.
10. Use a production secret manager for real funds.

---

## Current Prototype Scope

The prototype focuses on the economic and payment primitive:

```text
Agent
  ↓
Discover capabilities
  ↓
Evaluate competing services
  ↓
Apply economic constraints
  ↓
Select capability
  ↓
Encounter HTTP 402
  ↓
Pay autonomously
  ↓
Receive purchased resource
```

The current research response is intentionally simple/static.

The innovation being demonstrated is **autonomous capability discovery, economic selection, and machine-to-machine payment**, rather than the sophistication of the research model itself.

The same architecture could be used for:

- model inference;
- proprietary datasets;
- specialized research;
- image generation;
- compute jobs;
- storage;
- agent tools;
- external APIs;
- other autonomous agents.

---

## Extending the Marketplace

A natural next step is allowing independent providers to register capabilities such as:

```json
{
  "name": "Weather Intelligence Agent",
  "capability": "weather-analysis",
  "endpoint": "https://provider.example/api/weather",
  "price": "0.002",
  "network": "eip155:10143"
}
```

The marketplace could then evolve toward:

```text
Provider registration
        ↓
Capability discovery
        ↓
Semantic matching
        ↓
Price comparison
        ↓
Reputation / quality signals
        ↓
Agent selection
        ↓
x402 purchase
```

Possible future mechanisms include:

- dynamic service registration;
- multiple live providers;
- semantic capability matching;
- provider reputation;
- service quality history;
- competitive pricing;
- bidding;
- auctions;
- agent-to-agent negotiation.

These are future directions, not features claimed by the current prototype.

---

## Reusing AgentMarket

To add another real paid capability:

1. implement the capability endpoint;
2. protect it with x402;
3. configure its payment recipient and price;
4. register the service in the marketplace;
5. mark it purchasable only when the endpoint is actually live;
6. configure the payer's allowed assets and limits;
7. extend the payment adapter if different endpoints require dynamic routing.

The core abstraction is:

```text
Capability
    +
Price
    +
Availability
    +
Payment Requirement
        ↓
Agent Evaluation
        ↓
Economic Decision
        ↓
Service Selection
        ↓
x402 Payment
        ↓
Capability Result
```

---

## Tech Stack

- **Python** — agent orchestration and marketplace policy
- **Streamlit** — interactive marketplace/demo UI
- **TypeScript / Node.js** — x402 payment adapter and service infrastructure
- **Express** — paid resource API
- **x402** — HTTP-native machine payment protocol
- **viem** — EVM account/signing utilities
- **Monad Testnet** — settlement network
- **USDC** — payment asset
- **Docker** — mixed Python/Node deployment

---

## Hackathon

Built during **Monad Blitz Berlin**.

AgentMarket explores a future where software doesn't merely call software:

> **Software can discover capabilities, evaluate their economics, and buy services from software.**

---

## License

No license is currently included.

If you want others to freely use, modify, and redistribute AgentMarket, add an explicit open-source license such as MIT.