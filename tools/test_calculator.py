"""Tests for calculator_engine.py"""

import pytest
from calculator_engine import (
    DealType, DealTerms, TierRate,
    compute_gross_monthly_revenue,
    compute_monthly_partner_payout,
    compute_financials,
)


def make_terms(**overrides) -> DealTerms:
    defaults = dict(
        partner_name="Test Corp",
        deal_type=DealType.REV_SHARE,
        rev_share_pct=15.0,
        monthly_volume=1000,
        avg_deal_value=50.0,
        deal_duration_months=12,
        acquisition_cost=10000.0,
    )
    defaults.update(overrides)
    return DealTerms(**defaults)


class TestGrossRevenue:
    def test_basic(self):
        terms = make_terms(monthly_volume=1000, avg_deal_value=50.0)
        assert compute_gross_monthly_revenue(terms) == 50_000.0

    def test_zero_volume(self):
        terms = make_terms(monthly_volume=0)
        assert compute_gross_monthly_revenue(terms) == 0.0

    def test_zero_value(self):
        terms = make_terms(avg_deal_value=0.0)
        assert compute_gross_monthly_revenue(terms) == 0.0


class TestRevShare:
    def test_basic(self):
        terms = make_terms(deal_type=DealType.REV_SHARE, rev_share_pct=15.0)
        gross = compute_gross_monthly_revenue(terms)  # 50,000
        payout = compute_monthly_partner_payout(terms, gross)
        assert payout == 7_500.0

    def test_full_financials(self):
        terms = make_terms(deal_type=DealType.REV_SHARE, rev_share_pct=20.0)
        f = compute_financials(terms)
        assert f.gross_monthly_revenue == 50_000.0
        assert f.monthly_partner_payout == 10_000.0
        assert f.monthly_net_revenue == 40_000.0
        assert f.margin_pct == 80.0
        assert f.annual_partner_payout == 120_000.0
        assert f.total_deal_value == 120_000.0


class TestFlatFee:
    def test_basic(self):
        terms = make_terms(deal_type=DealType.FLAT_FEE, flat_fee_monthly=5000.0)
        gross = compute_gross_monthly_revenue(terms)
        payout = compute_monthly_partner_payout(terms, gross)
        assert payout == 5_000.0

    def test_financials(self):
        terms = make_terms(deal_type=DealType.FLAT_FEE, flat_fee_monthly=5000.0)
        f = compute_financials(terms)
        assert f.monthly_partner_payout == 5_000.0
        assert f.monthly_net_revenue == 45_000.0
        assert f.margin_pct == 90.0


class TestHybrid:
    def test_basic(self):
        terms = make_terms(
            deal_type=DealType.HYBRID,
            rev_share_pct=10.0,
            flat_fee_monthly=2000.0,
        )
        gross = compute_gross_monthly_revenue(terms)  # 50,000
        payout = compute_monthly_partner_payout(terms, gross)
        assert payout == 7_000.0  # 5,000 (10% of 50k) + 2,000


class TestTiered:
    def test_basic(self):
        terms = make_terms(
            deal_type=DealType.TIERED,
            monthly_volume=500,
            avg_deal_value=50.0,
            tiered_rates=[
                TierRate(volume_min=0, volume_max=100, rate_pct=20.0),
                TierRate(volume_min=100, volume_max=500, rate_pct=15.0),
                TierRate(volume_min=500, volume_max=None, rate_pct=10.0),
            ],
        )
        gross = compute_gross_monthly_revenue(terms)  # 25,000
        payout = compute_monthly_partner_payout(terms, gross)
        # Tier 1: 100 units * $50 * 20% = $1,000
        # Tier 2: 400 units * $50 * 15% = $3,000
        # Total: $4,000
        assert payout == 4_000.0

    def test_exceeds_all_tiers(self):
        terms = make_terms(
            deal_type=DealType.TIERED,
            monthly_volume=1000,
            avg_deal_value=50.0,
            tiered_rates=[
                TierRate(volume_min=0, volume_max=100, rate_pct=20.0),
                TierRate(volume_min=100, volume_max=500, rate_pct=15.0),
                TierRate(volume_min=500, volume_max=None, rate_pct=10.0),
            ],
        )
        gross = compute_gross_monthly_revenue(terms)
        payout = compute_monthly_partner_payout(terms, gross)
        # Tier 1: 100 * $50 * 20% = $1,000
        # Tier 2: 400 * $50 * 15% = $3,000
        # Tier 3: 500 * $50 * 10% = $2,500
        # Total: $6,500
        assert payout == 6_500.0


class TestUsageBased:
    def test_basic(self):
        terms = make_terms(
            deal_type=DealType.USAGE_BASED,
            monthly_volume=1000,
            per_unit_rate=2.50,
        )
        gross = compute_gross_monthly_revenue(terms)
        payout = compute_monthly_partner_payout(terms, gross)
        assert payout == 2_500.0


class TestBreakeven:
    def test_basic(self):
        terms = make_terms(acquisition_cost=10_000.0)
        f = compute_financials(terms)
        # Net monthly = 50,000 - 7,500 = 42,500
        # Breakeven = ceil(10,000 / 42,500) = 1 month
        assert f.breakeven_months == 1

    def test_no_acquisition_cost(self):
        terms = make_terms(acquisition_cost=0.0)
        f = compute_financials(terms)
        assert f.breakeven_months == 0

    def test_high_acquisition_cost(self):
        terms = make_terms(acquisition_cost=200_000.0)
        f = compute_financials(terms)
        # Net monthly = 42,500. ceil(200,000/42,500) = 5
        assert f.breakeven_months == 5

    def test_zero_net_revenue(self):
        terms = make_terms(rev_share_pct=100.0, acquisition_cost=10_000.0)
        f = compute_financials(terms)
        assert f.breakeven_months is None


class TestDuration:
    def test_short_duration(self):
        terms = make_terms(deal_duration_months=6)
        f = compute_financials(terms)
        assert f.total_deal_value == f.monthly_partner_payout * 6
        assert f.annual_partner_payout == f.monthly_partner_payout * 6

    def test_long_duration(self):
        terms = make_terms(deal_duration_months=24)
        f = compute_financials(terms)
        assert f.total_deal_value == f.monthly_partner_payout * 24
        assert f.annual_partner_payout == f.monthly_partner_payout * 12
