# Phase 2 PRD: Simple CRM + Google Drive Automation

**Version:** 0.1 (Draft)
**Last Updated:** 2026-03-23
**Status:** Planned — flesh out after Phase 1 is built

---

## 1. What This Is

A lightweight deal tracker (CRM) per BD, connected to a shared Google Drive folder. When a new recording lands in the folder, the app auto-creates a deal and runs the Phase 1 pipeline (transcribe → extract → populate calculator). BD gets notified and reviews.

**Depends on:** Phase 1 (NLP Deal Calculator) must be complete and working.

---

## 2. What Phase 2 Adds on Top of Phase 1

| Capability | Phase 1 | Phase 2 |
|------------|---------|---------|
| Audio processing pipeline | Manual upload | Manual upload + auto-triggered from Google Drive |
| Deal storage | Single deal at a time | Persistent deal list per BD |
| Deal tracking | None | Status pipeline: Processing → Ready → Finalized |
| Google Drive | None | Watches shared folder for new recordings |
| Notifications | None | Push/email when a deal is ready for review |
| Multi-deal view | None | List, search, filter all deals |

---

## 3. User Flow

### Auto-triggered (Google Drive)
```
BD (or Gong export) drops recording into shared Google Drive folder
  │
  ▼
APP detects new file (Google Drive webhook / polling)
  │
  ▼
APP creates new Deal record
  │  - Assigns BD (based on subfolder or naming convention)
  │  - Status: "Processing"
  │
  ▼
RUNS Phase 1 pipeline automatically
  │  - Transcribe audio
  │  - Extract deal terms via NLP
  │  - Populate calculator with suggested terms
  │
  ▼
STATUS updates to "Ready for Review"
  │
  ▼
BD gets notified (push + email)
  │  - "New deal from [Partner Name] ready for review"
  │
  ▼
BD opens deal in CRM → reviews/edits in calculator → finalizes
```

### Manual (same as Phase 1)
```
BD opens app → taps "New Deal" → uploads recording manually → same Phase 1 flow
```

---

## 4. Screens

### Screen 1: Deal List (Home)
- Per-BD view of all their deals
- Each deal card shows: Partner name, deal type, status, date, total deal value
- Status badges: `Processing` (spinner) / `Ready for Review` (yellow) / `Finalized` (green)
- Sort: by date (default), by status, by value
- Filter: by status, by date range
- Search: by partner name
- "New Deal" button (manual upload)

### Screen 2: Deal Detail
- Tabs or sections:
  - **Summary:** Partner info, deal status, key financials
  - **Transcript:** Full transcript with audio playback controls
  - **Calculator:** The Phase 1 calculator (pre-filled, editable)
  - **History:** Timestamps of when deal was created, reviewed, finalized
- "Finalize" / "Edit" / "Delete" actions

### Screen 3: Settings
- Google Drive folder link (connect / disconnect)
- BD assignment rules (subfolder mapping or naming convention)
- Notification preferences (push on/off, email on/off)
- Guardrail configuration (same as Phase 1 but persisted)

---

## 5. Google Drive Integration — Detail

### Folder Structure (Proposed)
```
Shared Drive: BD Deal Recordings/
├── john-smith/          ← BD subfolder (auto-assigns deals to John)
│   ├── 2026-03-20-acme-corp.m4a
│   └── 2026-03-22-globex.mp3
├── jane-doe/
│   └── 2026-03-21-initech.wav
└── unassigned/          ← Deals here need manual BD assignment
    └── 2026-03-23-unknown.mp3
```

### Detection Mechanism
- **Option A: Webhook** — Google Drive push notifications (changes.watch API). Real-time but requires public endpoint.
- **Option B: Polling** — Check folder every N minutes for new files. Simpler but has latency.
- **Recommended for POC:** Polling every 2-5 minutes. Switch to webhook in production.

### File Processing Rules
- Only process audio files: `.mp3`, `.m4a`, `.wav`, `.ogg`, `.webm`
- Ignore non-audio files (docs, images, etc.)
- Skip files already processed (track by file ID)
- If file is in a BD subfolder → auto-assign to that BD
- If file is in `unassigned/` → create deal with no BD; notify admin

---

## 6. Deal Data Model

```
Deal {
  id:               UUID
  bd_user_id:       UUID (FK → User)
  partner_name:     String
  status:           Enum [processing, ready_for_review, finalized, archived]
  deal_type:        Enum [rev_share, flat_fee, hybrid, tiered, usage_based]

  // Deal terms (from NLP + BD edits)
  terms: {
    rev_share_pct:        Float
    flat_fee:             Float
    tiered_rates:         JSON
    deal_duration_months: Integer
    geo_scope:            String[]
    exclusivity:          Boolean
    payment_terms:        Enum [net_30, net_45, net_60, net_90]
    monthly_volume:       Integer
    avg_deal_value:       Float
    acquisition_cost:     Float
  }

  // Computed financials (stored on finalize)
  financials: {
    gross_monthly_revenue:    Float
    monthly_partner_payout:   Float
    monthly_net_revenue:      Float
    margin_pct:               Float
    annual_partner_payout:    Float
    annual_net_revenue:       Float
    total_deal_value:         Float
    breakeven_months:         Integer
  }

  // NLP extraction metadata
  extraction: {
    confidence_scores:  JSON  // per-field confidence
    source_quotes:      JSON  // per-field transcript quotes
    additional_notes:   String[]
  }

  // File references
  audio_file_url:     String (S3/GCS path)
  transcript_text:    Text
  gdrive_file_id:     String (null if manual upload)

  // Timestamps
  created_at:         DateTime
  updated_at:         DateTime
  finalized_at:       DateTime (null until finalized)
}
```

---

## 7. Notifications

| Event | Channel | Message |
|-------|---------|---------|
| New deal created (from Drive) | Push + Email | "New recording from [filename] is being processed" |
| Deal ready for review | Push + Email | "Deal with [Partner Name] is ready for your review" |
| Processing failed | Email | "Failed to process [filename] — [error reason]" |

---

## 8. Technical Additions (on top of Phase 1)

| Component | Technology | Notes |
|-----------|------------|-------|
| **Google Drive API** | Google Drive API v3 | Watch shared folder; download new audio files |
| **Background worker** | Celery / Cloud Tasks | Process recordings asynchronously |
| **Polling scheduler** | Cron / Cloud Scheduler | Check Drive folder every 2-5 min |
| **Notifications** | Firebase Cloud Messaging + SendGrid | Push + email |
| **User auth** | Simple auth (email/password or Google OAuth) | Identify which BD is logged in |

---

## 9. Open Questions

1. **Google Drive folder structure?** Subfolders per BD (proposed above) or flat folder with naming convention?
2. **How does Gong export to Drive?** Automatic export, or does BD manually save recordings there?
3. **Should deals be deletable?** Or only archivable (for audit trail)?
4. **Multi-BD deals?** Can two BDs work on the same deal?
5. **Offline access?** Does the CRM need to work offline on mobile?
6. **User management?** Who creates BD accounts — admin, or self-serve?

---

## 10. Success Criteria

| Criteria | Target |
|----------|--------|
| New Drive recording → deal ready for review | < 5 minutes (including transcription) |
| BD can find any deal | < 10 seconds (search/filter) |
| Zero missed recordings | Every file in Drive gets processed |
| BD correctly assigned | > 95% auto-assignment accuracy |
| Notification delivery | < 30 seconds after deal is ready |

---

*This PRD will be fleshed out further after Phase 1 is built and validated.*
