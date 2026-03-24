"""Tests for gaming partner calculator_engine.py"""

import pytest
from calculator_engine import DealTerms, BonusTier, compute_bonus, compute_financials


def make_terms(**overrides) -> DealTerms:
    defaults = dict(
        partner_name="Test Partner",
        monthly_new_players=10000,
        cost_per_player=8.0,
        monthly_spend_per_player=25.0,
        player_retention_months=6.0,
        profit_share_pct=15.0,
        contract_duration_months=12,
        bonus_tiers=[],
    )
    defaults.update(overrides)
    return DealTerms(**defaults)


class TestBasicFinancials:
    def test_active_players(self):
        f = compute_financials(make_terms(monthly_new_players=10000, player_retention_months=6))
        assert f.active_players == 60_000

    def test_monthly_revenue(self):
        f = compute_financials(make_terms())
        # 10k players * 6 months retention * $25 ARPU = $1,500,000
        assert f.monthly_revenue == 1_500_000.0

    def test_monthly_cpa_cost(self):
        f = compute_financials(make_terms())
        # 10k * $8 = $80,000
        assert f.monthly_cpa_cost == 80_000.0

    def test_monthly_profit_share(self):
        f = compute_financials(make_terms())
        # $1,500,000 * 15% = $225,000
        assert f.monthly_profit_share == 225_000.0

    def test_monthly_profit(self):
        f = compute_financials(make_terms())
        # revenue ($1.5M) - CPA ($80k) - profit share ($225k) = $1,195,000
        assert f.monthly_profit == 1_195_000.0

    def test_margin(self):
        f = compute_financials(make_terms())
        # $1,195,000 / $1,500,000 = 79.67%
        assert round(f.margin_pct, 2) == 79.67


class TestLTV:
    def test_ltv_per_player(self):
        f = compute_financials(make_terms(monthly_spend_per_player=25, player_retention_months=6))
        assert f.ltv_per_player == 150.0

    def test_cac(self):
        f = compute_financials(make_terms(cost_per_player=8))
        assert f.cac == 8.0

    def test_ltv_cac_ratio(self):
        f = compute_financials(make_terms(monthly_spend_per_player=25, player_retention_months=6, cost_per_player=8))
        # LTV=150, CAC=8, ratio=18.75
        assert f.ltv_cac_ratio == 18.75

    def test_ltv_cac_zero_cac(self):
        f = compute_financials(make_terms(cost_per_player=0))
        assert f.ltv_cac_ratio is None


class TestBonusTiers:
    def test_no_tiers(self):
        assert compute_bonus(1_000_000, []) == 0.0

    def test_below_all_tiers(self):
        tiers = [BonusTier(revenue_threshold=500_000, bonus_pct=2)]
        assert compute_bonus(400_000, tiers) == 0.0

    def test_single_tier(self):
        tiers = [BonusTier(revenue_threshold=500_000, bonus_pct=2)]
        # Revenue 1M: 500k above threshold * 2% = $10,000
        assert compute_bonus(1_000_000, tiers) == 10_000.0

    def test_multiple_tiers(self):
        tiers = [
            BonusTier(revenue_threshold=500_000, bonus_pct=2),
            BonusTier(revenue_threshold=1_500_000, bonus_pct=3),
            BonusTier(revenue_threshold=5_000_000, bonus_pct=5),
        ]
        # Revenue = 2M
        # Band 500k-1.5M: 1M * 2% = $20,000
        # Band 1.5M-2M: 500k * 3% = $15,000
        # Total: $35,000
        assert compute_bonus(2_000_000, tiers) == 35_000.0

    def test_exceeds_all_tiers(self):
        tiers = [
            BonusTier(revenue_threshold=500_000, bonus_pct=2),
            BonusTier(revenue_threshold=1_500_000, bonus_pct=3),
        ]
        # Revenue = 3M
        # Band 500k-1.5M: 1M * 2% = $20,000
        # Band 1.5M+: 1.5M * 3% = $45,000
        # Total: $65,000
        assert compute_bonus(3_000_000, tiers) == 65_000.0

    def test_bonus_in_financials(self):
        terms = make_terms(
            monthly_new_players=10000,
            monthly_spend_per_player=25,
            player_retention_months=6,
            bonus_tiers=[BonusTier(revenue_threshold=500_000, bonus_pct=2)],
        )
        f = compute_financials(terms)
        # Revenue = $1.5M, bonus = (1.5M - 500k) * 2% = $20,000
        assert f.monthly_bonus == 20_000.0


class TestContractTotals:
    def test_total_contract_value(self):
        f = compute_financials(make_terms(contract_duration_months=12))
        assert f.total_contract_value == f.monthly_partner_cost * 12

    def test_total_profit(self):
        f = compute_financials(make_terms(contract_duration_months=12))
        assert f.total_profit == f.monthly_profit * 12

    def test_short_contract(self):
        f = compute_financials(make_terms(contract_duration_months=3))
        assert f.total_contract_value == f.monthly_partner_cost * 3


class TestEdgeCases:
    def test_zero_players(self):
        f = compute_financials(make_terms(monthly_new_players=0))
        assert f.monthly_revenue == 0.0
        assert f.monthly_profit == 0.0
        assert f.margin_pct == 0.0

    def test_zero_spend(self):
        f = compute_financials(make_terms(monthly_spend_per_player=0))
        assert f.monthly_revenue == 0.0
        assert f.ltv_per_player == 0.0

    def test_zero_retention(self):
        f = compute_financials(make_terms(player_retention_months=0))
        assert f.active_players == 0.0
        assert f.monthly_revenue == 0.0
