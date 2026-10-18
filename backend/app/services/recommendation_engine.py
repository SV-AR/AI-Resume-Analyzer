"""Explainable recommendations.

Every recommendation is generated from the actual analysis result and carries a `reason`
that says WHY it was produced. Wording is conditional ("if you have...") and never invents
skills, projects, certifications, experience or achievements.
"""
from typing import Optional

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}


def _rec(category: str, priority: str, title: str, message: str, reason: str) -> dict:
    return {"category": category, "priority": priority, "title": title, "message": message, "reason": reason}


def generate_recommendations(profile: dict, job: dict, match: dict, quality: dict) -> list[dict]:
    recs: list[dict] = []
    sk, sem, exp, edu = match["skills"], match["semantic"], match["experience"], match["education"]

    # --- missing skills (priority comes only from how the job description labels them) ----
    for m in sk["missing_details"]:
        name, ctx = m["name"], m["context"]
        if ctx == "required":
            recs.append(_rec(
                "skill_gap", "high", f"{name} is required but was not detected",
                f"The job description requires {name}, but {name} was not detected in the resume.\n\n"
                f"Recommendation: If you have {name} experience, consider highlighting it in the skills or project section.",
                f"'{name}' appears in the job's required skills and no matching skill was found in your resume.",
            ))
        elif ctx in {"preferred", "responsibility"}:
            label = "listed as preferred" if ctx == "preferred" else "mentioned in the job responsibilities"
            recs.append(_rec(
                "skill_gap", "medium", f"{name} is {label.split(' ', 1)[0]} but was not detected",
                f"{name} is {label} in the job description, but it was not detected in the resume.\n\n"
                f"Recommendation: If you have worked with {name}, mention it where it fits (skills or projects).",
                f"'{name}' is {label} and was not found among your detected skills.",
            ))
    optional = [m["name"] for m in sk["missing_details"] if m["context"] == "other"]
    if optional:
        recs.append(_rec(
            "skill_gap", "low", "Other technologies mentioned in the posting",
            "The job description also mentions: " + ", ".join(optional) + ". These were not detected in your resume. "
            "If you have used any of them, you may add them.",
            "These skills appear only outside the requirements and responsibilities sections, so they are optional.",
        ))

    # --- skills listed but not evidenced ---------------------------------------------------
    no_evidence = [n for n in exp["skills_without_evidence"]
                   if n in sk["matched_skills"]
                   and next((d for d in sk["matched_details"] if d["name"] == n), {}).get("context") == "required"]
    if no_evidence:
        shown = ", ".join(no_evidence[:6])
        recs.append(_rec(
            "evidence", "medium", "Show where you used your matching skills",
            f"{shown} match the job's requirements but were not detected inside your experience or project descriptions.\n\n"
            "Recommendation: if you used them in a project or internship, say so in that entry.",
            "These skills were found in a skills list or elsewhere, but not in any experience/project text.",
        ))

    # --- requirement-level semantic coverage ----------------------------------------------
    weak = sorted((c for c in sem["requirement_coverage"] if not c["covered"] and c["kind"] != "responsibility"),
                  key=lambda c: c["best_similarity"])[:3]
    for c in weak:
        recs.append(_rec(
            "requirement_coverage", "medium" if c["kind"] == "required" else "low",
            "A job requirement has no close match in your resume",
            f"No line in your resume closely matches this {c['kind']} requirement: \"{c['requirement']}\".\n\n"
            "Recommendation: if you have relevant experience, consider describing it explicitly.",
            f"The most similar resume line scored {c['best_similarity']:.2f}, below the coverage threshold "
            f"of {sem['coverage_threshold']:.2f} (a tunable heuristic).",
        ))

    # --- experience ---------------------------------------------------------------------
    req_years = exp["required_years"]
    if req_years and exp["candidate_experience_months"] / 12 < req_years:
        recs.append(_rec(
            "experience", "medium", "Experience requirement may not be met",
            f"The job asks for {req_years}+ years of experience; about {exp['candidate_experience_months'] / 12:.1f} "
            "years were computed from the dated entries in your resume.\n\n"
            "Recommendation: if you have other relevant experience (internships, freelance work, open-source), "
            "list it with dates so it can be counted.",
            "Years were summed from dated Experience entries; undated or project-only work is not counted.",
        ))

    # --- education ---------------------------------------------------------------------
    if edu["education_score"] < 100:
        recs.append(_rec(
            "education", "medium", "Check your education section",
            f"{edu['note']}\n\nRecommendation: make sure your degree, institution and graduation year are clearly listed.",
            "Compared the highest degree level detected in your resume with the level stated in the job description.",
        ))

    # --- resume quality issues -------------------------------------------------------------
    advice = {
        "missing_metric": "Add numbers where you honestly can (users, accuracy, speed-up, dataset size).",
        "weak_project_description": "Describe the problem, your contribution, and the technologies for each project.",
        "missing_summary": "Consider a two-line summary that states your focus and strongest skills.",
        "excessive_length": "Trim older or less relevant details to keep the resume to one or two pages.",
        "repeated_words": "Replace repeated words with more specific language.",
        "repeated_bullet_opener": "Start bullet points with different action verbs.",
    }
    for issue in sorted(quality["issues"], key=lambda i: -i["penalty"]):
        if issue["type"] == "missing_relevant_skills" or issue["penalty"] < 4:
            continue  # already covered by skill-gap recommendations
        extra = advice.get(issue["type"], "")
        recs.append(_rec(
            "resume_quality", "high" if issue["severity"] == "high" else "medium" if issue["severity"] == "medium" else "low",
            issue["type"].replace("_", " ").capitalize(),
            (issue["message"] + (f"\n\nRecommendation: {extra}" if extra else "")).strip(),
            f"Resume Quality Analysis rule '{issue['type']}' triggered (penalty {issue['penalty']} points).",
        ))

    # --- strengths -------------------------------------------------------------------------
    req_total = len([d for d in sk["matched_details"] + sk["missing_details"] if d["context"] == "required"])
    req_hit = len([d for d in sk["matched_details"] if d["context"] == "required"])
    if req_total and req_hit / req_total >= 0.7:
        recs.append(_rec(
            "strength", "info", "Strong coverage of required skills",
            f"Your resume matches {req_hit} of {req_total} required skills.",
            "Counted required job skills that were also detected in your resume.",
        ))

    recs.sort(key=lambda r: _PRIORITY_ORDER[r["priority"]])
    for i, r in enumerate(recs):
        r["position"] = i
    return recs
