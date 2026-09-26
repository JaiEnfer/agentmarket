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
# Application configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAYER_DIR = PROJECT_ROOT / "payer"

DEFAULT_TASK = "Research ETH market sentiment"
DEFAULT_BUDGET = 0.010
BUDGET_STEP = 0.001

MONAD_NETWORK = "eip155:10143"


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PaymentResult:
    """Normalized result returned by the TypeScript x402 payer."""

    success: bool
    status: int
    network: str
    amount: Decimal
    currency: str
    payer: str
    data: dict[str, Any]


class PaymentError(RuntimeError):
    """Raised when the x402 payment adapter cannot complete a purchase."""


# ---------------------------------------------------------------------------
# Payment adapter
# ---------------------------------------------------------------------------


def get_npm_command() -> str:
    """Return the correct npm executable for the current operating system."""

    return "npm.cmd" if os.name == "nt" else "npm"


def execute_x402_payment() -> PaymentResult:
    """
    Execute the TypeScript x402 payer and normalize its JSON response.

    The TypeScript layer owns wallet signing and x402 protocol handling.
    Python only orchestrates the purchase and consumes the machine-readable
    result written to stdout.

    Raises:
        PaymentError: If the payer process fails or returns invalid data.
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
        raise PaymentError(f"x402 payment adapter failed: {error_message}")

    stdout = completed.stdout.strip()

    if not stdout:
        raise PaymentError("x402 payment adapter returned no response.")

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
# UI styling
# ---------------------------------------------------------------------------


def apply_custom_styles() -> None:
    """
    Apply a small presentation layer on top of Streamlit.

    The application deliberately keeps styling here instead of introducing
    a separate frontend framework. This keeps the hackathon prototype easy
    to understand and modify.
    """

    st.markdown(
        """
        <style>
        /* Give the application a little more horizontal room. */
        .block-container {
            max-width: 1100px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        /* Reduce excessive spacing around headings. */
        h1, h2, h3 {
            letter-spacing: -0.02em;
        }

        /* Small badge used in the hero section. */
        .agentmarket-badge {
            display: inline-block;
            padding: 0.25rem 0.65rem;
            margin-right: 0.35rem;
            margin-bottom: 0.35rem;
            border: 1px solid rgba(128, 128, 128, 0.35);
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
        }

        /* Hero copy. */
        .agentmarket-hero {
            margin-bottom: 1.25rem;
        }

        .agentmarket-hero-title {
            font-size: 2.7rem;
            font-weight: 750;
            line-height: 1.05;
            margin-bottom: 0.45rem;
        }

        .agentmarket-hero-subtitle {
            font-size: 1.08rem;
            opacity: 0.78;
            max-width: 760px;
            line-height: 1.55;
            margin-bottom: 0.9rem;
        }

        /* Pipeline shown during agent execution. */
        .agentmarket-pipeline {
            padding: 0.9rem 1rem;
            margin: 0.75rem 0 1.2rem 0;
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 0.75rem;
            text-align: center;
            font-weight: 650;
            letter-spacing: 0.01em;
        }

        /* Slightly improve metric-card separation. */
        div[data-testid="stMetric"] {
            border: 1px solid rgba(128, 128, 128, 0.20);
            border-radius: 0.75rem;
            padding: 0.85rem;
        }

        /* Make the primary action easier to spot during the demo. */
        div.stButton > button[kind="primary"] {
            min-height: 3rem;
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# General presentation
# ---------------------------------------------------------------------------


def render_header() -> None:
    """Render the AgentMarket hero section."""

    st.markdown(
        """
        <div class="agentmarket-hero">
            <div class="agentmarket-hero-title">⚡ AgentMarket</div>
            <div class="agentmarket-hero-subtitle">
                An autonomous capability marketplace where agents discover,
                evaluate, select, and pay for services using x402 on Monad.
            </div>
            <span class="agentmarket-badge">Monad</span>
            <span class="agentmarket-badge">x402</span>
            <span class="agentmarket-badge">Autonomous Payments</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pipeline() -> None:
    """Show the high-level workflow that the agent is executing."""

    st.markdown(
        """
        <div class="agentmarket-pipeline">
            DISCOVER &nbsp;→&nbsp;
            EVALUATE &nbsp;→&nbsp;
            SELECT &nbsp;→&nbsp;
            PAY &nbsp;→&nbsp;
            UNLOCK
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_task_controls() -> tuple[str, Decimal, bool]:
    """
    Render task and budget controls.

    Returns:
        A tuple containing the task, normalized budget, and whether the
        user requested an agent run.
    """

    st.subheader("Give the agent a task")

    task = st.text_input(
        "Task",
        value=DEFAULT_TASK,
        placeholder="Describe the capability the agent should purchase...",
        help="The marketplace uses this task to rank available services.",
    )

    budget_column, button_column = st.columns([2, 1])

    with budget_column:
        budget_input = st.number_input(
            "Maximum budget (USDC)",
            min_value=0.0,
            value=DEFAULT_BUDGET,
            step=BUDGET_STEP,
            format="%.3f",
            help="Maximum amount the agent is allowed to spend.",
        )

    with button_column:
        # Vertical spacing aligns the button with the number input.
        st.markdown("<div style='height: 1.75rem'></div>", unsafe_allow_html=True)

        run_requested = st.button(
            "Run autonomous agent",
            type="primary",
            use_container_width=True,
        )

    return (
        task,
        Decimal(str(budget_input)),
        run_requested,
    )


# ---------------------------------------------------------------------------
# Marketplace presentation
# ---------------------------------------------------------------------------


def render_marketplace() -> None:
    """Display every service currently registered in AgentMarket."""

    st.subheader("Service Marketplace")

    st.caption(
        "Capabilities advertise a price and availability. "
        "The agent decides which service is appropriate for its task."
    )

    columns = st.columns(len(SERVICES))

    for column, service in zip(columns, SERVICES):
        with column:
            st.markdown(f"### {service.name}")
            st.caption(service.capability)

            st.metric(
                label="Price",
                value=f"${service.price}",
                help="Price in Monad Testnet USDC.",
            )

            if service.purchasable:
                st.success("● LIVE x402 SERVICE")
            else:
                st.info("○ MARKETPLACE LISTING")


def get_service_decision(
    match: ServiceMatch,
    budget: Decimal,
) -> str:
    """Explain why a discovered service is or is not a purchase candidate."""

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
    """Display the agent's marketplace evaluation in a compact table."""

    rows = []

    for match in matches:
        service = match.service

        rows.append(
            {
                "Service": service.name,
                "Capability": service.capability,
                "Price": f"${service.price}",
                "Relevance": match.score,
                "Decision": get_service_decision(
                    match=match,
                    budget=budget,
                ),
            }
        )

    st.markdown("#### Marketplace evaluation")

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Service": st.column_config.TextColumn(
                "Service",
                width="medium",
            ),
            "Capability": st.column_config.TextColumn(
                "Capability",
                width="medium",
            ),
            "Price": st.column_config.TextColumn(
                "Price",
                width="small",
            ),
            "Relevance": st.column_config.NumberColumn(
                "Relevance",
                width="small",
            ),
            "Decision": st.column_config.TextColumn(
                "Decision",
                width="medium",
            ),
        },
    )


def render_selected_service(service: Service) -> None:
    """Highlight the capability selected by the agent."""

    st.success(
        f"Selected **{service.name}** · "
        f"{service.capability} · "
        f"${service.price} USDC"
    )

    st.caption(
        "Selection is based on task relevance, service availability, "
        "price, and the agent's spending budget."
    )


# ---------------------------------------------------------------------------
# Purchased resource presentation
# ---------------------------------------------------------------------------


def extract_purchased_result(
    payment: PaymentResult,
) -> tuple[str, str, float]:
    """
    Extract and validate the purchased research result.

    Keeping validation separate from rendering makes the UI functions
    simpler and keeps malformed service responses from leaking into the
    presentation layer.
    """

    try:
        result = payment.data["result"]

        asset = str(result["asset"])
        sentiment = str(result["sentiment"])
        confidence = float(result["confidence"])
    except (KeyError, TypeError, ValueError) as exc:
        raise PaymentError(
            "Paid service returned an unexpected result format."
        ) from exc

    return asset, sentiment, confidence


def render_purchased_result(payment: PaymentResult) -> None:
    """Display the resource returned by the selected paid service."""

    asset, sentiment, confidence = extract_purchased_result(payment)

    st.subheader("Purchased Intelligence")

    asset_column, sentiment_column, confidence_column = st.columns(3)

    asset_column.metric(
        label="Asset",
        value=asset,
    )

    sentiment_column.metric(
        label="Sentiment",
        value=sentiment.title(),
    )

    confidence_column.metric(
        label="Confidence",
        value=f"{confidence * 100:.0f}%",
    )


def render_payment_receipt(
    selected_service: Service,
    payment: PaymentResult,
    budget: Decimal,
) -> None:
    """Display the economic outcome of the completed transaction."""

    remaining_budget = budget - payment.amount

    st.subheader("Payment Receipt")

    spent_column, remaining_column, network_column = st.columns(3)

    spent_column.metric(
        label="Spent",
        value=f"{payment.amount} {payment.currency}",
    )

    remaining_column.metric(
        label="Remaining",
        value=f"{remaining_budget} USDC",
    )

    network_column.metric(
        label="Network",
        value="Monad Testnet",
    )

    with st.expander("Transaction details"):
        st.markdown(f"**Service:** {selected_service.name}")
        st.markdown(f"**Payer:** `{payment.payer}`")
        st.markdown(f"**HTTP status:** `{payment.status}`")
        st.markdown(f"**Network:** `{payment.network}`")
        st.markdown(f"**Budget:** `{budget} USDC`")
        st.markdown(
            f"**Amount paid:** `{payment.amount} {payment.currency}`"
        )


# ---------------------------------------------------------------------------
# Agent workflow
# ---------------------------------------------------------------------------


def run_agent(
    task: str,
    budget: Decimal,
) -> None:
    """
    Execute the complete AgentMarket workflow.

    Workflow:
        1. Discover marketplace services.
        2. Rank services against the requested task.
        3. Apply availability and budget constraints.
        4. Select a suitable capability.
        5. Execute the x402 payment.
        6. Validate the economic result.
        7. Display the purchased resource.
    """

    normalized_task = task.strip()

    if not normalized_task:
        st.warning("Enter a task before running the agent.")
        return

    st.divider()
    st.subheader("Agent Execution")

    render_pipeline()

    st.markdown(
        f"**Task:** `{normalized_task}`  \n"
        f"**Maximum budget:** `{budget} USDC`"
    )

    # Step 1: discover and evaluate marketplace services.
    selected_service, matches = select_service(
        task=normalized_task,
        budget=budget,
    )

    st.write(
        f"**Discovery complete:** {len(matches)} marketplace "
        "services evaluated."
    )

    render_service_evaluation(
        matches=matches,
        budget=budget,
    )

    # Step 2: stop safely when no live service satisfies the constraints.
    if selected_service is None:
        st.error(
            "No suitable live service matches both the task "
            "and the spending budget."
        )

        st.info(
            "No transaction executed. The agent kept its full budget."
        )
        return

    # Step 3: show the selected capability before authorizing payment.
    render_selected_service(selected_service)

    # Step 4: invoke the selected paid service.
    st.warning(
        "Selected service requires payment → "
        "**HTTP 402 Payment Required**"
    )

    # Step 5: authorize and execute the x402 payment.
    with st.spinner(
        f"Authorizing {selected_service.price} USDC "
        "payment via x402 on Monad..."
    ):
        try:
            payment = execute_x402_payment()
        except PaymentError as exc:
            st.error(str(exc))
            return

    # Defense in depth:
    # the amount reported by the payer must equal the selected listing price.
    if payment.amount != selected_service.price:
        st.error(
            "Payment amount does not match the selected "
            "marketplace price."
        )
        return

    st.success(
        "Payment settled on Monad. "
        "The selected capability is now unlocked."
    )

    # Step 6: validate and display the purchased resource.
    try:
        render_purchased_result(payment)
    except PaymentError as exc:
        st.error(str(exc))
        return

    # Step 7: make the agent's economic outcome explicit.
    render_payment_receipt(
        selected_service=selected_service,
        payment=payment,
        budget=budget,
    )

    st.success(
        "Agent completed the task autonomously: "
        "discover → evaluate → select → pay → unlock."
    )


# ---------------------------------------------------------------------------
# Streamlit application
# ---------------------------------------------------------------------------


def main() -> None:
    """Configure and render the AgentMarket Streamlit application."""

    st.set_page_config(
        page_title="AgentMarket · Autonomous Capability Marketplace",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    apply_custom_styles()

    render_header()

    task, budget, run_requested = render_task_controls()

    st.divider()

    render_marketplace()

    if run_requested:
        run_agent(
            task=task,
            budget=budget,
        )


if __name__ == "__main__":
    main()