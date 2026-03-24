"""
FastAPI backend for Deal Calculator.
Thin wrapper around tools/calculator_engine.py and tools/guardrail_rules.py.
"""

from __future__ import annotations

import sys
import os
from typing import Optional, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add tools/ to path so we can import the engine
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))

from calculator_engine import (
    DealType,
    DealTerms,
    TierRate,
    compute_financials,
)
from guardrail_rules import (
    validate_guardrails,
    GUARDRAILS,
)

app = FastAPI(title="Deal Calculator API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # POC only — lock down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request / Response models ---

class TierRateInput(BaseModel):
    volume_min: int
    volume_max: Optional[int] = None
    rate_pct: float


class CalculateRequest(BaseModel):
    partner_name: str = ""
    deal_type: str = "rev_share"
    rev_share_pct: float = 0.0
    flat_fee_monthly: float = 0.0
    tiered_rates: List[TierRateInput] = []
    per_unit_rate: float = 0.0
    deal_duration_months: int = 12
    geo_scope: List[str] = ["Global"]
    exclusivity: bool = False
    payment_terms: str = "net_30"
    monthly_volume: int = 0
    avg_deal_value: float = 0.0
    acquisition_cost: float = 0.0


class FinancialsResponse(BaseModel):
    gross_monthly_revenue: float
    monthly_partner_payout: float
    monthly_net_revenue: float
    margin_pct: float
    annual_partner_payout: float
    annual_net_revenue: float
    total_deal_value: float
    total_net_revenue: float
    breakeven_months: Optional[int]


class BreachResponse(BaseModel):
    field: str
    level: str
    message: str


class CalculateResponse(BaseModel):
    financials: FinancialsResponse
    guardrail_breaches: List[BreachResponse]


# --- Endpoints ---

@app.post("/api/calculate", response_model=CalculateResponse)
def calculate(req: CalculateRequest):
    terms = DealTerms(
        partner_name=req.partner_name,
        deal_type=DealType(req.deal_type),
        rev_share_pct=req.rev_share_pct,
        flat_fee_monthly=req.flat_fee_monthly,
        tiered_rates=[
            TierRate(
                volume_min=t.volume_min,
                volume_max=t.volume_max,
                rate_pct=t.rate_pct,
            )
            for t in req.tiered_rates
        ],
        per_unit_rate=req.per_unit_rate,
        deal_duration_months=req.deal_duration_months,
        geo_scope=req.geo_scope,
        exclusivity=req.exclusivity,
        payment_terms=req.payment_terms,
        monthly_volume=req.monthly_volume,
        avg_deal_value=req.avg_deal_value,
        acquisition_cost=req.acquisition_cost,
    )

    financials = compute_financials(terms)
    breaches = validate_guardrails(terms, financials)

    return CalculateResponse(
        financials=FinancialsResponse(
            gross_monthly_revenue=financials.gross_monthly_revenue,
            monthly_partner_payout=financials.monthly_partner_payout,
            monthly_net_revenue=financials.monthly_net_revenue,
            margin_pct=financials.margin_pct,
            annual_partner_payout=financials.annual_partner_payout,
            annual_net_revenue=financials.annual_net_revenue,
            total_deal_value=financials.total_deal_value,
            total_net_revenue=financials.total_net_revenue,
            breakeven_months=financials.breakeven_months,
        ),
        guardrail_breaches=[
            BreachResponse(
                field=b.field,
                level=b.level.value,
                message=b.message,
            )
            for b in breaches
        ],
    )


@app.get("/api/guardrails")
def get_guardrails():
    """Returns current guardrail configuration."""
    return GUARDRAILS


@app.get("/api/health")
def health():
    return {"status": "ok"}
