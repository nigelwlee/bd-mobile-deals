# Calculator Build Plan

**Created:** 2026-03-23
**Status:** In Progress

---

## Build Order

### Step 1: Calculator Engine (Python) -- IN PROGRESS
- `tools/calculator_engine.py` — all payout formulas (rev share, flat fee, hybrid, tiered, usage-based)
- `tools/guardrail_rules.py` — guardrail validation logic
- `tools/test_calculator.py` + `tools/test_guardrails.py` — unit tests
- Validate formulas are correct before any UI work

### Step 2: Backend API (FastAPI)
- Lightweight API that wraps the calculator engine
- POST endpoint: receives deal terms → returns computed financials + guardrail violations
- Serves the React frontend

### Step 3: Calculator UI (React)
- Mobile-first web app
- Input form: all deal term fields (dropdowns, sliders, number inputs)
- Output panel: real-time financial projections
- Guardrail indicators (green/yellow/red)
- Finalize button → saves deal summary

### Step 4: NLP Extraction (prompt + eval) — FUTURE
- `tools/nlp_extraction_prompt.txt` — LLM prompt for term extraction
- `tools/nlp_schema.json` — expected output schema
- Test against sample transcripts, measure accuracy

### Step 5: Upload + Transcription Flow — FUTURE
- Audio upload UI
- Speech-to-text integration (Whisper API)
- Wire NLP extraction → auto-populate calculator

### Step 6: Finalize Flow — FUTURE
- Lock deal, save to DB, export summary

---

## Notes
- Steps 1-3 first: working calculator app (no NLP yet)
- Calculator details to be refined after initial visual sample
- Formulas are placeholder — will be updated with real Deal Desk parameters
