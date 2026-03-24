# BD Deal Desk — Master Plan

**Last Updated:** 2026-03-23

---

## The Problem

BD reps spend ~1 week assembling a custom partner/affiliate deal. Too slow, too many tools, too many errors.

## The Goal

**From 1 week to 1 minute.** One tool that takes a call recording and turns it into finalized deal financials.

---

## Two-Phase POC

### Phase 1: NLP-Powered Deal Calculator
> **Status:** Active — building now
> **PRD:** `01-PRD-Phase1-Deal-Calculator.md`

Upload a call recording → transcribe → NLP extracts deal terms → populates calculator → BD edits → finalize deal financials.

**Delivers:** A standalone calculator that turns a conversation into structured deal terms + financial projections in under 1 minute.

### Phase 2: Simple CRM + Google Drive Automation
> **Status:** Planned
> **PRD:** `02-PRD-Phase2-CRM-Drive.md`

Shared Google Drive folder watches for new recordings → auto-creates deal → runs Phase 1 pipeline → BD gets notified → reviews and finalizes.

**Delivers:** A lightweight deal tracker per BD, with automation that eliminates the manual "upload and process" step from Phase 1.

---

## How We Work

> **See:** `03-WAY-OF-WORKING.md`

Defines our end-to-end workflow, tools (including precision Python scripts for the calculator engine), and agent personas that oversee each stage of the pipeline.

---

## Future Phases (Post-POC)

Once the POC is validated:

- HubSpot CRM sync (bi-directional)
- Deal Desk approval workflow (auto-approve in-guardrail, route exceptions)
- Contract PDF generation (auto-populate Legal-approved templates)
- E-signature integration (DocuSign/HelloSign)
- Gong direct integration (skip Google Drive; pull from Gong API)
- Scenario comparison (side-by-side up to 3 deal structures)
- Deal analytics dashboard (pipeline metrics, deal velocity, margin trends)

---

## Key Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | Platform | Mobile-first web app |
| 2 | Deal types | Rev share, flat fee, hybrid, tiered, usage-based |
| 3 | Recording input | Audio file upload (mp3/m4a/wav) |
| 4 | NLP approach | Transcribe audio → LLM extracts structured deal terms |
| 5 | Google Drive | Shared team folder; app watches for new recordings (Phase 2) |
| 6 | CRM | Build lightweight in Phase 2 (not HubSpot) |
| 7 | Guardrails | Deal Desk owns and maintains boundaries |
| 8 | Contract/PDF | Not in POC |
| 9 | E-signature | Not in POC |
| 10 | Approval workflow | Not in POC |

---

## File Index

| File | Purpose |
|------|---------|
| `00-MASTER-PLAN.md` | This file — overall roadmap and decisions |
| `01-PRD-Phase1-Deal-Calculator.md` | Phase 1 PRD — NLP calculator |
| `02-PRD-Phase2-CRM-Drive.md` | Phase 2 PRD — CRM + Google Drive |
| `03-WAY-OF-WORKING.md` | Workflow, tools, agent personas |
| `PRD-BD-Deal-Desk.md` | Original combined PRD (archived reference) |
