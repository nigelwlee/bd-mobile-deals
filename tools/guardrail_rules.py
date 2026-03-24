"""
Guardrail Rules
Deal Desk-defined boundaries for deal parameters.
Placeholder values — replace with actuals from Deal Desk.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union, List

from calculator_engine import DealTerms, DealFinancials


class BreachLevel(str, Enum):
    OK = "ok"
    WARNING = "warning"
    HARD_BLOCK = "hard_block"


@dataclass
class GuardrailBreach:
    field: str
    level: BreachLevel
    message: str
    current_value: float | str
    min_value: Optional[float | str] = None
    max_value: Optional[float | str] = None


# --- Guardrail definitions (Deal Desk to provide real values) ---

GUARDRAILS = {
    "rev_share_pct": {"min": 5.0, "max": 30.0, "level": "warning"},
    "flat_fee_monthly": {"min": 500.0, "max": 25000.0, "level": "warning"},
    "deal_duration_months": {"min": 3, "max": 36, "level": "warning"},
    "payment_terms": {
        "allowed": ["net_30", "net_45", "net_60", "net_90"],
        "hard_block_beyond": "net_90",
        "level": "hard_block",
    },
    "total_deal_value": {"max": 1_000_000.0, "level": "warning"},
    "margin_pct": {"min": 20.0, "level": "warning"},
}

PAYMENT_TERMS_ORDER = ["net_30", "net_45", "net_60", "net_90"]


def validate_guardrails(terms: DealTerms, financials: DealFinancials) -> list[GuardrailBreach]:
    breaches = []

    # Rev share %
    if terms.rev_share_pct > 0:
        g = GUARDRAILS["rev_share_pct"]
        if terms.rev_share_pct < g["min"]:
            breaches.append(GuardrailBreach(
                field="rev_share_pct", level=BreachLevel.WARNING,
                message=f"Rev share {terms.rev_share_pct}% is below minimum {g['min']}%",
                current_value=terms.rev_share_pct, min_value=g["min"], max_value=g["max"],
            ))
        elif terms.rev_share_pct > g["max"]:
            breaches.append(GuardrailBreach(
                field="rev_share_pct", level=BreachLevel.WARNING,
                message=f"Rev share {terms.rev_share_pct}% exceeds maximum {g['max']}%",
                current_value=terms.rev_share_pct, min_value=g["min"], max_value=g["max"],
            ))

    # Flat fee
    if terms.flat_fee_monthly > 0:
        g = GUARDRAILS["flat_fee_monthly"]
        if terms.flat_fee_monthly < g["min"]:
            breaches.append(GuardrailBreach(
                field="flat_fee_monthly", level=BreachLevel.WARNING,
                message=f"Flat fee ${terms.flat_fee_monthly:,.0f}/mo is below minimum ${g['min']:,.0f}/mo",
                current_value=terms.flat_fee_monthly, min_value=g["min"], max_value=g["max"],
            ))
        elif terms.flat_fee_monthly > g["max"]:
            breaches.append(GuardrailBreach(
                field="flat_fee_monthly", level=BreachLevel.WARNING,
                message=f"Flat fee ${terms.flat_fee_monthly:,.0f}/mo exceeds maximum ${g['max']:,.0f}/mo",
                current_value=terms.flat_fee_monthly, min_value=g["min"], max_value=g["max"],
            ))

    # Deal duration
    g = GUARDRAILS["deal_duration_months"]
    if terms.deal_duration_months < g["min"]:
        breaches.append(GuardrailBreach(
            field="deal_duration_months", level=BreachLevel.WARNING,
            message=f"Duration {terms.deal_duration_months}mo is below minimum {g['min']}mo",
            current_value=terms.deal_duration_months, min_value=g["min"], max_value=g["max"],
        ))
    elif terms.deal_duration_months > g["max"]:
        breaches.append(GuardrailBreach(
            field="deal_duration_months", level=BreachLevel.WARNING,
            message=f"Duration {terms.deal_duration_months}mo exceeds maximum {g['max']}mo",
            current_value=terms.deal_duration_months, min_value=g["min"], max_value=g["max"],
        ))

    # Payment terms
    g = GUARDRAILS["payment_terms"]
    if terms.payment_terms not in g["allowed"]:
        breaches.append(GuardrailBreach(
            field="payment_terms", level=BreachLevel.HARD_BLOCK,
            message=f"Payment terms '{terms.payment_terms}' not allowed. Max is {g['hard_block_beyond']}.",
            current_value=terms.payment_terms,
        ))

    # Total deal value
    g = GUARDRAILS["total_deal_value"]
    if financials.total_deal_value > g["max"]:
        breaches.append(GuardrailBreach(
            field="total_deal_value", level=BreachLevel.WARNING,
            message=f"Total deal value ${financials.total_deal_value:,.0f} exceeds ${g['max']:,.0f} threshold",
            current_value=financials.total_deal_value, max_value=g["max"],
        ))

    # Margin
    g = GUARDRAILS["margin_pct"]
    if financials.gross_monthly_revenue > 0 and financials.margin_pct < g["min"]:
        breaches.append(GuardrailBreach(
            field="margin_pct", level=BreachLevel.WARNING,
            message=f"Margin {financials.margin_pct:.1f}% is below minimum {g['min']}%",
            current_value=financials.margin_pct, min_value=g["min"],
        ))

    return breaches
