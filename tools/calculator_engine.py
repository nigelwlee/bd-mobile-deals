"""
Deal Calculator Engine
Source of truth for all deal financial computations.
"""

from __future__ import annotations

import math
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List


class DealType(str, Enum):
    REV_SHARE = "rev_share"
    FLAT_FEE = "flat_fee"
    HYBRID = "hybrid"
    TIERED = "tiered"
    USAGE_BASED = "usage_based"


@dataclass
class TierRate:
    volume_min: int
    volume_max: Optional[int]  # None = unlimited
    rate_pct: float


@dataclass
class DealTerms:
    partner_name: str = ""
    deal_type: DealType = DealType.REV_SHARE
    rev_share_pct: float = 0.0           # e.g. 15.0 for 15%
    flat_fee_monthly: float = 0.0        # e.g. 5000.0
    tiered_rates: List[TierRate] = field(default_factory=list)
    per_unit_rate: float = 0.0           # for usage-based
    deal_duration_months: int = 12
    geo_scope: List[str] = field(default_factory=lambda: ["Global"])
    exclusivity: bool = False
    payment_terms: str = "net_30"
    monthly_volume: int = 0
    avg_deal_value: float = 0.0          # revenue per unit
    acquisition_cost: float = 0.0        # one-time partner onboarding cost


@dataclass
class DealFinancials:
    gross_monthly_revenue: float = 0.0
    monthly_partner_payout: float = 0.0
    monthly_net_revenue: float = 0.0
    margin_pct: float = 0.0
    annual_partner_payout: float = 0.0
    annual_net_revenue: float = 0.0
    total_deal_value: float = 0.0        # total partner payout over term
    total_net_revenue: float = 0.0       # total net revenue over term
    breakeven_months: Optional[int] = None


def compute_gross_monthly_revenue(terms: DealTerms) -> float:
    return terms.monthly_volume * terms.avg_deal_value


def compute_monthly_partner_payout(terms: DealTerms, gross_monthly: float) -> float:
    if terms.deal_type == DealType.REV_SHARE:
        return gross_monthly * (terms.rev_share_pct / 100.0)

    elif terms.deal_type == DealType.FLAT_FEE:
        return terms.flat_fee_monthly

    elif terms.deal_type == DealType.HYBRID:
        rev_share_portion = gross_monthly * (terms.rev_share_pct / 100.0)
        return rev_share_portion + terms.flat_fee_monthly

    elif terms.deal_type == DealType.TIERED:
        total_payout = 0.0
        remaining_volume = terms.monthly_volume
        for tier in sorted(terms.tiered_rates, key=lambda t: t.volume_min):
            if remaining_volume <= 0:
                break
            tier_max = tier.volume_max if tier.volume_max is not None else float('inf')
            tier_capacity = tier_max - tier.volume_min
            tier_volume = min(remaining_volume, tier_capacity)
            tier_revenue = tier_volume * terms.avg_deal_value
            total_payout += tier_revenue * (tier.rate_pct / 100.0)
            remaining_volume -= tier_volume
        return total_payout

    elif terms.deal_type == DealType.USAGE_BASED:
        return terms.monthly_volume * terms.per_unit_rate

    return 0.0


def compute_financials(terms: DealTerms) -> DealFinancials:
    gross_monthly = compute_gross_monthly_revenue(terms)
    monthly_payout = compute_monthly_partner_payout(terms, gross_monthly)
    monthly_net = gross_monthly - monthly_payout
    margin = (monthly_net / gross_monthly * 100.0) if gross_monthly > 0 else 0.0

    annual_payout = monthly_payout * min(terms.deal_duration_months, 12)
    annual_net = monthly_net * min(terms.deal_duration_months, 12)
    total_deal_value = monthly_payout * terms.deal_duration_months
    total_net = monthly_net * terms.deal_duration_months

    breakeven = None
    if monthly_net > 0 and terms.acquisition_cost > 0:
        breakeven = math.ceil(terms.acquisition_cost / monthly_net)
    elif terms.acquisition_cost == 0 and monthly_net > 0:
        breakeven = 0

    return DealFinancials(
        gross_monthly_revenue=round(gross_monthly, 2),
        monthly_partner_payout=round(monthly_payout, 2),
        monthly_net_revenue=round(monthly_net, 2),
        margin_pct=round(margin, 2),
        annual_partner_payout=round(annual_payout, 2),
        annual_net_revenue=round(annual_net, 2),
        total_deal_value=round(total_deal_value, 2),
        total_net_revenue=round(total_net, 2),
        breakeven_months=breakeven,
    )
