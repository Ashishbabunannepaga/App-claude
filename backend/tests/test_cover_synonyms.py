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
