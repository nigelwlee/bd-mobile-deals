# PRD: BD Deal Desk — POC

**Version:** 0.3 (POC)
**Author:** [TBD]
**Last Updated:** 2026-03-23
**Status:** Draft — Open for iteration

---

## 1. Problem

BD reps spend ~1 week assembling a custom partner/affiliate deal. The process: record a call, manually pull out deal points, build a spreadsheet, email Deal Desk, wait for approval, draft a contract. Too slow, too many tools, too many errors.

## 2. Goal

**From 1 week to 1 minute.** BD uploads a recording, gets suggested deal terms extracted via NLP, edits them, and locks in the financials — all in one tool.

| Metric | Current | Target |
|--------|---------|--------|
| Time to finalize deal terms | ~1 week | < 1 minute |
| Tools used | 4-6 | 1 |
| Manual data entry errors | Frequent | Near-zero |

---

## 3. POC Scope — Two Phases

### Phase 1: NLP-Powered Deal Calculator

**What it does:** BD uploads a call recording. The app transcribes it, extracts deal-relevant terms via NLP, and populates a calculator. BD reviews/edits the suggested terms, and the calculator outputs finalized deal financials.

**User flow:**

```
BD uploads audio recording (mp3/m4a/wav)
  → App transcribes audio to text (speech-to-text)
  → NLP extracts deal terms from transcript:
      - Partner name
      - Deal type (rev share / flat fee / hybrid / tiered)
      - Proposed percentages, rates, fees
      - Duration / term length
      - Geo or exclusivity terms mentioned
      - Payment terms discussed
  → Extracted terms populate the Deal Calculator
  → BD reviews suggested terms (highlighted with confidence scores)
  → BD edits / adjusts any terms via input fields + sliders
  → Calculator computes deal financials in real-time:
      - Projected partner payout
      - Net revenue to company
      - Margin %
      - Breakeven point
  → BD taps "Finalize Deal"
  → Summary of finalized deal terms + financials saved
```

**Key components:**

| Component | Description |
|-----------|-------------|
| **Audio upload** | Accepts mp3, m4a, wav; max ~60 min recording |
| **Speech-to-text** | Transcribes recording (Whisper API, Deepgram, or similar) |
| **NLP term extraction** | Parses transcript for deal-relevant data points (LLM-based) |
| **Deal Calculator** | Editable fields pre-filled by NLP; real-time financial projections |
| **Guardrails** | Deal Desk-defined min/max boundaries per parameter; flags out-of-range terms |
| **Finalize & save** | Locks deal terms + financials; stores as a deal record |

**What's NOT in Phase 1:**
- No CRM
- No deal list / pipeline view
- No PDF generation
- No approval workflow
- No Google Drive integration

---

### Phase 2: Simple CRM + Google Drive Automation

**What it does:** A lightweight deal tracker (CRM) that lists all deals per BD. Connects to a shared Google Drive folder — when a new recording is uploaded to the folder, the app auto-detects it, creates a new deal record, and runs the Phase 1 pipeline (transcribe → extract → populate calculator).

**User flow:**

```
BD (or Gong) drops a recording into the shared Google Drive folder
  → App detects new file via Google Drive watch/webhook
  → App creates a new Deal record:
      - Assigns to the BD who uploaded (or based on folder/naming convention)
      - Status: "Processing"
  → Runs Phase 1 pipeline automatically:
      - Transcribes audio
      - Extracts deal terms via NLP
      - Populates calculator with suggested terms
  → BD gets notified (push / email): "New deal ready for review"
  → BD opens the deal in the CRM
  → BD reviews/edits terms in the calculator
  → BD finalizes → deal status updates to "Finalized"
```

**Key components:**

| Component | Description |
|-----------|-------------|
| **Deal list (CRM)** | Per-BD view of all deals; statuses: `Processing` → `Ready for Review` → `Finalized` |
| **Deal detail view** | Partner info, calculator, transcript, audio playback |
| **Google Drive connector** | Watches a shared team folder for new audio files |
| **Auto-pipeline trigger** | New file → create deal → transcribe → extract → populate calculator |
| **Notifications** | Push/email alert when a deal is ready for BD review |
| **Basic search & filter** | Find deals by partner name, status, date |

**What's NOT in Phase 2:**
- No HubSpot sync (future)
- No Deal Desk approval workflow (future)
- No PDF/contract generation (future)
- No e-signature (future)

---

## 4. Deal Calculator — Detail

The calculator is the core of both phases. Here's what it computes:

### Input fields (pre-filled by NLP, editable by BD)

| Field | Type | Example |
|-------|------|---------|
| Partner name | Text | "Acme Corp" |
| Deal type | Dropdown | Rev share / Flat fee / Hybrid / Tiered / Usage-based |
| Revenue share % | Slider + input | 15% |
| Flat fee (if applicable) | Currency input | $5,000/mo |
| Tiered rates | Table (volume → rate) | 0-100: 20%, 101-500: 15%, 500+: 10% |
| Deal duration | Dropdown | 6 mo / 12 mo / 24 mo / Custom |
| Geo scope | Multi-select | US, EU, APAC, Global |
| Exclusivity | Toggle | Yes / No |
| Payment terms | Dropdown | Net 30 / Net 60 / Net 90 |
| Estimated monthly volume | Number input | 1,000 units |
| Average deal value | Currency input | $50/unit |

### Output (computed in real-time)

| Output | Formula logic |
|--------|---------------|
| **Projected monthly partner payout** | Volume x deal value x rev share % (or flat fee) |
| **Projected annual partner payout** | Monthly x 12 (adjusted for duration) |
| **Net revenue to company** | Gross revenue - partner payout |
| **Margin %** | Net revenue / gross revenue |
| **Breakeven point** | When cumulative net revenue > partner acquisition cost |
| **Total deal value** | Sum of all payouts over deal duration |

### Guardrails (Deal Desk configurable)

| Parameter | Min | Max | Action if breached |
|-----------|-----|-----|--------------------|
| Rev share % | 5% | 30% | Warning + flag |
| Flat fee | $500/mo | $25,000/mo | Warning + flag |
| Deal duration | 3 months | 36 months | Warning + flag |
| Payment terms | Net 30 | Net 90 | Hard block beyond Net 90 |

*(Actual values TBD by Deal Desk — above are placeholder examples)*

---

## 5. NLP Term Extraction — Detail

The NLP layer processes the transcript and extracts structured data. It should handle:

| What to extract | Example from transcript | Mapped to |
|----------------|------------------------|-----------|
| Partner identity | "We're talking to Acme Corp about..." | Partner name |
| Deal structure | "We're thinking a rev share model..." | Deal type |
| Rates/percentages | "...somewhere around 15 to 20 percent" | Rev share % (suggests 17.5%, shows range) |
| Fees | "...plus a flat monthly fee of five thousand" | Flat fee |
| Duration | "...for a 12-month initial term" | Deal duration |
| Geography | "...focused on the US and European markets" | Geo scope |
| Exclusivity | "...they want exclusivity in APAC" | Exclusivity toggle + geo |
| Payment | "...net 60 payment terms" | Payment terms |

**Confidence scoring:** Each extracted field gets a confidence score (high/medium/low). Low-confidence fields are visually flagged so the BD knows to double-check.

**Fallback:** If NLP can't extract a field, it's left blank for the BD to fill manually. The calculator still works with partial data.

---

## 6. Technical Approach (POC)

| Layer | Approach |
|-------|----------|
| **Frontend** | Mobile-first web app (React / React Native or Flutter) |
| **Speech-to-text** | OpenAI Whisper API or Deepgram |
| **NLP extraction** | LLM-based (GPT-4 / Claude) with structured output prompts |
| **Calculator engine** | Client-side computation; guardrails config from backend |
| **Backend** | Lightweight API (Node/Python) |
| **Database** | PostgreSQL or Firebase (deal records, configs) |
| **Google Drive** | Google Drive API v3 — watch changes on shared folder |
| **Notifications** | Firebase Cloud Messaging (push) + email (SendGrid) |
| **Hosting** | Vercel / Railway / GCP (keep it simple for POC) |

---

## 7. Information Architecture

### Phase 1 (Calculator only)
```
Upload Recording
  → Processing Screen (transcribing...)
  → Review Extracted Terms (with confidence indicators)
  → Deal Calculator (edit terms + view financials)
  → Finalized Deal Summary
```

### Phase 2 (CRM + Drive)
```
Home (Deal List)
├── Deal Card → Deal Detail
│   ├── Partner Info
│   ├── Transcript + Audio Playback
│   ├── Deal Calculator
│   └── Finalized Summary
├── New Deal (manual upload — same as Phase 1)
├── Auto-created Deals (from Google Drive)
└── Settings
    ├── Google Drive Folder Link
    ├── Guardrail Configuration
    └── Notification Preferences
```

---

## 8. Decisions Made

| # | Question | Decision |
|---|----------|----------|
| 1 | Platform | Mobile-first web app |
| 2 | Deal types | Multiple — rev share, flat fee, hybrid, tiered, usage-based |
| 3 | Recording input | Audio file upload (mp3/m4a/wav) |
| 4 | NLP source | Transcribe audio → extract terms via LLM |
| 5 | Google Drive | Shared team folder; app watches for new recordings |
| 6 | CRM | Build simple/lightweight in Phase 2 (not HubSpot sync) |
| 7 | Guardrail ownership | Deal Desk defines and maintains boundaries |
| 8 | Contract/PDF | Not in POC — future phase |
| 9 | E-signature | Not in POC — future phase |
| 10 | Approval workflow | Not in POC — future phase |

## 9. Open Questions

1. **What speech-to-text service to use?** (Whisper, Deepgram, Google STT — cost/accuracy tradeoff)
2. **What LLM for extraction?** (GPT-4, Claude — depends on accuracy needs and cost)
3. **Actual guardrail values from Deal Desk?** (Need real min/max for rev share, fees, duration, etc.)
4. **Google Drive folder structure?** (Single folder? Subfolders per BD? Naming convention for files?)
5. **How is BD identified from a Drive upload?** (Folder path, filename convention, or manual assignment?)

---

## 10. Future Phases (Post-POC)

Once the POC is validated, the roadmap expands:

- **HubSpot CRM sync** — bi-directional; replace manual partner data entry
- **Deal Desk approval workflow** — auto-approve in-guardrail, route exceptions
- **Contract PDF generation** — auto-populate Legal-approved templates
- **E-signature** — DocuSign/HelloSign integration
- **Gong direct integration** — skip Google Drive; pull recordings from Gong API
- **Scenario comparison** — side-by-side compare up to 3 deal structures
- **Deal analytics dashboard** — pipeline metrics, deal velocity, margin trends

---

*This is a living document. Edit directly.*
