"""Evaluate the skill extractor, skill matcher and semantic matcher on evaluation/sample_dataset.json.

All numbers are computed from the dataset at run time; nothing is hard-coded.

    cd backend
    python evaluation/evaluate_models.py                 # real all-MiniLM-L6-v2 (downloads on first run)
    python evaluation/evaluate_models.py --encoder hashing   # offline smoke test, NOT transformer results
    python evaluation/evaluate_models.py --json results.json
"""
import argparse
import json
import os
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("JWT_SECRET_KEY", "evaluation-only-secret-key-0123456789")  # settings need one; unused here
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import numpy as np  # noqa: E402

from app.services.job_analyzer import JobAnalyzer  # noqa: E402
from app.services.matching_service import match_skills  # noqa: E402
from app.services.skill_extractor import get_skill_extractor  # noqa: E402


def prf(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4), "tp": tp, "fp": fp, "fn": fn}


def eval_skill_extraction(data: list[dict]) -> dict:
    ex = get_skill_extractor()
    tp = fp = fn = 0
    errors = []
    for item in data:
        pred = {n for n, _, _ in ex.find_in_text(item["text"])}
        gold = set(item["skills"])
        tp += len(pred & gold)
        fp += len(pred - gold)
        fn += len(gold - pred)
        if pred != gold:
            errors.append({"text": item["text"], "false_positives": sorted(pred - gold), "false_negatives": sorted(gold - pred)})
    return {"micro": prf(tp, fp, fn), "examples": len(data), "errors": errors}


def eval_skill_matching(data: list[dict]) -> dict:
    analyzer = JobAnalyzer()
    exact, counts, errors = 0, {"matched": [0, 0, 0], "missing": [0, 0, 0], "additional": [0, 0, 0]}, []
    for item in data:
        job = analyzer.analyze(item["job_text"])
        res = match_skills([{"name": n, "category": "x", "confidence": 1.0} for n in item["resume_skills"]], job)
        ok = True
        for key in counts:
            pred, gold = set(res[f"{key}_skills"]), set(item[f"expected_{key}"])
            counts[key][0] += len(pred & gold)
            counts[key][1] += len(pred - gold)
            counts[key][2] += len(gold - pred)
            ok &= pred == gold
        exact += ok
        if not ok:
            errors.append({"job_text": item["job_text"], "got": {k: res[f"{k}_skills"] for k in counts}})
    return {
        "exact_match_accuracy": round(exact / len(data), 4),
        "examples": len(data),
        "per_bucket": {k: prf(*v) for k, v in counts.items()},
        "errors": errors,
    }


def spearman(a: list[float], b: list[float]) -> float | None:
    if len(set(a)) < 2 or len(set(b)) < 2:
        return None
    ra, rb = np.argsort(np.argsort(a)).astype(float), np.argsort(np.argsort(b)).astype(float)
    return round(float(np.corrcoef(ra, rb)[0, 1]), 4)


def eval_semantic(data: dict, encoder_name: str) -> dict:
    from app.services.embedding_service import EmbeddingService, SentenceTransformerEncoder

    if encoder_name == "hashing":
        sys.path.insert(0, str(ROOT))
        from tests.helpers import HashingEncoder
        svc = EmbeddingService(HashingEncoder())
    else:
        svc = EmbeddingService(SentenceTransformerEncoder("sentence-transformers/all-MiniLM-L6-v2"))

    resumes = {r["id"]: svc.embed_document(r["text"]) for r in data["resumes"]}
    top1_hits, pair_ok, pair_total, per_job, all_sims, all_rel = 0, 0, 0, {}, [], []
    for job in data["jobs"]:
        jv = svc.embed_document(job["text"])
        sims = {rid: svc.cosine(v, jv) for rid, v in resumes.items()}
        rel = data["relevance"][job["id"]]
        best_gold = max(rel.values())
        top1_hits += rel[max(sims, key=sims.get)] == best_gold
        for a, b in combinations(rel, 2):
            if rel[a] != rel[b]:
                pair_total += 1
                pair_ok += (sims[a] > sims[b]) == (rel[a] > rel[b])
        ids = list(rel)
        per_job[job["id"]] = {"similarities": {k: round(v, 4) for k, v in sims.items()},
                              "top1_correct": rel[max(sims, key=sims.get)] == best_gold,
                              "spearman": spearman([sims[i] for i in ids], [rel[i] for i in ids])}
        all_sims += [sims[i] for i in ids]
        all_rel += [rel[i] for i in ids]
    related = [s for s, r in zip(all_sims, all_rel) if r == 2]
    unrelated = [s for s, r in zip(all_sims, all_rel) if r == 0]
    return {
        "encoder": encoder_name if encoder_name == "hashing" else "sentence-transformers/all-MiniLM-L6-v2",
        "top1_accuracy": round(top1_hits / len(data["jobs"]), 4),
        "pairwise_ordering_accuracy": round(pair_ok / pair_total, 4) if pair_total else None,
        "mean_similarity_strong_fit": round(float(np.mean(related)), 4) if related else None,
        "mean_similarity_unrelated": round(float(np.mean(unrelated)), 4) if unrelated else None,
        "per_job": per_job,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=str(ROOT / "evaluation" / "sample_dataset.json"))
    ap.add_argument("--encoder", choices=["transformer", "hashing"], default="transformer")
    ap.add_argument("--json", help="write full results to this file")
    args = ap.parse_args()
    data = json.loads(Path(args.dataset).read_text(encoding="utf-8"))

    results = {"skill_extraction": eval_skill_extraction(data["skill_extraction"]),
               "skill_matching": eval_skill_matching(data["skill_matching"])}
    try:
        results["semantic_matching"] = eval_semantic(data["semantic_matching"], args.encoder)
    except Exception as exc:  # e.g. model cannot be downloaded offline
        results["semantic_matching"] = {"skipped": f"{exc.__class__.__name__}: could not run the encoder"}

    se = results["skill_extraction"]
    print("== Skill extraction (micro-averaged) ==")
    print(f"  examples={se['examples']}  precision={se['micro']['precision']:.3f}  recall={se['micro']['recall']:.3f}  f1={se['micro']['f1']:.3f}")
    for e in se["errors"]:
        print("  error:", e)
    sm = results["skill_matching"]
    print("== Skill matching ==")
    print(f"  exact-match accuracy={sm['exact_match_accuracy']:.3f} over {sm['examples']} cases")
    for k, v in sm["per_bucket"].items():
        print(f"  {k:<10} precision={v['precision']:.3f} recall={v['recall']:.3f} f1={v['f1']:.3f}")
    sem = results["semantic_matching"]
    print("== Semantic matching ==")
    if "skipped" in sem:
        print("  skipped:", sem["skipped"], "(use --encoder hashing for an offline smoke test)")
    else:
        if sem["encoder"] == "hashing":
            print("  WARNING: hashing encoder = bag-of-words smoke test, NOT transformer results")
        print(f"  encoder={sem['encoder']}  top-1 accuracy={sem['top1_accuracy']}  pairwise ordering={sem['pairwise_ordering_accuracy']}")
        print(f"  mean similarity strong-fit={sem['mean_similarity_strong_fit']}  unrelated={sem['mean_similarity_unrelated']}")
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2), encoding="utf-8")
        print("Saved", args.json)


if __name__ == "__main__":
    main()
