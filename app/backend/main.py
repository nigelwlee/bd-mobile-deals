"""
FastAPI backend for Gaming Partner Deal Calculator.
"""

from __future__ import annotations

import sys
import os
from typing import Optional, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))

from calculator_engine import DealTerms, BonusTier, compute_financials
from guardrail_rules import validate_guardrails, GUARDRAILS

app = FastAPI(title="Gaming Partner Deal Calculator API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BonusTierInput(BaseModel):
    revenue_threshold: float
    bonus_pct: float


class CalculateRequest(BaseModel):
    partner_name: str = ""
    monthly_new_players: int = 0
    cost_per_player: float = 0.0
    monthly_spend_per_player: float = 0.0
    player_retention_months: float = 6.0
    profit_share_pct: float = 0.0
    contract_duration_months: int = 12
    bonus_tiers: List[BonusTierInput] = []


class FinancialsResponse(BaseModel):
    monthly_new_players: int
    active_players: float
    monthly_revenue: float
    monthly_cpa_cost: float
    monthly_profit_share: float
    monthly_bonus: float
    monthly_partner_cost: float
    monthly_profit: float
    margin_pct: float
    ltv_per_player: float
    cac: float
    ltv_cac_ratio: Optional[float]
    total_contract_value: float
    total_revenue: float
    total_profit: float


class BreachResponse(BaseModel):
    field: str
    level: str
    message: str


class CalculateResponse(BaseModel):
    financials: FinancialsResponse
    guardrail_breaches: List[BreachResponse]


@app.post("/api/calculate", response_model=CalculateResponse)
def calculate(req: CalculateRequest):
    terms = DealTerms(
        partner_name=req.partner_name,
        monthly_new_players=req.monthly_new_players,
        cost_per_player=req.cost_per_player,
        monthly_spend_per_player=req.monthly_spend_per_player,
        player_retention_months=req.player_retention_months,
        profit_share_pct=req.profit_share_pct,
        contract_duration_months=req.contract_duration_months,
        bonus_tiers=[
            BonusTier(revenue_threshold=t.revenue_threshold, bonus_pct=t.bonus_pct)
            for t in req.bonus_tiers
        ],
    )

    financials = compute_financials(terms)
    breaches = validate_guardrails(terms, financials)

    return CalculateResponse(
        financials=FinancialsResponse(
            monthly_new_players=financials.monthly_new_players,
            active_players=financials.active_players,
            monthly_revenue=financials.monthly_revenue,
            monthly_cpa_cost=financials.monthly_cpa_cost,
            monthly_profit_share=financials.monthly_profit_share,
            monthly_bonus=financials.monthly_bonus,
            monthly_partner_cost=financials.monthly_partner_cost,
            monthly_profit=financials.monthly_profit,
            margin_pct=financials.margin_pct,
            ltv_per_player=financials.ltv_per_player,
            cac=financials.cac,
            ltv_cac_ratio=financials.ltv_cac_ratio,
            total_contract_value=financials.total_contract_value,
            total_revenue=financials.total_revenue,
            total_profit=financials.total_profit,
        ),
        guardrail_breaches=[
            BreachResponse(field=b.field, level=b.level.value, message=b.message)
            for b in breaches
        ],
    )


@app.get("/api/guardrails")
def get_guardrails():
    return GUARDRAILS


@app.get("/api/health")
def health():
    return {"status": "ok"}
