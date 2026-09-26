from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import streamlit as st

from marketplace import SERVICES, Service, ServiceMatch, select_service


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAYER_DIR = PROJECT_ROOT / "payer"

DEFAULT_TASK = "Research ETH market sentiment"
DEFAULT_BUDGET = 0.01
BUDGET_STEP = 0.001


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PaymentResult:
    """Normalized result returned by the x402 payment adapter."""

    success: bool
    status: int
    network: str
    amount: Decimal
    currency: str
    payer: str
    data: dict[str, Any]


class PaymentError(RuntimeError):
    """Raised when an x402 payment cannot be completed."""


# ---------------------------------------------------------------------------
# Payment adapter
# ---------------------------------------------------------------------------


def get_npm_command() -> str:
    """Return the platform-appropriate npm executable."""

    return "npm.cmd" if os.name == "nt" else "npm"


def execute_x402_payment() -> PaymentResult:
    """
    Execute the existing TypeScript x402 payment adapter.

    The TypeScript payer owns wallet signing and x402 protocol handling.
    Python receives only the machine-readable result from stdout.

    Raises:
        PaymentError: If the payer fails or returns an invalid response.
    """

    completed = subprocess.run(
        [get_npm_command(), "run", "start", "--silent"],
        cwd=PAYER_DIR,
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        error_message = (
            completed.stderr.strip()
            or completed.stdout.strip()
            or "Unknown x402 payer error."
        )

        raise PaymentError(
            f"x402 payment adapter failed: {error_message}"
        )

    stdout = completed.stdout.strip()

    if not stdout:
        raise PaymentError(
            "x402 payment adapter returned no response."
        )

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise PaymentError(
            "x402 payment adapter returned invalid JSON."
        ) from exc

    if payload.get("success") is not True:
        raise PaymentError(
            f"x402 payment was not successful: {payload}"
        )

    try:
        return PaymentResult(
            success=True,
            status=int(payload["status"]),
            network=str(payload["network"]),
            amount=Decimal(str(payload["amount"])),
            currency=str(payload["currency"]),
            payer=str(payload["payer"]),
            data=payload["data"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise PaymentError(
            "x402 payer returned an unexpected response format."
        ) from exc


# ---------------------------------------------------------------------------
# Marketplace presentation
# ---------------------------------------------------------------------------


def render_header() -> None:
    """Render the AgentMarket introduction."""

    st.title("⚡ AgentMarket")

    st.caption(
        "Autonomous capability discovery and payments "
        "with x402 on Monad"
    )

    st.markdown(
        """
**Give the agent a task and a spending budget.**

AgentMarket discovers available services, evaluates their
relevance and price, selects a suitable capability, and
autonomously pays for access using x402.
"""
    )


def render_marketplace() -> None:
    """Display the services currently listed in AgentMarket."""

    st.subheader("Agent Service Marketplace")

    columns = st.columns(len(SERVICES))

    for column, service in zip(columns, SERVICES):
        with column:
            st.markdown(f"**{service.name}**")
            st.caption(service.capability)

            st.metric(
                "Price",
                f"${service.price} USDC",
            )

            if service.purchasable:
                st.caption("🟢 Live x402 service")
            else:
                st.caption("⚪ Marketplace listing")


def get_service_decision(
    match: ServiceMatch,
    budget: Decimal,
) -> str:
    """Explain why a marketplace service is or is not a candidate."""

    service = match.service

    if match.score == 0:
        return "Not relevant"

    if service.price > budget:
        return "Over budget"

    if not service.purchasable:
        return "Listed / unavailable"

    return "Candidate"


def render_service_evaluation(
    matches: list[ServiceMatch],
    budget: Decimal,
) -> None:
    """Show how the agent evaluated discovered services."""

    st.markdown("#### Service evaluation")

    for match in matches:
        service = match.service
        decision = get_service_decision(
            match=match,
            budget=budget,
        )

        st.write(
            f"**{service.name}** — "
            f"${service.price} USDC · "
            f"relevance {match.score} · "
            f"**{decision}**"
        )


# ---------------------------------------------------------------------------
# Purchased result presentation
# ---------------------------------------------------------------------------


def render_purchased_result(
    payment: PaymentResult,
) -> None:
    """Display the resource returned by the paid service."""

    try:
        result = payment.data["result"]

        asset = result["asset"]
        sentiment = result["sentiment"]
        confidence = float(result["confidence"])
    except (KeyError, TypeError, ValueError) as exc:
        raise PaymentError(
            "Paid service returned an unexpected result format."
        ) from exc

    st.markdown("### Purchased intelligence")

    asset_column, sentiment_column, confidence_column = st.columns(3)

    asset_column.metric(
        "Asset",
        asset,
    )

    sentiment_column.metric(
        "Sentiment",
        str(sentiment).title(),
    )

    confidence_column.metric(
        "Confidence",
        f"{confidence * 100:.0f}%",
    )


def render_agent_economics(
    selected_service: Service,
    payment: PaymentResult,
    budget: Decimal,
) -> None:
    """Display the economic outcome of the agent's purchase."""

    remaining_budget = budget - payment.amount

    st.markdown("### Agent economics")

    st.code(
        "\n".join(
            [
                f"Selected:  {selected_service.name}",
                f"Payer:     {payment.payer}",
                f"Spent:     {payment.amount} {payment.currency}",
                f"Network:   {payment.network}",
                f"Budget:    {budget} USDC",
                f"Remaining: {remaining_budget} USDC",
            ]
        )
    )


# ---------------------------------------------------------------------------
# Agent workflow
# ---------------------------------------------------------------------------


def run_agent(
    task: str,
    budget: Decimal,
) -> None:
    """
    Run the AgentMarket discovery, selection, and purchase workflow.

    Workflow:
        1. Discover marketplace services.
        2. Rank them against the user's task.
        3. Enforce availability and budget constraints.
        4. Select a suitable service.
        5. Execute its x402 payment.
        6. Display the purchased resource.
    """

    normalized_task = task.strip()

    if not normalized_task:
        st.warning(
            "Enter a task before running the agent."
        )
        return

    st.markdown("### Agent activity")

    st.write(
        f"🔎 **Discovering services for:** `{normalized_task}`"
    )

    selected_service, matches = select_service(
        task=normalized_task,
        budget=budget,
    )

    st.write(
        f"**{len(matches)} marketplace services discovered.**"
    )

    render_service_evaluation(
        matches=matches,
        budget=budget,
    )

    if selected_service is None:
        st.error(
            "No suitable live service matches both "
            "the task and the spending budget."
        )
        return

    st.success(
        f"Selected **{selected_service.name}** — "
        f"${selected_service.price} USDC"
    )

    st.caption(
        "Selection is based on task relevance, "
        "service availability, price, and budget."
    )

    st.info(
        "Calling selected service → "
        "HTTP 402 Payment Required"
    )

    with st.spinner(
        f"Paying ${selected_service.price} USDC "
        "via x402 on Monad..."
    ):
        try:
            payment = execute_x402_payment()
        except PaymentError as exc:
            st.error(str(exc))
            return

    # Defense-in-depth check:
    # the amount reported by the payer must match the selected listing.
    if payment.amount != selected_service.price:
        st.error(
            "Payment amount does not match the selected "
            "marketplace price."
        )
        return

    st.success(
        "Payment settled. Selected service unlocked."
    )

    try:
        render_purchased_result(payment)
    except PaymentError as exc:
        st.error(str(exc))
        return

    render_agent_economics(
        selected_service=selected_service,
        payment=payment,
        budget=budget,
    )

    st.caption(
        "AgentMarket discovered the capability, evaluated "
        "the economics, selected the service, authorized "
        "the purchase, and received the resource after "
        "x402 settlement."
    )


# ---------------------------------------------------------------------------
# Streamlit application
# ---------------------------------------------------------------------------


def main() -> None:
    """Render and run the AgentMarket Streamlit application."""

    st.set_page_config(
        page_title="AgentMarket",
        page_icon="⚡",
        layout="centered",
    )

    render_header()

    task = st.text_input(
        "Task",
        value=DEFAULT_TASK,
        help="Describe the capability the agent should purchase.",
    )

    budget_input = st.number_input(
        "Maximum budget (USDC)",
        min_value=0.0,
        value=DEFAULT_BUDGET,
        step=BUDGET_STEP,
        format="%.3f",
        help="Maximum amount the agent is allowed to spend.",
    )

    st.divider()

    render_marketplace()

    st.divider()

    if st.button(
        "Run autonomous agent",
        type="primary",
        use_container_width=True,
    ):
        run_agent(
            task=task,
            budget=Decimal(str(budget_input)),
        )


if __name__ == "__main__":
    main()