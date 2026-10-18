import json

import pytest

from app.services.skill_extractor import SkillExtractor, load_catalog


@pytest.mark.parametrize("alias,canonical", [
    ("JS", "JavaScript"), ("js", "JavaScript"), ("Postgres", "PostgreSQL"), ("ML", "Machine Learning"),
    ("NLP", "Natural Language Processing"), ("TF", "TensorFlow"), ("sklearn", "Scikit-learn"),
    ("K8s", "Kubernetes"), ("Node.js", "Node.js"), ("Microsoft Azure", "Azure"),
])
def test_skill_normalization(extractor, alias, canonical):
    assert extractor.normalize(alias) == canonical


def test_unknown_skill_not_normalized(extractor):
    assert extractor.normalize("Underwater Basket Weaving") is None


def _names(extractor, text):
    return {n for n, _, _ in extractor.find_in_text(text)}


def test_aliases_are_normalized_in_text(extractor):
    found = _names(extractor, "I use JS, Postgres and ML daily; also NLP.")
    assert {"JavaScript", "PostgreSQL", "Machine Learning", "Natural Language Processing"} <= found


def test_java_does_not_match_inside_javascript(extractor):
    assert _names(extractor, "Worked with JavaScript only") == {"JavaScript"}


def test_c_and_cpp_distinguished(extractor):
    assert _names(extractor, "Languages: C, C++") == {"C", "C++"}


def test_case_sensitive_ambiguous_words_do_not_match(extractor):
    found = _names(extractor, "The rest of the team can excel in go-to-market work.")
    assert not found & {"REST API", "Excel", "Go"}


def test_tf_idf_is_not_tensorflow(extractor):
    assert "TensorFlow" not in _names(extractor, "Used TF-IDF features for classification")


def test_longest_match_wins(extractor):
    found = _names(extractor, "Experience in Natural Language Processing and Machine Learning")
    assert found == {"Natural Language Processing", "Machine Learning"}


def test_extract_returns_heuristic_confidence_with_section_context(extractor):
    sections = {"skills": "Python, Docker", "experience": "Built an API using Python."}
    hits = {h.name: h for h in extractor.extract("", sections)}
    assert hits["Python"].confidence > hits["Docker"].confidence  # skills list + usage evidence
    assert all(h.confidence_type == "heuristic" for h in hits.values())
    assert all(0 < h.confidence <= 0.95 for h in hits.values())
    d = hits["Python"].to_dict()
    assert set(d) >= {"name", "category", "confidence", "confidence_type"}
    assert d["category"] == "Programming"


def test_required_skills_present_in_dictionary(extractor):
    for name in ["Java", "Python", "C", "C++", "JavaScript", "React", "HTML", "CSS", "Tailwind CSS", "Node.js",
                 "Express", "FastAPI", "Django", "MySQL", "PostgreSQL", "MongoDB", "Redis", "Machine Learning",
                 "Deep Learning", "Natural Language Processing", "Computer Vision", "Transformers", "Scikit-learn",
                 "TensorFlow", "PyTorch", "AWS", "Azure", "Docker", "Kubernetes", "Git", "GitHub", "Postman"]:
        assert name in extractor.category_of, name


def test_custom_skills_file_extends_dictionary(tmp_path, nlp):
    f = tmp_path / "custom.json"
    f.write_text(json.dumps({"AI/ML": {"LangChain": ["lang-chain"]}}))
    ex = SkillExtractor(nlp, load_catalog(str(f)))
    assert ex.normalize("lang-chain") == "LangChain"
    assert {n for n, _, _ in ex.find_in_text("Built agents with LangChain")} == {"LangChain"}
