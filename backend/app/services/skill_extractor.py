"""Dictionary + spaCy PhraseMatcher skill extraction with heuristic confidence.

Why PhraseMatcher? It matches on spaCy *tokens*, so "Node.js", "C++" and "CI/CD" are
tokenised the same way in the dictionary and in the text. The match is therefore
token-aligned (Java does not match inside JavaScript) rather than a raw substring search.

Confidence values are HEURISTIC scores (not model probabilities). See `_confidence`.
"""
import json
import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional

from spacy.matcher import PhraseMatcher
from spacy.util import filter_spans

from app.services.skills_data import CASE_SENSITIVE, NON_TECH_CATEGORIES, SKILL_CATALOG

logger = logging.getLogger(__name__)

_SKILLS_SECTIONS = {"skills"}
_EVIDENCE_SECTIONS = {"experience", "projects"}
_CONTEXT_CUES = re.compile(
    r"\b(?:experience (?:with|in)|proficient (?:in|with)|skilled in|worked (?:with|on)|"
    r"built|developed|implemented|using|deployed|designed)\b",
    re.I,
)


@dataclass
class SkillHit:
    name: str
    category: str
    confidence: float
    mentions: int = 1
    sections: list[str] = field(default_factory=list)
    in_skills_section: bool = False
    confidence_type: str = "heuristic"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "confidence": self.confidence,
            "confidence_type": self.confidence_type,
            "mentions": self.mentions,
            "in_skills_section": self.in_skills_section,
        }


def load_catalog(custom_path: Optional[str] = None) -> dict[str, dict[str, list[str]]]:
    """Return the built-in catalog merged with an optional JSON extension file."""
    catalog = {cat: {k: list(v) for k, v in skills.items()} for cat, skills in SKILL_CATALOG.items()}
    if custom_path and Path(custom_path).exists():
        try:
            extra = json.loads(Path(custom_path).read_text(encoding="utf-8"))
            for cat, skills in extra.items():
                target = catalog.setdefault(cat, {})
                for name, aliases in skills.items():
                    target.setdefault(name, [])
                    target[name] = sorted(set(target[name]) | set(aliases))
            logger.info("Loaded custom skills from %s", custom_path)
        except (OSError, ValueError, AttributeError) as exc:
            logger.warning("Could not load custom skills file: %s", exc.__class__.__name__)
    return catalog


class SkillExtractor:
    def __init__(self, nlp, catalog: Optional[dict] = None):
        self.nlp = nlp
        self.catalog = catalog or load_catalog()
        self.category_of: dict[str, str] = {}
        self._alias_to_canonical: dict[str, str] = {}  # lower-cased alias -> canonical
        self._ci = PhraseMatcher(nlp.vocab, attr="LOWER")
        self._cs = PhraseMatcher(nlp.vocab, attr="ORTH")
        self._build()

    def _build(self) -> None:
        ci_patterns, cs_patterns = {}, {}
        for category, skills in self.catalog.items():
            for canonical, aliases in skills.items():
                self.category_of[canonical] = category
                for alias in {canonical, *aliases}:
                    self._alias_to_canonical[alias.lower()] = canonical
                    pattern_doc = self.nlp.make_doc(alias)
                    target = cs_patterns if (alias in CASE_SENSITIVE or len(alias) <= 2) else ci_patterns
                    target.setdefault(canonical, []).append(pattern_doc)
        for canonical, docs in ci_patterns.items():
            self._ci.add(canonical, docs)
        for canonical, docs in cs_patterns.items():
            self._cs.add(canonical, docs)

    # ---------------------------------------------------------------- normalise
    def normalize(self, name: str) -> Optional[str]:
        """Map any alias to its canonical skill name ('JS' -> 'JavaScript'); None if unknown."""
        return self._alias_to_canonical.get((name or "").strip().lower())

    def is_technical(self, canonical: str) -> bool:
        return self.category_of.get(canonical) not in NON_TECH_CATEGORIES

    # ------------------------------------------------------------------ extract
    def find_in_text(self, text: str) -> list[tuple[str, int, int]]:
        """Return non-overlapping (canonical_name, start_char, end_char) matches (longest wins)."""
        if not text:
            return []
        doc = self.nlp.make_doc(text)
        spans = []
        for matcher in (self._ci, self._cs):
            for match_id, start, end in matcher(doc):
                span = doc[start:end]
                span.label_ = self.nlp.vocab.strings[match_id]
                spans.append(span)
        results = []
        for s in filter_spans(spans):
            # "TF-IDF" is not TensorFlow: reject short aliases glued to a hyphenated word.
            if len(s.text) <= 3 and re.match(r"-[A-Za-z]", text[s.end_char:s.end_char + 2]):
                continue
            results.append((s.label_, s.start_char, s.end_char))
        return results

    def extract(self, text: str, sections: Optional[dict[str, str]] = None) -> list[SkillHit]:
        """Extract skills from a whole resume. If `sections` is given, location in the
        resume (skills list vs. experience/project evidence) feeds the confidence heuristic."""
        sections = sections or {"unknown": text}
        counts: dict[str, dict[str, int]] = {}
        cue_hits: dict[str, bool] = {}
        for section_name, section_text in sections.items():
            for canonical, start, end in self.find_in_text(section_text):
                counts.setdefault(canonical, {}).setdefault(section_name, 0)
                counts[canonical][section_name] += 1
                window = section_text[max(0, start - 60):end + 20]
                if _CONTEXT_CUES.search(window):
                    cue_hits[canonical] = True

        hits = []
        for canonical, per_section in counts.items():
            mentions = sum(per_section.values())
            hits.append(
                SkillHit(
                    name=canonical,
                    category=self.category_of.get(canonical, "Other"),
                    confidence=self._confidence(per_section, mentions, cue_hits.get(canonical, False)),
                    mentions=mentions,
                    sections=sorted(per_section),
                    in_skills_section=any(s in _SKILLS_SECTIONS for s in per_section),
                )
            )
        return sorted(hits, key=lambda h: (-h.confidence, h.name))

    @staticmethod
    def _confidence(per_section: dict[str, int], mentions: int, has_cue: bool) -> float:
        """HEURISTIC confidence (not a probability): base 0.60, +0.20 if listed in a skills
        section, +0.10 if evidenced in experience/projects, +0.05 for repeated mentions,
        +0.05 for a usage cue such as 'built with'. Capped at 0.95."""
        score = 0.60
        if any(s in _SKILLS_SECTIONS for s in per_section):
            score += 0.20
        if any(s in _EVIDENCE_SECTIONS for s in per_section):
            score += 0.10
        if mentions > 1:
            score += 0.05
        if has_cue:
            score += 0.05
        return round(min(score, 0.95), 2)


@lru_cache
def get_skill_extractor() -> SkillExtractor:
    from app.core.config import get_settings
    from app.services.nlp_processor import get_nlp

    return SkillExtractor(get_nlp(), load_catalog(get_settings().custom_skills_path))
