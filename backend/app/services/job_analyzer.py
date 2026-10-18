"""Job description analysis.

Skills are only reported if they appear in the text (nothing is invented). Each skill gets
a *context* so priorities are based on what the job description actually says:

  required        -> in a requirements/qualifications section, or a clause with a "must/required" cue
  preferred       -> in a "nice to have/preferred" section, or a clause such as "... is a plus"
  responsibility  -> only mentioned under responsibilities / duties
  other           -> mentioned elsewhere (e.g. company description)

If the posting has no recognisable headings, every skill is treated as required unless its
clause carries a preferred cue.
"""
import re
from collections import Counter
from typing import Optional

from app.services.nlp_processor import DATE_RANGE_RE, LEVEL_NAMES, ResumeNLPProcessor, get_nlp  # noqa: F401
from app.services.skill_extractor import SkillExtractor, get_skill_extractor
from app.utils.text import is_bullet, strip_bullet

_REQ_HEADINGS = [
    "requirements", "required skills", "required qualifications", "qualifications", "must have", "must haves",
    "what you'll need", "what you need", "minimum qualifications", "basic qualifications", "skills required",
    "key skills", "technical skills", "skills and qualifications", "who you are", "what we're looking for",
    "what we are looking for", "you have", "you will bring", "your profile", "eligibility", "skills",
    "required experience", "requirements and qualifications",
]
_PREF_HEADINGS = [
    "preferred", "preferred skills", "preferred qualifications", "nice to have", "nice to haves", "good to have",
    "bonus", "bonus points", "desired skills", "desirable", "added advantage", "preferred experience",
    "additional qualifications", "plus", "pluses",
]
_RESP_HEADINGS = [
    "responsibilities", "key responsibilities", "what you'll do", "what you will do", "role and responsibilities",
    "roles and responsibilities", "duties", "your role", "the role", "day to day", "about the role", "job duties",
]
_OTHER_HEADINGS = ["about us", "about the company", "who we are", "benefits", "perks", "what we offer", "why join us",
                   "company overview", "about", "overview"]

_PREF_CUES = re.compile(
    r"\b(preferred|nice to have|good to have|bonus|a plus|is a plus|are a plus|desirable|added advantage|"
    r"advantage|familiarity with|exposure to|plus)\b", re.I)
_REQ_CUES = re.compile(
    r"\b(required|requires?|must|mandatory|proficien\w+|strong|expertise|hands-on|experience (?:with|in)|"
    r"solid understanding|minimum)\b", re.I)

_YEARS_RE = re.compile(r"(\d{1,2})\s*\+?\s*(?:(?:to|-|–)\s*(\d{1,2})\s*\+?\s*)?(?:years?|yrs?)", re.I)
_FRESHER_RE = re.compile(r"\b(fresher|freshers|entry[- ]level|recent graduate|new grad|0\s*(?:-|to)\s*1 years?)\b", re.I)
_EDU_RE = re.compile(r"\b(bachelor'?s?|master'?s?|b\.?\s?tech|b\.?\s?e\b|m\.?\s?tech|b\.?\s?sc|m\.?\s?sc|mca|bca|"
                     r"degree|ph\.?d|diploma|graduat\w+)\b", re.I)

_EDU_LEVELS = [(re.compile(r"ph\.?d|doctorate", re.I), 4),
               (re.compile(r"master|m\.?\s?tech|m\.?\s?sc|mca|mba", re.I), 3),
               (re.compile(r"bachelor|b\.?\s?tech|b\.?\s?e\b|b\.?\s?sc|bca|graduat|degree", re.I), 2),
               (re.compile(r"diploma", re.I), 1)]


def _heading_kind(line: str) -> Optional[str]:
    s = re.sub(r"[#*_:]+", " ", line).strip().lower()
    s = re.sub(r"\([^)]*\)", "", s).strip(" -–—:")
    if not s or len(s.split()) > 7 or is_bullet(line):
        return None
    for kind, names in (("preferred", _PREF_HEADINGS), ("required", _REQ_HEADINGS),
                        ("responsibility", _RESP_HEADINGS), ("other", _OTHER_HEADINGS)):
        if s in names or (line.strip().endswith(":") and any(s.startswith(n) for n in names if len(n) > 4)):
            return kind
    return None


def _clauses(line: str) -> list[str]:
    return [c for c in re.split(r";|\.\s|\sbut\s|\swhile\s", line) if c.strip()]


class JobAnalyzer:
    def __init__(self, nlp=None, extractor: Optional[SkillExtractor] = None):
        self.nlp = nlp or get_nlp()
        self.extractor = extractor or get_skill_extractor()

    def analyze(self, text: str) -> dict:
        lines = [l.strip() for l in text.split("\n")]
        # 1) assign each line a section context
        context = None
        structured = False
        tagged: list[tuple[str, str]] = []  # (line, context)
        for line in lines:
            if not line:
                continue
            kind = _heading_kind(line)
            if kind:
                context, structured = kind, True
                continue
            tagged.append((line, context or "unlabelled"))

        # 2) classify skills per clause
        priority = {"required": 4, "preferred": 3, "responsibility": 2, "other": 1}
        best: dict[str, str] = {}
        mentions: Counter = Counter()
        for line, ctx in tagged:
            for clause in _clauses(line):
                for clause_ctx, sub in self._split_mixed(clause, ctx, structured):
                    for name, _, _ in self.extractor.find_in_text(sub):
                        mentions[name] += 1
                        if priority[clause_ctx] > priority.get(best.get(name, ""), 0):
                            best[name] = clause_ctx

        by_ctx = {k: [] for k in priority}
        for name, ctx in best.items():
            by_ctx[ctx].append(name)
        for v in by_ctx.values():
            v.sort(key=lambda n: (-mentions[n], n))

        skill_details = [
            {"name": n, "category": self.extractor.category_of.get(n, "Other"), "context": c, "mentions": mentions[n]}
            for c in priority for n in by_ctx[c]
        ]
        exp = self._experience_requirements(tagged)
        edu = self._education_requirements(tagged)
        responsibilities = [strip_bullet(l) for l, c in tagged if c == "responsibility"][:15]

        warnings = []
        if not best:
            warnings.append("No known skills were detected in this job description, so skill matching will be empty.")
        if not structured:
            warnings.append("No section headings detected: skills were treated as required unless marked as preferred.")

        return {
            "required_skills": by_ctx["required"],
            "preferred_skills": by_ctx["preferred"],
            "responsibility_skills": by_ctx["responsibility"],
            "other_skills": by_ctx["other"],
            "skill_details": skill_details,
            "technologies": sorted(n for n in best if self.extractor.is_technical(n)),
            "experience_requirements": exp["items"],
            "min_years_experience": exp["min_years"],
            "education_requirements": edu["items"],
            "required_education_level": edu["level"],
            "responsibilities": responsibilities,
            "keywords": self._keywords(text),
            "requirements": self._requirement_lines(tagged, structured),
            "structure_detected": structured,
            "warnings": warnings,
        }

    # ------------------------------------------------------------------ helpers
    def _split_mixed(self, clause: str, ctx: str, structured: bool) -> list[tuple[str, str]]:
        """Resolve the context of a clause. Mixed clauses ("strong Python and Docker is a plus")
        are split so each part gets its own context."""
        base = {"required": "required", "preferred": "preferred", "responsibility": "responsibility",
                "other": "other"}.get(ctx, "required")
        has_pref, has_req = bool(_PREF_CUES.search(clause)), bool(_REQ_CUES.search(clause))
        if ctx == "other":
            return [("other", clause)]
        if has_pref and has_req:
            parts = [p for p in re.split(r",|\sand\s|\sor\s", clause) if p.strip()]
            return [("preferred" if _PREF_CUES.search(p) else base, p) for p in parts]
        if has_pref:
            return [("preferred", clause)]
        if has_req and ctx == "responsibility":
            return [("required", clause)]
        return [(base, clause)]

    @staticmethod
    def _experience_requirements(tagged) -> dict:
        items, mins, seen = [], [], set()
        for line, _ in tagged:
            for clause in _clauses(line):
                text = strip_bullet(clause).strip()
                if text in seen or not (re.search(r"experience|exposure|background", clause, re.I)
                                        or _FRESHER_RE.search(clause)):
                    continue
                years = list(_YEARS_RE.finditer(clause))
                if years:
                    for m in years:
                        lo = int(m.group(1))
                        items.append({"text": text, "min_years": lo, "max_years": int(m.group(2)) if m.group(2) else None})
                        mins.append(lo)
                elif _FRESHER_RE.search(clause):
                    items.append({"text": text, "min_years": 0, "max_years": 1})
                    mins.append(0)
                else:
                    continue
                seen.add(text)
        return {"items": items[:6], "min_years": max(mins) if mins else None}

    @staticmethod
    def _education_requirements(tagged) -> dict:
        items, levels = [], []
        for line, _ in tagged:
            if _EDU_RE.search(line) and len(line.split()) <= 40:
                text = strip_bullet(line)
                if text not in items:
                    items.append(text)
                for pat, lvl in _EDU_LEVELS:
                    if pat.search(line):
                        levels.append(lvl)
                        break
        level = LEVEL_NAMES[min(levels)] if levels else None  # lowest acceptable level
        return {"items": items[:5], "level": level}

    def _keywords(self, text: str, top_n: int = 12) -> list[str]:
        """Frequency-based important keywords: lemmatised noun chunks without stop words."""
        doc = self.nlp(text)
        counts: Counter = Counter()
        try:
            chunks = list(doc.noun_chunks)
        except (NotImplementedError, ValueError):  # blank pipeline has no parser
            chunks = []
        for chunk in chunks:
            words = [t.lemma_.lower() for t in chunk if not t.is_stop and not t.is_punct and t.is_alpha]
            if words and 3 <= len(" ".join(words)) <= 40:
                counts[" ".join(words)] += 1
        if not counts:
            for t in doc:
                if t.is_alpha and not t.is_stop and len(t.text) > 3:
                    counts[t.lemma_.lower() if t.lemma_ else t.text.lower()] += 1
        return [w for w, _ in counts.most_common(top_n)]

    @staticmethod
    def _requirement_lines(tagged, structured: bool) -> list[dict]:
        """Lines used for requirement-level semantic coverage."""
        kind_map = {"required": "required", "preferred": "preferred", "responsibility": "responsibility"}
        out = []
        for line, ctx in tagged:
            text = strip_bullet(line)
            if len(text.split()) < 4 or len(text.split()) > 60:
                continue
            if ctx in kind_map and (is_bullet(line) or structured):
                out.append({"text": text, "kind": kind_map[ctx]})
            elif ctx == "unlabelled" and not structured and (is_bullet(line) or len(text.split()) <= 35):
                out.append({"text": text, "kind": "required"})
        return out[:25]


def get_job_analyzer() -> JobAnalyzer:
    return JobAnalyzer()
