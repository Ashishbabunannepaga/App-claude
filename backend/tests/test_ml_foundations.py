import sys
import types

import pytest
from PIL import Image

from app.ai import embeddings
from app.core.config import get_settings
from app.processing import text_extraction


def test_pad_keeps_cosine_and_rejects_oversize():
    assert embeddings.pad([0.6, 0.8], 4) == [0.6, 0.8, 0.0, 0.0]
    with pytest.raises(ValueError):
        embeddings.pad([1.0] * 5, 4)


def test_local_embedder_normalises_and_pads(monkeypatch):
    class FakeModel:
        def __init__(self, name):
            self.name = name

        def encode(self, texts, normalize_embeddings, batch_size):
            import numpy as np

            assert normalize_embeddings
            return np.array([[1.0, 0.0, 0.0]] * len(texts))

    monkeypatch.setitem(sys.modules, "sentence_transformers", types.SimpleNamespace(SentenceTransformer=FakeModel))
    e = embeddings.LocalEmbedder("BAAI/bge-m3", 8)
    assert e.model.name == "BAAI/bge-m3"
    assert e.embed(["a", "b"]) == [[1.0, 0.0, 0.0, 0, 0, 0, 0, 0]] * 2


def test_paddle_ocr_reading_order(monkeypatch):
    class FakePaddle:
        def ocr(self, image, cls):
            # Boxes out of order; two on the same visual line; one low-confidence line dropped.
            return [
                [
                    ([[300, 50]], ("Rs. 10,00,000", 0.97)),
                    ([[20, 52]], ("Sum Insured:", 0.98)),
                    ([[20, 10]], ("Star Health Policy", 0.99)),
                    ([[20, 90]], ("smudge", 0.2)),
                ]
            ]

    monkeypatch.setattr(get_settings(), "ocr_provider", "paddle")
    text_extraction._paddle_engine.cache_clear()
    monkeypatch.setattr(text_extraction, "_paddle_engine", lambda: FakePaddle())
    text = text_extraction._ocr_image(Image.new("RGB", (10, 10)))
    assert text == "Star Health Policy\nSum Insured: Rs. 10,00,000"


def test_paddle_missing_reports_ocr_unavailable(monkeypatch):
    monkeypatch.setattr(get_settings(), "ocr_provider", "paddle")
    monkeypatch.setitem(sys.modules, "paddleocr", None)
    text_extraction._paddle_engine.cache_clear()
    with pytest.raises(text_extraction.ExtractionError) as err:
        text_extraction._ocr_image(Image.new("RGB", (10, 10)))
    assert err.value.code == "ocr_unavailable"
    text_extraction._paddle_engine.cache_clear()


def test_backfill_and_reembed_scripts(client, auth, capsys):
    from app.scripts import backfill_clauses, reembed
    from tests.conftest import make_pdf

    doc = client.post("/api/v1/documents", files={"file": ("p.pdf", make_pdf(), "application/pdf")}, headers=auth)
    pid = client.get(f"/api/v1/documents/{doc.json()['id']}", headers=auth).json()["policy_id"]
    before = client.get(f"/api/v1/policies/{pid}/clauses", headers=auth).json()
    backfill_clauses.main()
    reembed.main()
    out = capsys.readouterr().out
    assert "clauses rebuilt for 1 policies" in out and "re-embedded" in out
    after = client.get(f"/api/v1/policies/{pid}/clauses", headers=auth).json()
    assert [c["text"] for c in after] == [c["text"] for c in before]
