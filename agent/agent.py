from __future__ import annotations

import json
import subprocess
import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAYER_DIR = PROJECT_ROOT / "payer"

SERVICE_PRICE = Decimal("0.001")
DEFAULT_BUDGET = Decimal("0.01")


@dataclass(frozen=True)
class PurchaseResult:
    service: str
    amount: Decimal
    currency: str
    network: str
    data: dict[str, Any]


class AgentMarketError(RuntimeError):
    """Raised when an AgentMarket purchase cannot be completed."""


def purchase_research() -> PurchaseResult:
    """Purchase research through the existing x402 payment adapter."""

    npm_command = "npm.cmd" if os.name == "nt" else "npm"

    completed = subprocess.run(
        [npm_command, "run", "start", "--silent"],
        cwd=PAYER_DIR,
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        error = completed.stderr.strip() or completed.stdout.strip()
        raise AgentMarketError(f"x402 payment failed: {error}")

    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()

    print(f"[DEBUG] payer return code: {completed.returncode}")
    print(f"[DEBUG] stdout: {stdout!r}")
    print(f"[DEBUG] stderr: {stderr!r}")

    if not stdout:
        raise AgentMarketError(
            f"x402 payer returned no stdout. stderr={stderr!r}"
        )

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise AgentMarketError(
            f"x402 payer returned invalid JSON:\n{stdout}"
        ) from exc

    if payload.get("success") is not True:
        raise AgentMarketError(
            f"x402 payer reported failure: {payload}"
        )

    return PurchaseResult(
        service="research-agent",
        amount=Decimal(payload["amount"]),
        currency=payload["currency"],
        network=payload["network"],
        data=payload["data"],
    )


def run_agent(
    task: str,
    budget: Decimal = DEFAULT_BUDGET,
) -> None:
    print("\n=== AgentMarket ===")
    print(f"Task: {task}")
    print(f"Budget: ${budget}")
    print()

    print(
        f"[DISCOVER] research-agent costs "
        f"${SERVICE_PRICE} USDC"
    )

    if SERVICE_PRICE > budget:
        print(
            "[REFUSE] Service exceeds the agent's spending budget."
        )
        return

    print(
        f"[DECIDE] Purchase approved. "
        f"${SERVICE_PRICE} <= ${budget}"
    )

    print("[PAY] Executing x402 payment on Monad...")

    purchase = purchase_research()

    remaining_budget = budget - purchase.amount

    print("[PAID] Payment successful.")
    print(
        f"[RECEIVE] Purchased result from {purchase.service}"
    )

    result = purchase.data["result"]

    print()
    print("=== Purchased Intelligence ===")
    print(f"Asset:      {result['asset']}")
    print(f"Sentiment:  {result['sentiment']}")
    print(f"Confidence: {result['confidence']}")
    print()
    print(f"Spent:     ${purchase.amount} {purchase.currency}")
    print(f"Remaining: ${remaining_budget}")
    print(f"Network:   {purchase.network}")


if __name__ == "__main__":
    run_agent(
        task="Research ETH market sentiment",
        budget=Decimal("0.01"),
    )