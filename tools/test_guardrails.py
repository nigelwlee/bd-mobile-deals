"""Tests for gaming partner guardrail_rules.py"""

import pytest
from calculator_engine import DealTerms, BonusTier, compute_financials
from guardrail_rules import BreachLevel, validate_guardrails


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


class TestCPAGuardrails:
    def test_within_range(self):
        terms = make_terms(cost_per_player=8.0)
        financials = compute_financials(terms)
        breaches = [b for b in validate_guardrails(terms, financials) if b.field == "cost_per_player"]
        assert len(breaches) == 0

    def test_below_min(self):
        terms = make_terms(cost_per_player=0.10)
        financials = compute_financials(terms)
        breaches = [b for b in validate_guardrails(terms, financials) if b.field == "cost_per_player"]
        assert len(breaches) == 1
        assert breaches[0].level == BreachLevel.WARNING

    def test_above_max(self):
        terms = make_terms(cost_per_player=100.0)
        financials = compute_financials(terms)
        breaches = [b for b in validate_guardrails(terms, financials) if b.field == "cost_per_player"]
        assert len(breaches) == 1


class TestProfitShareGuardrails:
    def test_within_range(self):
        terms = make_terms(profit_share_pct=15.0)
        financials = compute_financials(terms)
        breaches = [b for b in validate_guardrails(terms, financials) if b.field == "profit_share_pct"]
        assert len(breaches) == 0

    def test_above_max(self):
        terms = make_terms(profit_share_pct=45.0)
        financials = compute_financials(terms)
        breaches = [b for b in validate_guardrails(terms, financials) if b.field == "profit_share_pct"]
        assert len(breaches) == 1


class TestLTVCACGuardrails:
    def test_healthy_ratio(self):
        # LTV=150, CAC=8 => ratio=18.75
        terms = make_terms()
        financials = compute_financials(terms)
        breaches = [b for b in validate_guardrails(terms, financials) if b.field == "ltv_cac_ratio"]
        assert len(breaches) == 0

    def test_low_ratio(self):
        # LTV = 5*1 = 5, CAC = 8 => ratio = 0.625
        terms = make_terms(monthly_spend_per_player=1.0, player_retention_months=5, cost_per_player=8.0)
        financials = compute_financials(terms)
        breaches = [b for b in validate_guardrails(terms, financials) if b.field == "ltv_cac_ratio"]
        assert len(breaches) == 1


class TestMarginGuardrails:
    def test_healthy_margin(self):
        terms = make_terms()
        financials = compute_financials(terms)
        breaches = [b for b in validate_guardrails(terms, financials) if b.field == "margin_pct"]
        assert len(breaches) == 0

    def test_low_margin(self):
        # Very high profit share eats margin
        terms = make_terms(profit_share_pct=50.0, cost_per_player=40.0)
        financials = compute_financials(terms)
        breaches = [b for b in validate_guardrails(terms, financials) if b.field == "margin_pct"]
        assert len(breaches) == 1


class TestCleanDeal:
    def test_no_breaches(self):
        terms = make_terms()
        financials = compute_financials(terms)
        breaches = validate_guardrails(terms, financials)
        assert len(breaches) == 0
