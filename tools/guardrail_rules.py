"""
Guardrail Rules for Gaming Partner Deals
Boundaries to flag risky deal terms.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List

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


GUARDRAILS = {
    "cost_per_player": {"min": 0.50, "max": 50.0, "level": "warning"},
    "profit_share_pct": {"min": 5.0, "max": 40.0, "level": "warning"},
    "contract_duration_months": {"min": 3, "max": 36, "level": "warning"},
    "ltv_cac_ratio": {"min": 3.0, "level": "warning"},
    "margin_pct": {"min": 30.0, "level": "warning"},
    "total_contract_value": {"max": 10_000_000.0, "level": "warning"},
}


def validate_guardrails(terms: DealTerms, financials: DealFinancials) -> list[GuardrailBreach]:
    breaches = []

    # CPA bounds
    if terms.cost_per_player > 0:
        g = GUARDRAILS["cost_per_player"]
        if terms.cost_per_player < g["min"]:
            breaches.append(GuardrailBreach(
                field="cost_per_player", level=BreachLevel.WARNING,
                message=f"CPA ${terms.cost_per_player:.2f} is below minimum ${g['min']:.2f}",
                current_value=terms.cost_per_player, min_value=g["min"], max_value=g["max"],
            ))
        elif terms.cost_per_player > g["max"]:
            breaches.append(GuardrailBreach(
                field="cost_per_player", level=BreachLevel.WARNING,
                message=f"CPA ${terms.cost_per_player:.2f} exceeds maximum ${g['max']:.2f}",
                current_value=terms.cost_per_player, min_value=g["min"], max_value=g["max"],
            ))

    # Profit share bounds
    if terms.profit_share_pct > 0:
        g = GUARDRAILS["profit_share_pct"]
        if terms.profit_share_pct < g["min"]:
            breaches.append(GuardrailBreach(
                field="profit_share_pct", level=BreachLevel.WARNING,
                message=f"Profit share {terms.profit_share_pct}% is below minimum {g['min']}%",
                current_value=terms.profit_share_pct, min_value=g["min"], max_value=g["max"],
            ))
        elif terms.profit_share_pct > g["max"]:
            breaches.append(GuardrailBreach(
                field="profit_share_pct", level=BreachLevel.WARNING,
                message=f"Profit share {terms.profit_share_pct}% exceeds maximum {g['max']}%",
                current_value=terms.profit_share_pct, min_value=g["min"], max_value=g["max"],
            ))

    # Contract duration
    g = GUARDRAILS["contract_duration_months"]
    if terms.contract_duration_months < g["min"]:
        breaches.append(GuardrailBreach(
            field="contract_duration_months", level=BreachLevel.WARNING,
            message=f"Duration {terms.contract_duration_months}mo is below minimum {g['min']}mo",
            current_value=terms.contract_duration_months, min_value=g["min"], max_value=g["max"],
        ))
    elif terms.contract_duration_months > g["max"]:
        breaches.append(GuardrailBreach(
            field="contract_duration_months", level=BreachLevel.WARNING,
            message=f"Duration {terms.contract_duration_months}mo exceeds maximum {g['max']}mo",
            current_value=terms.contract_duration_months, min_value=g["min"], max_value=g["max"],
        ))

    # LTV/CAC ratio
    if financials.ltv_cac_ratio is not None:
        g = GUARDRAILS["ltv_cac_ratio"]
        if financials.ltv_cac_ratio < g["min"]:
            breaches.append(GuardrailBreach(
                field="ltv_cac_ratio", level=BreachLevel.WARNING,
                message=f"LTV/CAC ratio {financials.ltv_cac_ratio:.1f}x is below minimum {g['min']}x",
                current_value=financials.ltv_cac_ratio, min_value=g["min"],
            ))

    # Margin
    if financials.monthly_revenue > 0 and financials.margin_pct < GUARDRAILS["margin_pct"]["min"]:
        g = GUARDRAILS["margin_pct"]
        breaches.append(GuardrailBreach(
            field="margin_pct", level=BreachLevel.WARNING,
            message=f"Margin {financials.margin_pct:.1f}% is below minimum {g['min']}%",
            current_value=financials.margin_pct, min_value=g["min"],
        ))

    # Total contract value
    g = GUARDRAILS["total_contract_value"]
    if financials.total_contract_value > g["max"]:
        breaches.append(GuardrailBreach(
            field="total_contract_value", level=BreachLevel.WARNING,
            message=f"Total contract value ${financials.total_contract_value:,.0f} exceeds ${g['max']:,.0f} threshold",
            current_value=financials.total_contract_value, max_value=g["max"],
        ))

    return breaches
