from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Service:
    id: str
    name: str
    capability: str
    description: str
    price: Decimal
    keywords: tuple[str, ...]
    purchasable: bool = False


SERVICES = (
    Service(
        id="quick-research",
        name="Quick Research Agent",
        capability="Market sentiment",
        description="Fast crypto market sentiment research.",
        price=Decimal("0.001"),
        keywords=(
            "research",
            "sentiment",
            "market",
            "eth",
            "ethereum",
            "crypto",
        ),
        purchasable=True,
    ),
    Service(
        id="deep-research",
        name="Deep Research Agent",
        capability="Detailed research",
        description="Detailed analysis for complex research tasks.",
        price=Decimal("0.003"),
        keywords=(
            "deep",
            "detailed",
            "research",
            "analysis",
            "crypto",
        ),
    ),
    Service(
        id="risk-analysis",
        name="Risk Analysis Agent",
        capability="Risk analysis",
        description="Evaluates market and asset risk.",
        price=Decimal("0.002"),
        keywords=(
            "risk",
            "volatility",
            "exposure",
            "market",
            "crypto",
        ),
    ),
)


@dataclass(frozen=True)
class ServiceMatch:
    service: Service
    score: int


def discover_services(
    task: str,
) -> list[ServiceMatch]:
    """Rank marketplace services against the requested task."""

    normalized_task = task.lower()

    matches = []

    for service in SERVICES:
        score = sum(
            1
            for keyword in service.keywords
            if keyword in normalized_task
        )

        matches.append(
            ServiceMatch(
                service=service,
                score=score,
            )
        )

    return sorted(
        matches,
        key=lambda match: (
            -match.score,
            match.service.price,
        ),
    )


def select_service(
    task: str,
    budget: Decimal,
) -> tuple[Service | None, list[ServiceMatch]]:
    """
    Select the highest-relevance affordable service.

    Price is used as a tie-breaker when multiple services
    have equal relevance.
    """

    matches = discover_services(task)

    candidates = [
        match
        for match in matches
        if match.score > 0
        and match.service.price <= budget
        and match.service.purchasable
    ]

    if not candidates:
        return None, matches

    return candidates[0].service, matches