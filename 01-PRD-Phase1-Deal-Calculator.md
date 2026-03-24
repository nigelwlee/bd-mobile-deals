# Phase 1 PRD: NLP-Powered Deal Calculator

**Version:** 0.1 (Draft)
**Last Updated:** 2026-03-23
**Status:** Active — fleshing out

---

## 1. What This Is

A standalone tool where a BD uploads a call recording and gets back structured deal terms + financial projections — ready to finalize in under 1 minute.

**Input:** Audio recording of a BD-partner conversation
**Output:** Finalized deal terms + computed financials (partner payout, net revenue, margin, breakeven)

---

## 2. User Flow

```
BD uploads audio recording (mp3/m4a/wav)
  │
  ▼
TRANSCRIBE — speech-to-text converts audio to transcript
  │
  ▼
EXTRACT — NLP/LLM pulls deal terms from transcript
  │  - Partner name
  │  - Deal type (rev share / flat fee / hybrid / tiered)
  │  - Percentages, rates, fees
  │  - Duration / term length
  │  - Geo scope, exclusivity
  │  - Payment terms
  │
  ▼
REVIEW — BD sees extracted terms with confidence scores
  │  - High confidence: green, pre-filled
  │  - Medium confidence: yellow, pre-filled but flagged
  │  - Low confidence: red, needs BD input
  │  - Not found: blank, BD fills manually
  │
  ▼
CALCULATE — BD edits terms; calculator updates financials in real-time
  │  - Projected partner payout (monthly + annual)
  │  - Net revenue to company
  │  - Margin %
  │  - Breakeven point
  │  - Total deal value over term
  │  - Guardrail warnings if terms are out of range
  │
  ▼
FINALIZE — BD locks in the deal; summary saved
```

---

## 3. Screens

### Screen 1: Upload
- Drag-and-drop or tap to select audio file
- Accepts: mp3, m4a, wav (max ~60 min / ~100MB)
- "Upload & Process" button
- Progress indicator while transcribing

### Screen 2: Review Extracted Terms
- Left column: raw transcript (scrollable, searchable)
- Right column: extracted fields in a form layout
- Each field shows:
  - Extracted value (editable)
  - Confidence badge (high / medium / low)
  - Source quote from transcript (highlighted, clickable to jump to context)
- "Looks good — go to Calculator" button
- "Re-extract" button (re-runs NLP if BD made manual transcript edits)

### Screen 3: Deal Calculator
- All deal term fields (pre-filled from extraction, fully editable)
- Financial outputs panel (updates in real-time as inputs change)
- Guardrail indicators (green = within range, yellow = warning, red = hard block)
- "Finalize Deal" button (disabled if hard-block guardrails are breached)

### Screen 4: Finalized Summary
- Read-only summary of all deal terms + financials
- "Edit" button to go back to calculator
- "Export" button (copy to clipboard / download as JSON — no PDF in Phase 1)
- "New Deal" button to start over

---

## 4. Deal Calculator — Detailed Specification

### 4.1 Input Fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| Partner name | Text | From NLP | Free text |
| Deal type | Dropdown | From NLP | Rev share / Flat fee / Hybrid / Tiered / Usage-based |
| Revenue share % | Slider (1-50%) + number input | From NLP | Only visible when deal type includes rev share |
| Flat fee | Currency input | From NLP | Only visible when deal type includes flat fee |
| Tiered rates | Editable table | From NLP | Rows: volume threshold → rate. Add/remove rows |
| Deal duration | Dropdown + custom | From NLP | 3mo / 6mo / 12mo / 24mo / 36mo / Custom (months) |
| Geo scope | Multi-select chips | From NLP | US, EU, APAC, LATAM, MEA, Global |
| Exclusivity | Toggle | From NLP | Yes / No. If Yes, scoped to selected geos |
| Payment terms | Dropdown | From NLP | Net 30 / Net 45 / Net 60 / Net 90 |
| Estimated monthly volume | Number input | From NLP or manual | Units per month |
| Average deal value | Currency input | From NLP or manual | Revenue per unit |
| Partner acquisition cost | Currency input | Manual | One-time cost to onboard partner (for breakeven) |

### 4.2 Output Fields (Computed)

| Output | Formula | Display |
|--------|---------|---------|
| **Gross monthly revenue** | Monthly volume x avg deal value | Currency |
| **Monthly partner payout** | *Depends on deal type (see 4.3)* | Currency |
| **Monthly net revenue** | Gross monthly revenue - monthly partner payout | Currency |
| **Margin %** | Monthly net revenue / gross monthly revenue x 100 | Percentage |
| **Annual partner payout** | Monthly partner payout x 12 | Currency |
| **Annual net revenue** | Monthly net revenue x 12 | Currency |
| **Total deal value** | Monthly partner payout x deal duration (months) | Currency |
| **Breakeven (months)** | Partner acquisition cost / monthly net revenue | Number (rounded up) |

### 4.3 Payout Formulas by Deal Type

**Revenue Share:**
```
monthly_partner_payout = gross_monthly_revenue x (rev_share_pct / 100)
```

**Flat Fee:**
```
monthly_partner_payout = flat_fee_per_month
```

**Hybrid (Rev Share + Flat Fee):**
```
monthly_partner_payout = (gross_monthly_revenue x (rev_share_pct / 100)) + flat_fee_per_month
```

**Tiered:**
```
For each tier (volume_min, volume_max, rate_pct):
  tier_volume = min(monthly_volume, volume_max) - volume_min
  tier_payout += tier_volume x avg_deal_value x (rate_pct / 100)
monthly_partner_payout = sum(tier_payouts)
```

**Usage-Based:**
```
monthly_partner_payout = monthly_volume x per_unit_rate
```

### 4.4 Guardrails

| Parameter | Min | Max | Breach Action |
|-----------|-----|-----|---------------|
| Rev share % | 5% | 30% | Yellow warning; BD can still proceed |
| Flat fee / month | $500 | $25,000 | Yellow warning; BD can still proceed |
| Deal duration | 3 months | 36 months | Yellow warning; BD can still proceed |
| Payment terms | Net 30 | Net 90 | Red hard block beyond Net 90 |
| Total deal value | — | $1,000,000 | Yellow warning above threshold |
| Margin % | 20% | — | Yellow warning if margin drops below 20% |

*(Placeholder values — Deal Desk to provide actuals before build)*

**Guardrail behavior:**
- **Yellow warning:** Field border turns yellow; tooltip explains the breach; BD can proceed but the deal is tagged as "outside guardrails"
- **Red hard block:** Field border turns red; "Finalize" button disabled; BD must adjust the term to proceed
- All breaches logged for Deal Desk visibility (future phase)

---

## 5. NLP Term Extraction — Detailed Specification

### 5.1 Pipeline

```
Audio file (mp3/m4a/wav)
  → Speech-to-text API (Whisper / Deepgram)
  → Raw transcript (timestamped)
  → LLM extraction prompt (structured output)
  → JSON of extracted deal terms + confidence scores + source quotes
```

### 5.2 Extraction Schema (LLM Output)

The LLM returns structured JSON:

```json
{
  "partner_name": {
    "value": "Acme Corp",
    "confidence": "high",
    "source_quote": "We're here with the Acme Corp team to discuss...",
    "timestamp": "00:01:23"
  },
  "deal_type": {
    "value": "rev_share",
    "confidence": "high",
    "source_quote": "We're thinking a revenue share model would work best...",
    "timestamp": "00:03:45"
  },
  "rev_share_pct": {
    "value": 17.5,
    "confidence": "medium",
    "source_quote": "somewhere around 15 to 20 percent",
    "range": [15, 20],
    "timestamp": "00:05:12"
  },
  "flat_fee": null,
  "deal_duration_months": {
    "value": 12,
    "confidence": "high",
    "source_quote": "for a 12-month initial term",
    "timestamp": "00:08:30"
  },
  "geo_scope": {
    "value": ["US", "EU"],
    "confidence": "medium",
    "source_quote": "focused on the US and European markets",
    "timestamp": "00:10:15"
  },
  "exclusivity": {
    "value": false,
    "confidence": "low",
    "source_quote": null,
    "timestamp": null
  },
  "payment_terms": {
    "value": "net_60",
    "confidence": "high",
    "source_quote": "we'd want net 60 payment terms",
    "timestamp": "00:12:45"
  },
  "monthly_volume": null,
  "avg_deal_value": null,
  "additional_notes": [
    "Partner mentioned wanting a performance bonus at 150% of target",
    "They asked about a ramp-up period for the first 3 months"
  ]
}
```

### 5.3 Confidence Scoring Rules

| Confidence | Criteria | UI Treatment |
|------------|----------|--------------|
| **High** | Exact value stated clearly in transcript | Green badge; auto-filled |
| **Medium** | Value implied or range given (e.g., "15 to 20%") | Yellow badge; auto-filled with midpoint; range shown |
| **Low** | Topic mentioned but no value given | Red badge; field flagged for manual input |
| **Null** | Not mentioned in transcript at all | Empty field; no badge |

### 5.4 Edge Cases

| Scenario | Handling |
|----------|----------|
| Multiple deal structures discussed | Extract primary; list alternatives in `additional_notes` |
| Conflicting terms (e.g., "15%... no wait, 20%") | Use the last-stated value; flag as medium confidence |
| Very short recording (< 2 min) | Warn BD that extraction may be incomplete |
| Non-English audio | Out of scope for POC; return error |
| Poor audio quality | STT will have low word-confidence; flag entire extraction as low confidence |
| No deal terms discussed | Return all nulls; show "No deal terms detected" message |

---

## 6. Technical Approach

| Component | Technology | Notes |
|-----------|------------|-------|
| **Frontend** | React (Next.js) or React Native | Mobile-first; responsive |
| **Speech-to-text** | OpenAI Whisper API | Best accuracy for conversational audio |
| **NLP extraction** | Claude API (structured output) | Reliable JSON extraction; good at nuance |
| **Calculator engine** | Python script (see `tools/`) | Precision matters — version-controlled formulas |
| **Backend API** | Python (FastAPI) | Lightweight; matches calculator language |
| **Database** | PostgreSQL | Deal records, guardrail configs |
| **File storage** | S3 / GCS | Audio files + transcripts |
| **Hosting** | Railway or GCP Cloud Run | Simple deploy for POC |

---

## 7. Open Questions

1. **Actual guardrail values from Deal Desk?** Need real min/max before build.
2. **What does "finalize" mean in Phase 1?** Just save locally? Export JSON? Email summary?
3. **Should the transcript be editable?** (BD corrects STT errors before NLP extraction)
4. **Max recording length?** 60 min is a guess — what's the longest BD call?
5. **Multi-speaker diarization needed?** (Identify who said what — BD vs. partner)
6. **Currency?** USD only for POC, or multi-currency?

---

## 8. Success Criteria

| Criteria | Target |
|----------|--------|
| Upload → finalized deal terms | < 1 minute (excluding transcription wait) |
| Transcription accuracy | > 90% word accuracy |
| NLP extraction accuracy | > 80% of fields correctly extracted (high/medium confidence) |
| Calculator correctness | 100% — formulas must match exactly |
| BD can edit any field | All extracted + computed fields are editable |
| Guardrail violations caught | 100% — no out-of-range terms slip through unnoticed |

---

*Phase 1 is the foundation. Everything else builds on top of this calculator + NLP pipeline.*
