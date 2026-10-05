"""Versioned prompts. Bump the version when changing a prompt so evaluations stay comparable."""

EXTRACT_VERSION = "extract-v1"
SUMMARY_VERSION = "summary-v2"
QA_VERSION = "qa-v2"

CORE_FIELDS = [
    "insurer",
    "plan_name",
    "policy_number",
    "start_date",
    "end_date",
    "premium",
    "sum_insured",
    "payment_frequency",
]

DETAIL_FIELDS = {
    "health": [
        "room_rent_limit",
        "initial_waiting_period",
        "ped_waiting_period",
        "specific_disease_waiting_period",
        "pre_hospitalisation_days",
        "post_hospitalisation_days",
        "maternity",
        "opd",
        "day_care",
        "ambulance",
        "domiciliary",
        "home_healthcare",
        "ayush",
        "modern_treatment",
        "no_claim_bonus",
        "deductible",
        "co_payment",
        "restoration",
        "sub_limits",
        "insured_members",
        "tpa",
        "exclusions",
    ],
    "life": [
        "sum_assured",
        "premium_paying_term",
        "policy_term",
        "plan_category",
        "fund_options",
        "charges",
        "lock_in_period",
        "surrender",
        "partial_withdrawal",
        "bonus",
        "maturity_benefit",
        "death_benefit",
        "riders",
        "nominee",
        "life_assured",
    ],
    "motor": [
        "vehicle_make_model",
        "registration_number",
        "idv",
        "own_damage_premium",
        "third_party_premium",
        "add_ons",
        "zero_depreciation",
        "engine_protection",
        "return_to_invoice",
        "consumables",
        "roadside_assistance",
        "ncb_percentage",
        "compulsory_deductible",
        "exclusions",
    ],
    "other": ["coverage_description", "exclusions"],
}

EXTRACT_SYSTEM = """You extract structured data from Indian insurance policy documents.
Rules:
- Use ONLY information present in the document text. Never guess or use outside knowledge.
- If a value is not clearly stated, return null with confidence 0.
- Dates: ISO format YYYY-MM-DD. Amounts: plain numbers in INR without commas or symbols.
- payment_frequency: one of annual, half_yearly, quarterly, monthly, single, null.
- confidence: 0.0-1.0, how certain you are the value is correct and complete.
- Respond with a single JSON object and nothing else."""

EXTRACT_PROMPT = """Classify this policy as one of: health, life, motor, other.
Then extract fields.

Return JSON exactly in this shape:
{{
  "policy_type": "health|life|motor|other",
  "fields": {{ "<core_field>": {{"value": <string|number|null>, "confidence": <0-1>}} , ... }},
  "details": {{ "<detail_field>": <short plain-language string or null>, ... }}
}}

Core fields: {core_fields}
Detail fields by type (use only those for the detected type):
{detail_fields}

DOCUMENT TEXT (pages separated by [Page N]):
<<<
{text}
>>>"""

SUMMARY_SYSTEM = """You explain insurance policies to ordinary people in India in simple, plain English.
Use ONLY the provided policy data and excerpts. If something is not stated, say it is not mentioned.
Never recommend buying, switching or any specific insurance product.
Respond with a single JSON object and nothing else."""

SUMMARY_PROMPT = """Write a short summary of this {policy_type} policy.

Return JSON:
{{
  "headline": "<one sentence: what this policy is and the main cover>",
  "key_points": ["<up to 6 short bullet points of the most important benefits and limits>"],
  "watch_outs": ["<up to 4 important limitations, waiting periods, co-pays or exclusions that are stated>"]
}}

STRUCTURED DATA:
{structured}

EXCERPTS:
{excerpts}"""

QA_SYSTEM = """You answer a user's questions about THEIR OWN insurance policy.
Strict rules:
- Answer ONLY from the CONTEXT excerpts and structured data provided. Do not use general knowledge
  about insurance or about this insurer.
- If the context does not clearly answer the question, set "answerable" to false and say you could not
  find it in the policy document. Do not guess.
- Cite the excerpt ids (e.g. "C2") that support your answer.
- Keep the answer short (2-5 sentences), plain English, mention conditions/limits that apply.
- Never recommend buying or switching insurance products.
Respond with a single JSON object and nothing else."""

QA_PROMPT = """STRUCTURED POLICY DATA:
{structured}

CONTEXT EXCERPTS:
{excerpts}

QUESTION: {question}

Return JSON:
{{"answerable": true|false, "answer": "<answer>", "citations": ["C1", ...], "confidence": "high|medium|low"}}"""


LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "bn": "Bengali",
    "gu": "Gujarati",
    "ml": "Malayalam",
}


def language_instruction(language: str) -> str:
    if language == "en":
        return ""
    name = LANGUAGES.get(language, "English")
    return (
        f"\nWrite every text value in {name}, in simple everyday words. Keep insurer names, plan names, "
        "numbers, amounts and dates exactly as written. The user may also ask in "
        f"{name}; understand it, but search the English document as usual."
    )
