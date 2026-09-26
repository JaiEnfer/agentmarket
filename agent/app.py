from __future__ import annotations

import json
import subprocess
from decimal import Decimal
from pathlib import Path
from typing import Any

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAYER_DIR = PROJECT_ROOT / "payer"

SERVICE_PRICE = Decimal("0.001")


def purchase_service() -> dict[str, Any]:
    """Execute the proven x402 payment adapter."""

    completed = subprocess.run(
        ["npm.cmd", "run", "start", "--silent"],
        cwd=PAYER_DIR,
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        error = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(error)

    stdout = completed.stdout.strip()

    if not stdout:
        raise RuntimeError("Payment adapter returned no response.")

    return json.loads(stdout)


st.set_page_config(
    page_title="AgentMarket",
    page_icon="⚡",
    layout="centered",
)

st.title("⚡ AgentMarket")

st.caption(
    "AI agents autonomously buying services with x402 on Monad"
)

st.markdown(
    """
**Give the agent a task and a budget.**

AgentMarket discovers a paid service, checks whether the
purchase fits its budget, and pays for it autonomously.
"""
)

task = st.text_input(
    "Task",
    value="Research ETH market sentiment",
)

budget_input = st.number_input(
    "Maximum budget (USDC)",
    min_value=0.0,
    value=0.01,
    step=0.001,
    format="%.3f",
)

st.divider()

st.subheader("Available service")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Crypto Research Agent",
        "$0.001 USDC",
    )

with col2:
    st.metric(
        "Network",
        "Monad",
    )

if st.button(
    "Run autonomous agent",
    type="primary",
    use_container_width=True,
):
    budget = Decimal(str(budget_input))

    st.markdown("### Agent activity")

    st.write("🔎 **Discovering services...**")

    st.write(
        "💰 Found `Crypto Research Agent` — "
        "**$0.001 USDC**"
    )

    if SERVICE_PRICE > budget:
        st.error(
            "Purchase refused: service exceeds the "
            "agent's spending budget."
        )

    else:
        st.success(
            f"Budget check passed: "
            f"${SERVICE_PRICE} ≤ ${budget}"
        )

        st.info(
            "HTTP 402 received — payment required."
        )

        with st.spinner(
            "Agent is paying $0.001 USDC via x402 on Monad..."
        ):
            try:
                payment = purchase_service()
            except Exception as exc:
                st.error(f"Payment failed: {exc}")
                st.stop()

        if payment.get("success") is not True:
            st.error("Payment adapter reported failure.")
            st.stop()

        st.success("Payment settled. Service unlocked.")

        purchased = payment["data"]
        result = purchased["result"]

        st.markdown("### Purchased intelligence")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Asset",
            result["asset"],
        )

        c2.metric(
            "Sentiment",
            result["sentiment"].title(),
        )

        c3.metric(
            "Confidence",
            f"{float(result['confidence']) * 100:.0f}%",
        )

        spent = Decimal(payment["amount"])

        st.markdown("### Transaction")

        st.code(
            "\n".join(
                [
                    f"Payer:    {payment['payer']}",
                    f"Spent:    {spent} {payment['currency']}",
                    f"Network:  {payment['network']}",
                    f"Budget:   {budget} USDC",
                    f"Remaining:{budget - spent} USDC",
                ]
            )
        )

        st.caption(
            "The service result was returned only after "
            "the x402 payment completed."
        )