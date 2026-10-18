from tests.helpers import read_sample

JOB = read_sample("job_ml_engineer.txt")


def test_required_vs_preferred_classification(job_analyzer):
    r = job_analyzer.analyze(JOB)
    assert {"Python", "Machine Learning", "Natural Language Processing", "SQL", "PostgreSQL", "FastAPI"} <= set(r["required_skills"])
    assert {"Docker", "Azure", "AWS", "Kubernetes", "Hugging Face"} <= set(r["preferred_skills"])
    assert "Docker" not in r["required_skills"]


def test_company_description_skills_are_other_not_required(job_analyzer):
    r = job_analyzer.analyze(JOB)
    assert "Terraform" in r["other_skills"] and "Terraform" not in r["required_skills"]


def test_nothing_is_invented(job_analyzer):
    r = job_analyzer.analyze(JOB)
    all_skills = set(r["required_skills"] + r["preferred_skills"] + r["responsibility_skills"] + r["other_skills"])
    assert not all_skills & {"Java", "React", "PyTorch", "MongoDB", "Django"}


def test_experience_and_education_requirements(job_analyzer):
    r = job_analyzer.analyze(JOB)
    assert r["min_years_experience"] == 0
    assert r["required_education_level"] == "bachelor"
    assert r["education_requirements"]


def test_years_extraction(job_analyzer):
    r = job_analyzer.analyze("We need a backend engineer with 3+ years of experience in Python and SQL. "
                             "This is a full time role in our Chennai office with great benefits.")
    assert r["min_years_experience"] == 3
    assert set(r["required_skills"]) == {"Python", "SQL"}


def test_mixed_clause_priority_split(job_analyzer):
    r = job_analyzer.analyze("Strong Python skills and Docker is a plus. Must know SQL; familiarity with Kubernetes is nice.")
    assert "Python" in r["required_skills"] and "SQL" in r["required_skills"]
    assert "Docker" in r["preferred_skills"] and "Kubernetes" in r["preferred_skills"]


def test_responsibilities_and_requirement_lines(job_analyzer):
    r = job_analyzer.analyze(JOB)
    assert len(r["responsibilities"]) == 3
    kinds = {x["kind"] for x in r["requirements"]}
    assert kinds == {"required", "preferred", "responsibility"}


def test_warning_when_no_skills_found(job_analyzer):
    r = job_analyzer.analyze("We are looking for a friendly person to join our small team and help with daily work.")
    assert r["required_skills"] == [] and r["warnings"]


def test_keywords_returned(job_analyzer):
    assert len(job_analyzer.analyze(JOB)["keywords"]) >= 5
