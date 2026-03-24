"""
Gaming Channel Partner Deal Calculator Engine
Calculates economics for a player acquisition partnership deal.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class BonusTier:
    """When total monthly revenue crosses threshold, partner gets bonus_pct on revenue in that band."""
    revenue_threshold: float  # e.g. 500_000
    bonus_pct: float          # e.g. 2.0 for 2%


@dataclass
class DealTerms:
    partner_name: str = ""
    monthly_new_players: int = 0
    cost_per_player: float = 0.0          # CPA paid to partner per acquired player
    monthly_spend_per_player: float = 0.0 # ARPU — avg in-game spend per player per month
    player_retention_months: float = 6.0  # avg months a player stays active
    profit_share_pct: float = 0.0         # % of revenue shared with partner (on top of CPA)
    contract_duration_months: int = 12
    bonus_tiers: List[BonusTier] = field(default_factory=list)


@dataclass
class DealFinancials:
    monthly_new_players: int = 0
    active_players: float = 0.0           # steady-state active player base
    monthly_revenue: float = 0.0          # gross monthly revenue at steady state
    monthly_cpa_cost: float = 0.0         # monthly CPA payout to partner
    monthly_profit_share: float = 0.0     # monthly rev share payout to partner
    monthly_bonus: float = 0.0            # monthly bonus tier payout
    monthly_partner_cost: float = 0.0     # total monthly payout to partner
    monthly_profit: float = 0.0           # our monthly profit after partner costs
    margin_pct: float = 0.0
    ltv_per_player: float = 0.0           # lifetime value of one acquired player
    cac: float = 0.0                      # cost to acquire one player
    ltv_cac_ratio: Optional[float] = None
    total_contract_value: float = 0.0     # total partner payout over contract life
    total_revenue: float = 0.0            # total revenue over contract life
    total_profit: float = 0.0             # total profit over contract life


def compute_bonus(monthly_revenue: float, tiers: List[BonusTier]) -> float:
    """Calculate tiered bonus on total monthly revenue (marginal rates)."""
    if not tiers:
        return 0.0

    sorted_tiers = sorted(tiers, key=lambda t: t.revenue_threshold)
    total_bonus = 0.0

    for i, tier in enumerate(sorted_tiers):
        if monthly_revenue <= tier.revenue_threshold:
            break
        # Revenue in this band
        ceiling = sorted_tiers[i + 1].revenue_threshold if i + 1 < len(sorted_tiers) else float('inf')
        band_revenue = min(monthly_revenue, ceiling) - tier.revenue_threshold
        total_bonus += band_revenue * (tier.bonus_pct / 100.0)

    return total_bonus


def compute_financials(terms: DealTerms) -> DealFinancials:
    # Steady-state active players (Little's law)
    active_players = terms.monthly_new_players * terms.player_retention_months

    # Monthly revenue from all active players
    monthly_revenue = active_players * terms.monthly_spend_per_player

    # Partner costs
    monthly_cpa_cost = terms.monthly_new_players * terms.cost_per_player
    monthly_profit_share = monthly_revenue * (terms.profit_share_pct / 100.0)
    monthly_bonus = compute_bonus(monthly_revenue, terms.bonus_tiers)
    monthly_partner_cost = monthly_cpa_cost + monthly_profit_share + monthly_bonus

    # Our profit
    monthly_profit = monthly_revenue - monthly_partner_cost
    margin_pct = (monthly_profit / monthly_revenue * 100.0) if monthly_revenue > 0 else 0.0

    # Per-player economics
    ltv = terms.monthly_spend_per_player * terms.player_retention_months
    cac = terms.cost_per_player
    ltv_cac = (ltv / cac) if cac > 0 else None

    # Contract totals (using steady-state monthly figures)
    total_contract_value = monthly_partner_cost * terms.contract_duration_months
    total_revenue = monthly_revenue * terms.contract_duration_months
    total_profit = monthly_profit * terms.contract_duration_months

    return DealFinancials(
        monthly_new_players=terms.monthly_new_players,
        active_players=round(active_players, 0),
        monthly_revenue=round(monthly_revenue, 2),
        monthly_cpa_cost=round(monthly_cpa_cost, 2),
        monthly_profit_share=round(monthly_profit_share, 2),
        monthly_bonus=round(monthly_bonus, 2),
        monthly_partner_cost=round(monthly_partner_cost, 2),
        monthly_profit=round(monthly_profit, 2),
        margin_pct=round(margin_pct, 2),
        ltv_per_player=round(ltv, 2),
        cac=round(cac, 2),
        ltv_cac_ratio=round(ltv_cac, 2) if ltv_cac is not None else None,
        total_contract_value=round(total_contract_value, 2),
        total_revenue=round(total_revenue, 2),
        total_profit=round(total_profit, 2),
    )
