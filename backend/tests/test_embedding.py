import os

import numpy as np
import pytest

from app.services.embedding_service import EmbeddingService, SentenceTransformerEncoder
from app.services.matching_service import semantic_analysis
from tests.helpers import HashingEncoder, read_sample


def test_cosine_similarity_known_values():
    c = EmbeddingService.cosine
    assert c(np.array([1.0, 0.0]), np.array([1.0, 0.0])) == pytest.approx(1.0)
    assert c(np.array([1.0, 0.0]), np.array([0.0, 1.0])) == pytest.approx(0.0)
    assert c(np.array([1.0, 1.0]), np.array([-1.0, -1.0])) == pytest.approx(-1.0)
    assert c(np.zeros(2), np.array([1.0, 0.0])) == 0.0


def test_document_embedding_is_unit_length_and_chunked(embedder):
    long_text = " ".join(f"word{i}" for i in range(1000))
    assert len(embedder._chunk(long_text)) > 4  # long documents are split, not truncated
    v = embedder.embed_document(long_text)
    assert np.linalg.norm(v) == pytest.approx(1.0, abs=1e-5)


def test_similar_texts_score_higher_than_unrelated(embedder):
    a = embedder.embed_document("python machine learning fastapi postgresql developer")
    b = embedder.embed_document("looking for python and machine learning developer with fastapi")
    c = embedder.embed_document("pastry chef baking sourdough bread and croissants")
    assert embedder.cosine(a, b) > embedder.cosine(a, c) + 0.3


def test_model_is_loaded_once(monkeypatch):
    calls = {"n": 0}

    class FakeST:
        def __init__(self, name):
            calls["n"] += 1

        def encode(self, texts, **kw):
            return np.ones((len(texts), 4), dtype=np.float32)

    import sys, types
    monkeypatch.setitem(sys.modules, "sentence_transformers", types.SimpleNamespace(SentenceTransformer=FakeST))
    enc = SentenceTransformerEncoder("dummy")
    for _ in range(5):
        enc.encode(["a", "b"])
    assert calls["n"] == 1 and enc.loaded


def test_model_load_failure_is_reported_cleanly(monkeypatch):
    import sys, types
    from app.core.exceptions import ModelUnavailableError

    def boom(name):
        raise OSError("no network")

    monkeypatch.setitem(sys.modules, "sentence_transformers", types.SimpleNamespace(SentenceTransformer=boom))
    enc = SentenceTransformerEncoder("dummy")
    with pytest.raises(ModelUnavailableError):
        enc.encode(["x"])
    assert enc.load_error == "OSError"


def test_semantic_analysis_end_to_end(embedder, processor, job_analyzer):
    from types import SimpleNamespace
    resume_text, job_text = read_sample("resume_priya_raman.txt"), read_sample("job_ml_engineer.txt")
    profile = processor.parse(resume_text)
    job = SimpleNamespace(analysis=job_analyzer.analyze(job_text), raw_text=job_text, embedding=None)
    resume = SimpleNamespace(embeddings=None, raw_text=resume_text)
    r = semantic_analysis(resume, job, profile, job.analysis, embedder, 0.45, "m")
    assert 0 < r["semantic_similarity"] < 1
    assert r["semantic_score"] == pytest.approx(r["semantic_similarity"] * 100, abs=0.1)
    assert {"skills", "experience", "projects"} <= set(r["section_similarity"])
    assert r["requirement_coverage"] and all({"requirement", "best_similarity", "covered"} <= set(c)
                                             for c in r["requirement_coverage"])
    assert "resume" in r["cache_updates"] and "job" in r["cache_updates"]

    # second run reuses cached vectors (no re-embedding of the documents)
    resume.embeddings = r["cache_updates"]["resume"]
    job.embedding = r["cache_updates"]["job"]
    job.analysis = {**job.analysis, "_embedding_model": "m"}
    r2 = semantic_analysis(resume, job, profile, job.analysis, embedder, 0.45, "m")
    assert r2["cache_updates"] == {} and r2["semantic_similarity"] == r["semantic_similarity"]


@pytest.mark.transformer
@pytest.mark.skipif(os.getenv("RUN_MODEL_TESTS") != "1", reason="set RUN_MODEL_TESTS=1 to run with the real model")
def test_real_transformer_semantics():
    from app.core.config import get_settings
    svc = EmbeddingService(SentenceTransformerEncoder(get_settings().embedding_model_name))
    a = svc.embed_document("Experienced Python developer who builds machine learning APIs")
    b = svc.embed_document("We need a software engineer for ML model deployment using Python")
    c = svc.embed_document("Head chef needed for a busy seafood restaurant")
    assert a.shape[0] == 384  # all-MiniLM-L6-v2 dimension
    assert svc.cosine(a, b) > svc.cosine(a, c) + 0.2
