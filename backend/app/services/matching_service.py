"""Resume <-> job matching: skill matching, skill-gap analysis, semantic similarity and the
transparent overall score.

overall = 0.40*skills + 0.30*semantic + 0.15*experience + 0.10*education + 0.05*structure

The overall score is a Resume-Job Match Score. It is NOT a hiring probability.
"""
import logging
from typing import Optional

import numpy as np

from app.services.embedding_service import EmbeddingService
from app.services.nlp_processor import LEVEL_NAMES
from app.services.quality_analyzer import structure_score
from app.utils.text import is_bullet, strip_bullet

logger = logging.getLogger(__name__)

WEIGHTS = {"skills": 0.40, "semantic": 0.30, "experience": 0.15, "education": 0.10, "structure": 0.05}
# How much each job-skill context contributes to the skills score.
CONTEXT_WEIGHT = {"required": 1.0, "preferred": 0.5, "responsibility": 0.5, "other": 0.25}
PRIORITY_OF_CONTEXT = {"required": "critical", "preferred": "important", "responsibility": "important", "other": "optional"}
_LEVEL_RANK = {v: k for k, v in LEVEL_NAMES.items()}


# ------------------------------------------------------------------ skill matching
def match_skills(resume_skills: list[dict], job: dict) -> dict:
    """Compare normalised resume skills with normalised job skills."""
    resume = {s["name"]: s for s in resume_skills}
    job_skills = job.get("skill_details", [])
    job_names = {s["name"] for s in job_skills}

    matched, missing = [], []
    for s in job_skills:
        entry = {"name": s["name"], "category": s["category"], "context": s["context"]}
        if s["name"] in resume:
            matched.append({**entry, "resume_confidence": resume[s["name"]]["confidence"]})
        else:
            missing.append({**entry, "priority": PRIORITY_OF_CONTEXT[s["context"]]})
    additional = [{"name": n, "category": s["category"]} for n, s in resume.items() if n not in job_names]

    total_w = sum(CONTEXT_WEIGHT[s["context"]] for s in job_skills)
    got_w = sum(CONTEXT_WEIGHT[m["context"]] for m in matched)
    skills_score = round(100 * got_w / total_w, 1) if total_w else 0.0

    return {
        "matched_skills": [m["name"] for m in matched],
        "missing_skills": [m["name"] for m in missing],
        "additional_skills": [a["name"] for a in additional],
        "matched_details": matched,
        "missing_details": missing,
        "additional_details": additional,
        "skill_gaps": {
            "critical": [m["name"] for m in missing if m["priority"] == "critical"],
            "important": [m["name"] for m in missing if m["priority"] == "important"],
            "optional": [m["name"] for m in missing if m["priority"] == "optional"],
        },
        "skills_score": skills_score,
    }


# ------------------------------------------------------------------------ semantic
def _resume_lines(profile: dict, limit: int = 150) -> list[str]:
    lines: list[str] = []
    for name, text in profile.get("sections", {}).items():
        if name in {"education"}:
            continue
        for raw in text.split("\n"):
            line = strip_bullet(raw)
            if len(line.split()) >= 4:
                lines.append(line)
    return list(dict.fromkeys(lines))[:limit]


def semantic_analysis(resume, job, profile: dict, job_analysis: dict, embedder: EmbeddingService,
                      coverage_threshold: float, model_name: str) -> dict:
    """Embeddings for the full documents, resume sections and individual job requirements.

    Document/section vectors are cached on the DB rows so the model is not re-run for the same text.
    Returns plain dicts; `cache_updates` tells the caller which DB fields to persist.
    """
    cache = resume.embeddings if resume.embeddings and resume.embeddings.get("model") == model_name else None
    cache_updates: dict = {}

    if cache and "document" in cache:
        resume_vec = np.asarray(cache["document"], dtype=np.float32)
        section_vecs = {k: np.asarray(v, dtype=np.float32) for k, v in cache.get("sections", {}).items()}
    else:
        resume_vec = embedder.embed_document(resume.raw_text)
        section_vecs = {n: embedder.embed_document(t) for n, t in profile.get("sections", {}).items() if t.strip()}
        cache_updates["resume"] = {
            "model": model_name,
            "document": resume_vec.tolist(),
            "sections": {k: v.tolist() for k, v in section_vecs.items()},
        }

    if job.embedding and job.analysis.get("_embedding_model") == model_name:
        job_vec = np.asarray(job.embedding, dtype=np.float32)
    else:
        job_vec = embedder.embed_document(job.raw_text)
        cache_updates["job"] = job_vec.tolist()

    similarity = max(0.0, min(1.0, embedder.cosine(resume_vec, job_vec)))
    section_similarity = {
        n: round(max(0.0, embedder.cosine(v, job_vec)), 4)
        for n, v in section_vecs.items() if n not in {"education"}
    }

    # requirement-level coverage: best-matching resume line for each job requirement
    requirements = job_analysis.get("requirements", [])
    lines = _resume_lines(profile)
    coverage = []
    if requirements and lines:
        req_vecs = embedder.embed_texts([r["text"] for r in requirements])
        line_vecs = embedder.embed_texts(lines)
        sims = req_vecs @ line_vecs.T
        for i, req in enumerate(requirements):
            j = int(np.argmax(sims[i]))
            best = float(sims[i, j])
            coverage.append({
                "requirement": req["text"],
                "kind": req["kind"],
                "best_similarity": round(best, 4),
                "best_match": lines[j],
                "covered": best >= coverage_threshold,
            })
    coverage_ratio = round(sum(c["covered"] for c in coverage) / len(coverage), 3) if coverage else None

    return {
        "semantic_similarity": round(similarity, 4),
        "semantic_score": round(similarity * 100, 1),
        "section_similarity": section_similarity,
        "requirement_coverage": coverage,
        "coverage_ratio": coverage_ratio,
        "coverage_threshold": coverage_threshold,
        "cache_updates": cache_updates,
    }


# ------------------------------------------------------------ experience / education
def experience_relevance(profile: dict, job: dict, matched_names: list[str]) -> dict:
    """50% years-of-experience fit + 50% evidence that matched skills were used in experience/projects."""
    months = profile.get("total_experience_months", 0) or 0
    min_years = job.get("min_years_experience")
    has_exp = bool(profile.get("experience"))
    has_projects = bool(profile.get("projects"))

    if min_years is None:
        years_fit = 0.7 if has_exp else (0.4 if has_projects else 0.0)
        note = "No years of experience stated in the job description."
    elif min_years == 0:
        years_fit = 1.0 if (has_exp or has_projects) else 0.5
        note = "The job description is entry-level."
    else:
        years_fit = min(1.0, (months / 12) / min_years)
        note = f"Job asks for {min_years}+ years; about {months / 12:.1f} years were computed from dated entries."

    evidence_pool = {s for e in profile.get("experience", []) for s in e.get("skills", [])}
    evidence_pool |= {t for p in profile.get("projects", []) for t in p.get("technologies", [])}
    shown = [n for n in matched_names if n in evidence_pool]
    evidence = len(shown) / len(matched_names) if matched_names else 0.0
    return {
        "experience_score": round(100 * (0.5 * years_fit + 0.5 * evidence), 1),
        "years_fit": round(years_fit, 2),
        "skill_evidence_ratio": round(evidence, 2),
        "skills_without_evidence": [n for n in matched_names if n not in evidence_pool],
        "candidate_experience_months": months,
        "required_years": min_years,
        "note": note,
    }


def education_relevance(profile: dict, job: dict) -> dict:
    """Degree-level fit. A degree in progress counts (typical for final-year students)."""
    levels = [_LEVEL_RANK[e["level"]] for e in profile.get("education", []) if e.get("level") in _LEVEL_RANK]
    required = job.get("required_education_level")
    if not profile.get("education"):
        return {"education_score": 0.0, "candidate_level": None, "required_level": required,
                "note": "No education entries were detected."}
    candidate = max(levels) if levels else None
    if required is None:
        score, note = 100.0, "The job description states no education requirement."
    elif candidate is None:
        score, note = 30.0, "Education entries were found, but no degree level could be identified."
    elif candidate >= _LEVEL_RANK[required]:
        score, note = 100.0, f"Highest detected level ({LEVEL_NAMES[candidate]}) meets the required level ({required})."
    else:
        score = round(100 * (candidate + 1) / (_LEVEL_RANK[required] + 1), 1)
        note = f"Highest detected level ({LEVEL_NAMES[candidate]}) is below the required level ({required})."
    return {"education_score": score, "candidate_level": LEVEL_NAMES.get(candidate) if candidate is not None else None,
            "required_level": required, "note": note}


# ---------------------------------------------------------------------- overall
def overall_score(skills: float, semantic: float, experience: float, education: float, structure: float) -> float:
    return round(
        WEIGHTS["skills"] * skills
        + WEIGHTS["semantic"] * semantic
        + WEIGHTS["experience"] * experience
        + WEIGHTS["education"] * education
        + WEIGHTS["structure"] * structure,
        1,
    )


def full_match(resume, job, profile: dict, embedder: EmbeddingService, coverage_threshold: float,
               model_name: str) -> dict:
    """Run every matching component and return one result dict (no DB writes)."""
    job_analysis = job.analysis
    sk = match_skills(profile["skills"], job_analysis)
    sem = semantic_analysis(resume, job, profile, job_analysis, embedder, coverage_threshold, model_name)
    exp = experience_relevance(profile, job_analysis, sk["matched_skills"])
    edu = education_relevance(profile, job_analysis)
    struct = structure_score(profile, resume.raw_text)
    total = overall_score(sk["skills_score"], sem["semantic_score"], exp["experience_score"],
                          edu["education_score"], struct)
    return {
        "skills": sk, "semantic": sem, "experience": exp, "education": edu,
        "structure_score": struct, "overall_score": total,
        "component_scores": {
            "skills": sk["skills_score"], "semantic": sem["semantic_score"], "experience": exp["experience_score"],
            "education": edu["education_score"], "structure": struct,
        },
        "weights": WEIGHTS,
    }
