import pytest

from app.services.matching_service import (CONTEXT_WEIGHT, WEIGHTS, education_relevance, experience_relevance,
                                           match_skills, overall_score)
from app.services.quality_analyzer import analyze_quality, structure_score
from app.services.recommendation_engine import generate_recommendations
from tests.helpers import read_sample

RESUME = read_sample("resume_priya_raman.txt")
JOB = read_sample("job_ml_engineer.txt")


@pytest.fixture()
def profile(processor):
    return processor.parse(RESUME)


@pytest.fixture()
def job(job_analyzer):
    return job_analyzer.analyze(JOB)


def test_weights_sum_to_one():
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)
    assert WEIGHTS == {"skills": 0.40, "semantic": 0.30, "experience": 0.15, "education": 0.10, "structure": 0.05}


def test_overall_score_matches_formula():
    s = overall_score(skills=80, semantic=60, experience=50, education=100, structure=75)
    assert s == pytest.approx(0.40 * 80 + 0.30 * 60 + 0.15 * 50 + 0.10 * 100 + 0.05 * 75, abs=0.05)
    assert overall_score(0, 0, 0, 0, 0) == 0 and overall_score(100, 100, 100, 100, 100) == 100


def test_skill_matching_buckets(profile, job):
    m = match_skills(profile["skills"], job)
    assert {"Python", "SQL", "FastAPI", "Machine Learning"} <= set(m["matched_skills"])
    assert {"Azure", "Kubernetes", "AWS", "Hugging Face"} & set(m["missing_skills"])
    assert "Docker" in m["matched_skills"]  # resume lists Docker, job lists it as preferred
    assert "Git" in m["additional_skills"] and "Python" not in m["additional_skills"]
    assert not set(m["matched_skills"]) & set(m["missing_skills"])


def test_skill_gap_priorities_follow_job_description(profile, job):
    gaps = match_skills(profile["skills"], job)["skill_gaps"]
    assert set(gaps["important"]) >= {"Kubernetes", "AWS"}  # preferred in the JD
    assert gaps["critical"] == []  # every required skill is on this resume
    assert "Terraform" in gaps["optional"]  # mentioned only in the company blurb


def test_missing_required_skill_is_critical(job_analyzer):
    job = job_analyzer.analyze("Requirements\n- Strong Rust and Kubernetes experience for production systems work.\n"
                               "Nice to have\n- Docker knowledge would help")
    gaps = match_skills([{"name": "Python", "category": "Programming", "confidence": 0.9}], job)["skill_gaps"]
    assert "Kubernetes" in gaps["critical"] and "Docker" in gaps["important"]


def test_skills_score_is_weighted(job):
    resume_skills = [{"name": n, "category": "x", "confidence": 0.9} for n in job["required_skills"]]
    all_ctx = {d["name"]: d["context"] for d in job["skill_details"]}
    total = sum(CONTEXT_WEIGHT[c] for c in all_ctx.values())
    got = sum(CONTEXT_WEIGHT[all_ctx[n]] for n in job["required_skills"])
    assert match_skills(resume_skills, job)["skills_score"] == pytest.approx(100 * got / total, abs=0.1)


def test_skills_score_zero_when_job_has_no_skills():
    assert match_skills([{"name": "Python", "category": "x", "confidence": 1}], {"skill_details": []})["skills_score"] == 0


def test_experience_relevance_entry_level(profile, job):
    m = match_skills(profile["skills"], job)["matched_skills"]
    r = experience_relevance(profile, job, m)
    assert r["required_years"] == 0 and r["years_fit"] == 1.0
    assert 0 < r["experience_score"] <= 100
    assert "Docker" in r["skills_without_evidence"]  # only appears in the skills list


def test_experience_relevance_senior_role_penalises_short_history(profile, job):
    senior = {**job, "min_years_experience": 5}
    r = experience_relevance(profile, senior, ["Python"])
    assert r["years_fit"] == pytest.approx(0.05, abs=0.01)


def test_education_relevance(profile):
    assert education_relevance(profile, {"required_education_level": "bachelor"})["education_score"] == 100
    assert education_relevance(profile, {"required_education_level": "master"})["education_score"] < 100
    assert education_relevance({"education": []}, {"required_education_level": "bachelor"})["education_score"] == 0


def test_structure_score_and_quality_for_good_resume(profile):
    assert structure_score(profile, RESUME) == 100
    q = analyze_quality(profile, RESUME, 1)
    assert q["quality_score"] >= 90


def test_quality_flags_weak_resume(processor):
    weak_text = "John Doe\n\nSKILLS\nPython\n\nPROJECTS\nToy app\n- made an app\n- made a website\n- made a game"
    p = processor.parse(weak_text)
    q = analyze_quality(p, weak_text, 1)
    types = {i["type"] for i in q["issues"]}
    assert {"missing_contact_email", "missing_education", "missing_metric", "too_short",
            "weak_project_description", "repeated_bullet_opener"} <= types
    assert q["quality_score"] < 60
    assert all({"type", "message"} <= set(i) for i in q["issues"])


def test_quality_job_specific_missing_skills(profile):
    q = analyze_quality(profile, RESUME, 1, missing_required_skills=["Rust", "Kubernetes"])
    assert any(i["type"] == "missing_relevant_skills" and "Rust" in i["message"] for i in q["issues"])


def test_recommendations_explain_why_and_never_invent(profile, job_analyzer, embedder):
    from types import SimpleNamespace
    from app.services.matching_service import full_match
    job = job_analyzer.analyze("Requirements\n- Strong Rust programming skills and Kubernetes experience required.\n"
                               "- Experience with Python and Docker\nNice to have\n- Terraform knowledge")
    job_row = SimpleNamespace(analysis=job, raw_text="Rust Kubernetes Python Docker Terraform", embedding=None)
    resume_row = SimpleNamespace(embeddings=None, raw_text=RESUME)
    match = full_match(resume_row, job_row, profile, embedder, 0.45, "test")
    quality = analyze_quality(profile, RESUME, 1, match["skills"]["skill_gaps"]["critical"])
    recs = generate_recommendations(profile, job, match, quality)

    assert recs and all(r["reason"] and r["message"] and r["title"] for r in recs)
    rust = next(r for r in recs if "Rust" in r["title"])
    assert rust["priority"] == "high" and "was not detected in the resume" in rust["message"]
    assert "If you have Rust experience" in rust["message"]  # conditional, never asserts the user has it
    # recommendations only mention skills that appear in the job description or the resume
    allowed = set(job["required_skills"] + job["preferred_skills"] + [s["name"] for s in profile["skills"]])
    assert "Rust" in allowed
    assert not any("PyTorch" in r["message"] or "AWS" in r["message"] for r in recs)
    assert [r["priority"] for r in recs] == sorted([r["priority"] for r in recs],
                                                   key=lambda p: ["high", "medium", "low", "info"].index(p))


def test_evaluation_script_computes_metrics_from_data():
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location(
        "evaluate_models", Path(__file__).resolve().parents[1] / "evaluation" / "evaluate_models.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.prf(8, 2, 2) == {"precision": 0.8, "recall": 0.8, "f1": 0.8, "tp": 8, "fp": 2, "fn": 2}
    # a deliberately wrong gold label must lower the score: metrics are computed, not fixed
    bad = [{"text": "Experienced with Python.", "skills": ["Java"]}]
    assert mod.eval_skill_extraction(bad)["micro"]["f1"] == 0.0
    good = [{"text": "Experienced with Python.", "skills": ["Python"]}]
    assert mod.eval_skill_extraction(good)["micro"]["f1"] == 1.0
