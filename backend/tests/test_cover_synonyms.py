"""Insurers name the same cover differently; Ask AI must find it under the policy's own name."""

import pytest

from app.ai.prompts import QA_SYSTEM
from app.processing.glossary import english_terms


@pytest.mark.parametrize(
    "question",
    [
        "Is zero depreciation included?",
        "do I have zero dep",
        "nil dep cover?",
        "Is it bumper to bumper?",
        "zero-depreciation claims limit",
    ],
)
def test_zero_depreciation_finds_depreciation_reimbursement(question):
    assert "depreciation reimbursement" in english_terms(question)


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("Is engine protection there?", "engine secure"),
        ("water in engine, hydrostatic lock covered?", "engine secure"),
        ("Do I get RSA?", "road side assistance"),
        ("return to invoice cover?", "return to invoice"),
        ("are consumables paid", "consumable expenses"),
        ("PED waiting period?", "pre-existing disease"),
        ("Any co-pay?", "co-payment"),
    ],
)
def test_other_cover_names(question, expected):
    assert expected in english_terms(question)


def test_unrelated_questions_add_nothing():
    assert english_terms("When does my policy end?") == ""
    assert english_terms("What is the deposit amount?") == ""  # "dep" inside a word is not zero dep


def test_hindi_glossary_still_works():
    assert "dental" in english_terms("क्या दांत का इलाज कवर है?")


def test_qa_prompt_treats_insurer_names_as_the_same_cover_and_adds_no_numbers():
    assert "depreciation reimbursement" in QA_SYSTEM
    assert "Never add one" in QA_SYSTEM


TATA_WORDING = "Section - I Add-On Covers (Add) Depreciation Reimbursement (TA 01) Rs 2599.60 (Add) Engine Secure"


def test_note_tells_the_model_this_policys_name_for_the_cover():
    from app.processing.glossary import cover_name_notes

    notes = cover_name_notes("Is zero depreciation included?", TATA_WORDING)
    assert len(notes) == 1
    assert '"zero depreciation"' in notes[0] and '"depreciation reimbursement"' in notes[0]
    assert "included" in notes[0]


def test_no_note_when_the_policy_does_not_have_the_cover_or_the_question_uses_its_name():
    from app.processing.glossary import cover_name_notes

    assert cover_name_notes("Is zero depreciation included?", "Basic own damage premium only") == []
    assert cover_name_notes("Is depreciation reimbursement included?", TATA_WORDING) == []
    assert cover_name_notes("When does my policy end?", TATA_WORDING) == []


def test_ask_sends_the_note_to_the_model(client, auth, monkeypatch):
    from app.ai.gateway import get_ai_gateway
    from tests.conftest import make_pdf

    policy_pages = [
        [
            "TATA AIG General Insurance - Auto Secure Private Car Package Policy",
            "Policy No. 6203516874 02 00  Period 04/10/2026 to 03/10/2027",
            "Total IDV 426164   Total Policy Premium Rs 13152",
            "Section - I Add-On Covers: (Add) Depreciation Reimbursement (TA 01) Rs 2599.60",
        ]
    ]
    doc = client.post(
        "/api/v1/documents", files={"file": ("p.pdf", make_pdf(policy_pages), "application/pdf")}, headers=auth
    ).json()
    policy_id = client.get(f"/api/v1/documents/{doc['id']}", headers=auth).json()["policy_id"]
    assert policy_id

    seen = {}
    provider = get_ai_gateway().provider
    real = provider.complete_json

    def spy(task, system, prompt, **kw):
        seen[task] = prompt
        return real(task, system, prompt, **kw)

    monkeypatch.setattr(provider, "complete_json", spy)
    r = client.post(f"/api/v1/policies/{policy_id}/ask", json={"question": "Is zero dep included?"}, headers=auth)
    assert r.status_code == 200
    assert 'this policy calls "depreciation reimbursement"' in seen["qa"]
