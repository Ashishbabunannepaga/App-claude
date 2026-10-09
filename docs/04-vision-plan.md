# Vision plan — from insurance app to insurance intelligence ecosystem

Maps the long-term vision (5 phases) to what is built, what is next, and what needs partners or legal work
rather than code. Updated: 5 Oct 2026.

Legend: ✅ built · 🟡 partly built · 🔜 next (code only) · 🤝 needs partners / legal / data first

## Phase 1 — Document intelligence foundation

| Capability | Status | Notes |
|---|---|---|
| OCR pipelines | ✅ | Tesseract (English + Hindi) by default; PaddleOCR provider for the ML worker |
| Policy parsing & metadata extraction | ✅ | AI extraction + regex grounding validation + per-field confidence |
| Clause extraction | ✅ | Rule-based typed clauses with page/section — explainable, and a labelled base for a future classifier |
| Structured JSON | ✅ | Core fields + type-specific details (health / life / motor) |
| Searchable policy database | ✅ | PostgreSQL + pgvector; clause search in the app |
| Layout-aware parsing (tables, multi-column) | 🔜 | docling / pdfplumber tables for premium & benefit tables |

## Phase 2 — RAG insurance assistant

| Capability | Status | Notes |
|---|---|---|
| Grounded retrieval, citation-enforced answers | ✅ | Refuses when the document doesn't say |
| Clause-aware responses | ✅ | Related clauses shown under each answer |
| Claims assistance | 🟡 | Static step-by-step guides; AI claim checklist per policy is next |
| Multilingual | 🟡 | AI answers/summaries in 9 Indian languages; app screens in English (UI translation 🔜) |
| Voice questions | 🔜 | Speech-to-text in the app, same Q&A pipeline |

## Phase 3 — Insurance intelligence engine

| Capability | Status | Notes |
|---|---|---|
| Coverage-gap insights | ✅ | Product-neutral; never names or ranks products |
| Coverage report (item-by-item checklist with page refs) | ✅ | Sample report for new users; feature map in `replica/` |
| Rewards (coins) | 🟡 | Ledger + earning built; redemption perks need partners 🤝 |
| Renewal tracking & reminders | ✅ | Prediction of lapse risk needs usage data 🤝 |
| Nominee management & family support | ✅ | Nominee records, minor/appointee, "if something happens" guide; secure nominee access 🔜 |
| Comparison of the user's own policies | ✅ | |
| Market product recommendations / comparison | 🤝 | Regulated by IRDAI — needs a licensed structure (broker / corporate agent / web aggregator) or licensed partner |
| Financial capability / risk profiling | 🤝 | Needs explicit consent design (DPDP) and income data |

## Phase 4 — Ecosystem integration

| Capability | Status | Notes |
|---|---|---|
| Hospitals (network lookup, cashless) | 🤝 | Insurer/TPA network data or partnership APIs |
| Garages (cashless motor repair) | 🤝 | Insurer network data / partnerships |
| Emergency workflows | 🟡 | Emergency card built (112 / 108, policy numbers to copy). Nearest-hospital lookup needs partner data 🤝 |
| Document verification (DigiLocker) | 🤝 | DigiLocker partner onboarding |
| Claim pipelines with insurers | 🤝 | Insurer APIs / Bima Sugam when available |

## Phase 5 — Proprietary AI

| Capability | Status | Notes |
|---|---|---|
| Own embeddings (bge-m3) | 🟡 | Provider + re-embed script built; deploy the ML worker to switch over |
| Own retrieval | ✅ | Hybrid vector + keyword + glossary; no framework lock-in |
| Fine-tuned small models (Qwen2.5-7B / Llama 3.1 8B) | 🤝 | Needs a labelled dataset (thousands of policies + Q&A) and GPU serving |
| Insurer-specific adapters | 🤝 | Needs per-insurer document samples |
| Fraud detection | 🤝 | Needs claims data from partners |

## The data flywheel (start now)

Own AI is only as good as the data. Every step below is already supported by the code:

1. **Collect** anonymised policies (Week 0 task) → upload them through the app or a script.
2. **Correct**: every user correction on the verify screen is stored with confidence 1.0 — that is a labelled example.
3. **Label clauses**: the rule-based clause types are a starting label set; reviewers fix mistakes → training data.
4. **Evaluate**: golden Q&A sets per policy (intern) measure every model change.
5. **Train**: once ~2–5k labelled policies exist, fine-tune a small model for extraction and clause typing, and
   compare it against the API models on the golden set before switching.

## Next code milestones (no partners needed)

1. AI claim checklist per policy (uses clauses + type-specific rules).
2. Emergency card (offline-capable) with helplines and policy numbers.
3. App UI translation to Hindi (strings are already in one place per screen; move to `flutter gen-l10n`).
4. Table-aware PDF parsing.
5. Deploy the ML worker (PaddleOCR + bge-m3) to staging and run the re-embed script.
