# ⚡ AgentMarket

**Autonomous machine-to-machine payments for AI agents, powered by x402 on Monad.**

AgentMarket is a prototype marketplace where an AI agent can discover a paid service, evaluate its price against a spending budget, autonomously pay for access using the **x402 HTTP payment protocol**, and consume the purchased result.

Built at **Monad Blitz Berlin**.

---

## The Idea

AI agents can call APIs, use tools, and interact with other agents — but most APIs still assume that a human created an account, entered billing information, purchased credits, and generated an API key.

AgentMarket explores a different model:

> **What if an agent could discover a service and pay another service directly?**

Instead of requiring subscriptions or pre-funded platform credits, a service can respond with:

```http
HTTP/1.1 402 Payment Required
```

The agent evaluates the payment requirement against its budget, authorizes an x402 payment, and retries the request.

Once settlement succeeds, the service returns the purchased resource.

---

## Demo Flow

```text
User
 │
 │ "Research ETH market sentiment"
 │ Budget: $0.01
 ▼
┌──────────────────────────────┐
│       Python Agent           │
│                              │
│ Discover service             │
│ Check price                  │
│ Enforce spending budget      │
└──────────────┬───────────────┘
               │
               │ GET /api/research
               ▼
┌──────────────────────────────┐
│    Paid Research Service     │
│                              │
│ HTTP 402 Payment Required    │
│ Price: $0.001 USDC           │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│        x402 Payer            │
│                              │
│ Sign payment authorization   │
│ Pay $0.001 USDC              │
└──────────────┬───────────────┘
               │
               ▼
          Monad Testnet
               │
               │ Payment settled
               ▼
┌──────────────────────────────┐
│    Paid Research Service     │
│                              │
│ HTTP 200                     │
│ Purchased result returned    │
└──────────────┬───────────────┘
               │
               ▼
         Python Agent
               │
               ▼
        Result displayed
```

Example:

```text
=== AgentMarket ===
Task: Research ETH market sentiment
Budget: $0.01

[DISCOVER] research-agent costs $0.001 USDC
[DECIDE] Purchase approved. $0.001 <= $0.01
[PAY] Executing x402 payment on Monad...
[PAID] Payment successful.
[RECEIVE] Purchased result from research-agent

=== Purchased Intelligence ===
Asset:      ETH
Sentiment:  bullish
Confidence: 0.82

Spent:      $0.001 USDC
Remaining:  $0.009
Network:    eip155:10143
```

---

## Why x402?

HTTP has had a status code for payments for decades:

```text
402 Payment Required
```

x402 turns that status code into a machine-readable payment protocol.

This makes it possible for software agents to:

- encounter a paid resource;
- understand its payment requirements;
- authorize payment programmatically;
- retry the request with payment;
- receive the resource without a human checkout flow.

AgentMarket uses this mechanism for **agent-to-service payments**.

---

## Why Monad?

Machine-to-machine payments benefit from infrastructure designed for fast and inexpensive execution.

AgentMarket currently uses:

```text
Network: Monad Testnet
Chain ID: 10143
CAIP-2:   eip155:10143
Payment:  USDC
Protocol: x402
```

The project uses the Monad x402 facilitator for payment verification and settlement.

---

## Architecture

AgentMarket deliberately keeps the architecture small.

```text
agentmarket/
│
├── agent/
│   ├── agent.py
│   ├── app.py
│   └── requirements.txt
│
├── payer/
│   ├── src/
│   │   └── pay.ts
│   ├── package.json
│   ├── tsconfig.json
│   └── .env.example
│
├── services/
│   └── api/
│       ├── src/
│       │   └── server.ts
│       ├── package.json
│       ├── tsconfig.json
│       └── .env.example
│
├── .gitignore
└── README.md
```

### `agent/`

The Python orchestration layer.

It is responsible for:

- receiving the task;
- maintaining the spending budget;
- evaluating whether a service is affordable;
- invoking the x402 payment adapter;
- consuming the purchased response.

`app.py` provides the Streamlit demo interface.

### `payer/`

The x402 payment adapter.

It is responsible for:

- managing the agent's wallet signer;
- handling the HTTP 402 challenge;
- creating the x402 payment authorization;
- enforcing allowed assets and maximum payment amounts;
- retrying the protected request after payment.

The wallet private key stays server-side and is never exposed to the UI.

### `services/api/`

The paid resource server.

It exposes a protected endpoint:

```http
GET /api/research
```

Without payment, the endpoint responds with an x402 payment requirement.

After a valid payment is settled, it returns the purchased resource.

---

## Spending Controls

Autonomous payments should not mean unlimited payments.

AgentMarket uses two layers of spending protection.

### Agent budget

The Python agent refuses purchases that exceed its current task budget.

For example:

```text
Budget: $0.000
Service: $0.001

→ Purchase refused
```

### x402 payer controls

The payment adapter also restricts which token and network can be used and limits the maximum amount that can be authorized per payment.

This provides a second enforcement boundary below the agent's decision layer.

---

## Prerequisites

Install:

- Python 3.12+
- Node.js 20+
- npm
- Git
- an EVM-compatible wallet
- Monad Testnet funds
- Monad Testnet USDC

---

## Local Setup

### 1. Clone the repository

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

Create `.env` from the example:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Set:

```env
PAY_TO_ADDRESS=0xYOUR_RECEIVER_WALLET_ADDRESS
```

This is the wallet that receives payments.

Start the API:

```bash
npm start
```

The default local server is:

```text
http://localhost:4021
```

Check:

```text
GET http://localhost:4021/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "agentmarket-api"
}
```

The protected endpoint is:

```text
GET http://localhost:4021/api/research
```

An unpaid request should return:

```text
402 Payment Required
```

---

### 3. Configure the x402 payer

Open another terminal:

```bash
cd payer
npm install
```

Create the local environment file:

```bash
cp .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

Configure:

```env
PRIVATE_KEY=0xYOUR_AGENT_WALLET_PRIVATE_KEY
AGENTMARKET_API_URL=http://localhost:4021/api/research
```

Use a dedicated development wallet containing only the funds required for testing.

**Never commit this `.env` file or your private key.**

Test the payer:

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

> Running the payer performs an actual testnet payment.

---

### 4. Run the Python agent

From the project root:

```bash
cd agent
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python agent.py
```

The agent evaluates the service price against its budget and purchases the resource when allowed.

---

## Run the Demo UI

Make sure the paid API is running first.

Then:

```bash
cd agent
streamlit run app.py
```

Open the URL printed by Streamlit.

Try two budgets.

### Refused purchase

```text
Budget: 0.000 USDC
```

The agent should refuse the purchase without spending funds.

### Approved purchase

```text
Budget: 0.010 USDC
```

The agent should:

```text
Discover service
      ↓
Check budget
      ↓
Receive HTTP 402
      ↓
Pay $0.001 USDC via x402
      ↓
Unlock service
      ↓
Display purchased result
```

> The approved path performs a real Monad Testnet USDC payment.

---

## Environment Variables

### Paid API

`services/api/.env`

```env
PAY_TO_ADDRESS=0x...
```

### Payer

`payer/.env`

```env
PRIVATE_KEY=0x...
AGENTMARKET_API_URL=http://localhost:4021/api/research
```

`.env` files are intentionally excluded from Git.

Only `.env.example` files should be committed.

---

## Security

This repository is a hackathon prototype and should not be treated as production payment infrastructure.

If you reuse it:

1. Use a dedicated wallet with limited funds.
2. Never expose private keys to the browser.
3. Never commit `.env` files.
4. Enforce payment limits independently of agent reasoning.
5. Restrict permitted networks and assets.
6. Validate all payment requirements before signing.
7. Add authentication/rate limiting before exposing privileged payment operations.
8. Use a proper secret manager in production.

---

## Current Prototype Scope

The project currently focuses on proving the payment primitive:

```text
agent
  → discovers service
  → makes economic decision
  → encounters HTTP 402
  → pays autonomously
  → receives purchased resource
```

The research response used by the hackathon prototype is intentionally simple/static. The core experiment is the **autonomous x402 payment flow**, not the quality of the research model.

This distinction is important if you build on the project: replace the example research endpoint with any useful paid capability, such as:

- model inference;
- data retrieval;
- specialized research;
- image generation;
- compute jobs;
- agent tools;
- API calls;
- other agent services.

The payment architecture remains the same.

---

## Reusing AgentMarket

To turn the prototype into another paid service:

1. Replace or extend the protected resource in `services/api`.
2. Set the service's x402 price.
3. Configure the receiver wallet.
4. Point the payer at the protected endpoint.
5. Configure the payer's allowed asset and spending limits.
6. Let the agent decide when purchasing the capability is worthwhile.

The key abstraction is:

```text
Capability + Price + HTTP 402
              ↓
        Agent Decision
              ↓
         x402 Payment
              ↓
       Capability Result
```

---

## Tech Stack

- **Python** — agent orchestration
- **Streamlit** — demo interface
- **TypeScript / Node.js** — payment and service infrastructure
- **Express** — paid API
- **x402** — HTTP-native payment protocol
- **viem** — EVM account/signing utilities
- **Monad Testnet** — settlement network
- **USDC** — payment asset

---

## Hackathon

Built during **Monad Blitz Berlin**.

The prototype explores machine-to-machine commerce where software agents can independently purchase capabilities instead of relying on human-managed subscriptions and API credits.

---

## License

This project does not currently include a license.

If you intend others to freely reuse and modify the repository, add an explicit open-source license before publishing it. MIT is a common choice for hackathon projects.