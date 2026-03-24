# Way of Working

**Last Updated:** 2026-03-23

---

## 1. End-to-End Workflow

How we go from a raw recording to finalized deal terms — and who/what is responsible at each step.

```
┌─────────────────────────────────────────────────────────────────┐
│                        DEAL PIPELINE                            │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────────┐ │
│  │  INGEST  │──▶│ PROCESS  │──▶│  REVIEW  │──▶│  FINALIZE   │ │
│  └──────────┘   └──────────┘   └──────────┘   └─────────────┘ │
│                                                                 │
│  BD uploads     Transcribe +   BD reviews +   Lock terms +     │
│  recording      NLP extract    edits terms    compute finals   │
│                                                                 │
│  Agent:         Agent:         Agent:          Agent:           │
│  —              NLP Processor  Deal Maker      Deal & Risk      │
│                                                Analyst          │
│                                                                 │
│                                  ┌──────────┐                   │
│                                  │ APPROVE  │ (Future Phase)    │
│                                  └──────────┘                   │
│                                  Agent:                         │
│                                  Exec Sponsor                   │
│                                  + Legal                        │
└─────────────────────────────────────────────────────────────────┘
```

### Step-by-step

| Step | Action | Owner | Input | Output | Tools Used |
|------|--------|-------|-------|--------|------------|
| **1. Ingest** | BD uploads call recording (or auto-ingested from Google Drive in Phase 2) | BD Rep | Audio file (mp3/m4a/wav) | File stored; processing triggered | App upload UI / Google Drive API |
| **2. Transcribe** | Convert audio to text | NLP Processor agent | Audio file | Timestamped transcript | Speech-to-text API (Whisper) |
| **3. Extract** | Parse transcript for deal terms | NLP Processor agent | Transcript | Structured JSON: terms + confidence scores + source quotes | LLM extraction (Claude API) |
| **4. Populate** | Pre-fill calculator with extracted terms | System | Extraction JSON | Calculator fields populated | App logic |
| **5. Review** | BD reviews extracted terms, corrects errors, fills gaps | BD Rep (Deal Maker agent advises) | Pre-filled calculator | Validated deal terms | Calculator UI |
| **6. Simulate** | Calculator computes financials in real-time as BD adjusts | Deal & Risk Analyst agent | Deal terms | Projected payout, revenue, margin, breakeven | Calculator engine (Python) |
| **7. Guardrail check** | System checks all terms against Deal Desk boundaries | Deal & Risk Analyst agent | Deal terms + guardrail config | Warnings / blocks for out-of-range terms | Guardrail rules engine |
| **8. Finalize** | BD locks in deal terms and financials | BD Rep | Validated terms + computed financials | Finalized deal record | App finalize action |
| **9. Approve** | Deal Desk / Exec reviews non-standard deals | Exec Sponsor + Legal agents | Finalized deal | Approved / rejected / modified deal | *(Future phase — not in POC)* |
| **10. Contract** | Generate PDF from approved terms | Legal agent | Approved deal terms | Signed-ready contract PDF | *(Future phase — not in POC)* |

---

## 2. Tools

Specific methodologies, scripts, and engines that require precision and version control. These are not throwaway code — they are the source of truth for calculations and logic.

### 2.1 Calculator Engine (`tools/calculator_engine.py`)

**Why a separate Python script?** The calculator formulas must be exact and auditable. We don't want financial logic buried in frontend code or scattered across components. A single Python module serves as the source of truth.

**What it contains:**
- Payout formulas for each deal type (rev share, flat fee, hybrid, tiered, usage-based)
- Financial projection computations (monthly, annual, total deal value, margin, breakeven)
- Guardrail validation logic (min/max checks, breach classification)
- Input validation and edge case handling

**How it's used:**
- Backend API calls the engine for all calculations
- Frontend mirrors the logic for real-time updates (generated from the Python source)
- Unit tests validate every formula against known test cases
- Any formula change goes through code review

**Structure:**
```
tools/
├── calculator_engine.py        # Core formulas + computations
├── guardrail_rules.py          # Guardrail definitions + validation
├── test_calculator.py          # Unit tests for all formulas
├── test_guardrails.py          # Unit tests for guardrail logic
└── README.md                   # How to run, test, and modify
```

### 2.2 NLP Extraction Prompt (`tools/nlp_extraction_prompt.txt`)

**Why version-controlled?** The LLM prompt that extracts deal terms from transcripts is critical. Small prompt changes can drastically affect extraction accuracy. We track it like code.

**What it contains:**
- System prompt for the extraction LLM
- Output schema definition (JSON structure)
- Confidence scoring instructions
- Edge case handling instructions
- Example input/output pairs for few-shot prompting

**Structure:**
```
tools/
├── nlp_extraction_prompt.txt   # The prompt template
├── nlp_schema.json             # Expected output JSON schema
├── nlp_test_cases/             # Sample transcripts + expected extraction
│   ├── test_rev_share.txt
│   ├── test_flat_fee.txt
│   ├── test_hybrid.txt
│   ├── test_ambiguous.txt
│   └── expected_outputs/
└── nlp_eval.py                 # Script to run prompt against test cases and score accuracy
```

### 2.3 Guardrail Configuration (`tools/guardrail_rules.py`)

**Why separate?** Guardrails change based on Deal Desk policy. Keeping them in a standalone config/module means Deal Desk can update boundaries without touching calculator logic.

**What it contains:**
- Parameter definitions (which fields have guardrails)
- Min/max values per parameter
- Breach action type (warning vs. hard block)
- Validation function that takes a deal and returns all breaches

---

## 3. Agent Personas

Each agent represents a domain expert perspective applied at specific stages of the pipeline. In the POC, these are conceptual roles that guide how we build and validate. In future phases, some may become actual AI agents or human workflows.

### 3.1 NLP Processor

| Attribute | Detail |
|-----------|--------|
| **Role** | Converts raw audio into structured deal data |
| **Responsible for** | Transcription accuracy, term extraction accuracy, confidence scoring |
| **Domain expertise** | Speech recognition, natural language understanding, deal terminology |
| **Quality bar** | > 90% transcription word accuracy; > 80% field extraction accuracy |
| **Failure mode** | Returns null/low-confidence when uncertain — never guesses |
| **Tools owned** | `nlp_extraction_prompt.txt`, `nlp_schema.json`, `nlp_eval.py`, Speech-to-text API |
| **Active in** | Steps 2-3 (Transcribe + Extract) |

**Key behaviors:**
- Prefers precision over recall — better to leave a field blank than fill it wrong
- When a range is given (e.g., "15-20%"), extracts midpoint but surfaces the range
- Flags contradictions or ambiguities in `additional_notes`
- Handles multi-speaker conversations (attributes statements to BD vs. partner when possible)

---

### 3.2 Deal Maker

| Attribute | Detail |
|-----------|--------|
| **Role** | Represents the BD's perspective — helps structure a competitive deal |
| **Responsible for** | Ensuring extracted terms make commercial sense; suggesting adjustments |
| **Domain expertise** | Partnership structures, competitive deal benchmarks, negotiation patterns |
| **Quality bar** | Deal terms are commercially viable and attractive to partners |
| **Failure mode** | Defers to the BD's judgment — advises but never overrides |
| **Tools owned** | None directly — advises on calculator inputs |
| **Active in** | Step 5 (Review) |

**Key behaviors:**
- Surfaces when extracted terms seem unusual (e.g., 45% rev share is abnormally high)
- Suggests common deal structures if NLP extraction is sparse
- Highlights terms that are likely to be negotiation leverage points
- *(Future: could become an AI assistant that suggests deal optimizations in-app)*

---

### 3.3 Deal & Risk Analyst

| Attribute | Detail |
|-----------|--------|
| **Role** | Evaluates the financial health and risk profile of a deal |
| **Responsible for** | Accurate financial projections, guardrail enforcement, risk flagging |
| **Domain expertise** | Financial modeling, margin analysis, deal risk assessment |
| **Quality bar** | 100% calculation accuracy; every guardrail breach caught |
| **Failure mode** | Conservative — flags aggressively, lets humans decide |
| **Tools owned** | `calculator_engine.py`, `guardrail_rules.py`, all test suites |
| **Active in** | Steps 6-7 (Simulate + Guardrail Check) |

**Key behaviors:**
- Never approximates — all calculations are deterministic and auditable
- Flags deals where margin drops below threshold, even if individual terms are within guardrails
- Surfaces compound risk (e.g., high rev share + long duration + exclusivity = high exposure)
- Breakeven analysis accounts for acquisition cost and ramp-up periods
- *(Future: could generate a "deal risk score" combining multiple factors)*

---

### 3.4 Executive Sponsor

| Attribute | Detail |
|-----------|--------|
| **Role** | Final approver for deals outside standard parameters |
| **Responsible for** | Strategic alignment, budget impact, portfolio-level risk |
| **Domain expertise** | Business strategy, P&L management, partner ecosystem |
| **Quality bar** | Approves only deals that align with company strategy and financial targets |
| **Failure mode** | Escalates to VP/C-level when deal exceeds their authority |
| **Tools owned** | Approval workflow *(future phase)* |
| **Active in** | Step 9 (Approve) — *future phase, not in POC* |

**Key behaviors:**
- Reviews deals flagged by guardrails (outside standard parameters)
- Considers portfolio-level impact (are we over-indexed on one partner type?)
- Can approve, reject, or send back with modified terms
- Approval is logged with rationale for audit trail
- *(In POC: this is a conceptual role. In future: becomes an approval workflow with SLAs.)*

---

### 3.5 Legal

| Attribute | Detail |
|-----------|--------|
| **Role** | Ensures deal terms are contractually sound and compliant |
| **Responsible for** | Contract template accuracy, clause compliance, regulatory checks |
| **Domain expertise** | Contract law, partnership agreements, compliance requirements |
| **Quality bar** | Every generated contract is legally enforceable and compliant |
| **Failure mode** | Blocks contract generation until terms are compliant |
| **Tools owned** | Contract templates, compliance rules *(future phase)* |
| **Active in** | Step 10 (Contract) — *future phase, not in POC* |

**Key behaviors:**
- Maintains pre-approved contract templates (MSA, addendum, partnership, affiliate)
- Validates that deal terms map correctly to contract clauses
- Flags terms that require special legal review (e.g., exclusivity in regulated markets)
- Ensures compliance with jurisdiction-specific requirements per geo scope
- *(In POC: Legal provides the guardrail boundaries and template structures. In future: becomes an automated compliance check before PDF generation.)*

---

## 4. How Agents Interact

```
                    ┌──────────────┐
                    │  BD uploads   │
                    │  recording    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ NLP Processor │
                    │ transcribe +  │
                    │ extract terms │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Deal Maker   │
                    │ review terms  │◄──── BD edits here
                    │ advise on     │
                    │ structure     │
                    └──────┬───────┘
                           │
                    ┌──────▼────────┐
                    │ Deal & Risk   │
                    │ Analyst       │
                    │ compute       │
                    │ financials +  │
                    │ check rails   │
                    └──────┬────────┘
                           │
                    ┌──────▼───────┐
              ┌─────│  GUARDRAILS  │─────┐
              │     │  check       │     │
              │     └──────────────┘     │
              │                          │
        ┌─────▼─────┐            ┌──────▼──────┐
        │  WITHIN   │            │  OUTSIDE    │
        │  range    │            │  range      │
        │           │            │             │
        │ Auto-     │            │ Route to    │
        │ finalize  │            │ Exec        │
        └───────────┘            │ Sponsor +   │
                                 │ Legal       │
                                 │ (future)    │
                                 └─────────────┘
```

---

## 5. Quality Gates

Each stage has a quality gate before the pipeline proceeds:

| Gate | After Step | Check | Fail Action |
|------|-----------|-------|-------------|
| **G1: Transcript quality** | Transcribe | Word confidence > 70% average | Warn BD; allow proceed with caution |
| **G2: Extraction completeness** | Extract | At least 3 fields extracted with high/medium confidence | Warn BD; all fields editable manually |
| **G3: BD validation** | Review | BD has reviewed and confirmed terms | Block finalize until BD confirms |
| **G4: Guardrail compliance** | Simulate | No hard-block breaches | Block finalize; BD must adjust terms |
| **G5: Financial sanity** | Simulate | Margin > 0%; breakeven < deal duration | Warn BD; allow proceed with flag |

---

## 6. File Structure (Project)

```
BD-Mobile-Deal-Desk/
├── 00-MASTER-PLAN.md                    # Overall roadmap
├── 01-PRD-Phase1-Deal-Calculator.md     # Phase 1 PRD
├── 02-PRD-Phase2-CRM-Drive.md           # Phase 2 PRD
├── 03-WAY-OF-WORKING.md                 # This file
├── PRD-BD-Deal-Desk.md                  # Original combined PRD (archive)
│
├── tools/                               # Precision scripts & configs
│   ├── calculator_engine.py             # Core financial formulas
│   ├── guardrail_rules.py              # Guardrail definitions + validation
│   ├── nlp_extraction_prompt.txt        # LLM extraction prompt
│   ├── nlp_schema.json                  # Expected extraction output schema
│   ├── nlp_eval.py                      # Prompt accuracy evaluation
│   ├── test_calculator.py               # Calculator unit tests
│   ├── test_guardrails.py               # Guardrail unit tests
│   └── nlp_test_cases/                  # Sample transcripts for testing
│       ├── test_rev_share.txt
│       ├── test_flat_fee.txt
│       ├── test_hybrid.txt
│       └── expected_outputs/
│
├── app/                                 # Application code (Phase 1+)
│   ├── frontend/                        # React / React Native
│   └── backend/                         # FastAPI
│
└── docs/                                # Additional documentation
    └── decisions/                       # Architecture Decision Records
```

---

*This document defines how we build, not what we build. For what, see the Phase PRDs.*
