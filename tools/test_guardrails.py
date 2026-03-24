"""Tests for guardrail_rules.py"""

import pytest
from calculator_engine import DealType, DealTerms, compute_financials
from guardrail_rules import BreachLevel, validate_guardrails


def make_terms(**overrides) -> DealTerms:
    defaults = dict(
        partner_name="Test Corp",
        deal_type=DealType.REV_SHARE,
        rev_share_pct=15.0,
        monthly_volume=1000,
        avg_deal_value=50.0,
        deal_duration_months=12,
        acquisition_cost=0.0,
    )
    defaults.update(overrides)
    return DealTerms(**defaults)


class TestRevShareGuardrails:
    def test_within_range(self):
        terms = make_terms(rev_share_pct=15.0)
        financials = compute_financials(terms)
        breaches = validate_guardrails(terms, financials)
        rev_breaches = [b for b in breaches if b.field == "rev_share_pct"]
        assert len(rev_breaches) == 0

    def test_below_min(self):
        terms = make_terms(rev_share_pct=2.0)
        financials = compute_financials(terms)
        breaches = validate_guardrails(terms, financials)
        rev_breaches = [b for b in breaches if b.field == "rev_share_pct"]
        assert len(rev_breaches) == 1
        assert rev_breaches[0].level == BreachLevel.WARNING

    def test_above_max(self):
        terms = make_terms(rev_share_pct=35.0)
        financials = compute_financials(terms)
        breaches = validate_guardrails(terms, financials)
        rev_breaches = [b for b in breaches if b.field == "rev_share_pct"]
        assert len(rev_breaches) == 1
        assert rev_breaches[0].level == BreachLevel.WARNING


class TestPaymentTermsGuardrails:
    def test_allowed(self):
        terms = make_terms(payment_terms="net_60")
        financials = compute_financials(terms)
        breaches = validate_guardrails(terms, financials)
        payment_breaches = [b for b in breaches if b.field == "payment_terms"]
        assert len(payment_breaches) == 0

    def test_blocked(self):
        terms = make_terms(payment_terms="net_120")
        financials = compute_financials(terms)
        breaches = validate_guardrails(terms, financials)
        payment_breaches = [b for b in breaches if b.field == "payment_terms"]
        assert len(payment_breaches) == 1
        assert payment_breaches[0].level == BreachLevel.HARD_BLOCK


class TestMarginGuardrails:
    def test_healthy_margin(self):
        terms = make_terms(rev_share_pct=15.0)  # 85% margin
        financials = compute_financials(terms)
        breaches = validate_guardrails(terms, financials)
        margin_breaches = [b for b in breaches if b.field == "margin_pct"]
        assert len(margin_breaches) == 0

    def test_low_margin(self):
        terms = make_terms(rev_share_pct=85.0)  # 15% margin
        financials = compute_financials(terms)
        breaches = validate_guardrails(terms, financials)
        margin_breaches = [b for b in breaches if b.field == "margin_pct"]
        assert len(margin_breaches) == 1
        assert margin_breaches[0].level == BreachLevel.WARNING


class TestDealValueGuardrails:
    def test_within_threshold(self):
        terms = make_terms(rev_share_pct=10.0, deal_duration_months=12)
        financials = compute_financials(terms)
        breaches = validate_guardrails(terms, financials)
        value_breaches = [b for b in breaches if b.field == "total_deal_value"]
        assert len(value_breaches) == 0

    def test_exceeds_threshold(self):
        terms = make_terms(
            rev_share_pct=25.0,
            monthly_volume=5000,
            avg_deal_value=100.0,
            deal_duration_months=24,
        )
        financials = compute_financials(terms)
        # 5000 * 100 * 25% = 125,000/mo * 24 = 3,000,000
        breaches = validate_guardrails(terms, financials)
        value_breaches = [b for b in breaches if b.field == "total_deal_value"]
        assert len(value_breaches) == 1


class TestCleanDeal:
    def test_no_breaches(self):
        terms = make_terms(
            rev_share_pct=15.0,
            deal_duration_months=12,
            payment_terms="net_30",
        )
        financials = compute_financials(terms)
        breaches = validate_guardrails(terms, financials)
        assert len(breaches) == 0
