"""Resume section detection based on heading lines."""
import re
from dataclasses import dataclass, field

SECTION_ALIASES: dict[str, list[str]] = {
    "summary": ["summary", "professional summary", "profile", "professional profile", "about me",
                "career summary", "executive summary"],
    "objective": ["objective", "career objective", "professional objective"],
    "education": ["education", "academic background", "academics", "educational qualifications",
                  "academic qualifications", "education and training", "qualifications"],
    "skills": ["skills", "technical skills", "key skills", "core competencies", "skills and tools",
               "technical proficiency", "technologies", "tools and technologies", "skills summary",
               "areas of expertise", "technical expertise"],
    "experience": ["experience", "work experience", "professional experience", "employment history",
                   "internships", "internship experience", "work history", "industry experience",
                   "relevant experience", "internship"],
    "projects": ["projects", "academic projects", "personal projects", "key projects", "project work",
                 "selected projects", "technical projects", "project experience"],
    "certifications": ["certifications", "certificates", "licenses and certifications",
                       "courses and certifications", "certifications and courses",
                       "training and certifications", "courses", "certification"],
    "achievements": ["achievements", "awards", "honors and awards", "accomplishments",
                     "awards and achievements", "extracurricular activities", "honors"],
    "publications": ["publications", "research papers", "research publications"],
}

_ALIAS_TO_SECTION = {alias: sec for sec, aliases in SECTION_ALIASES.items() for alias in aliases}


def normalize_heading(line: str) -> str:
    s = line.strip().lower().replace("&", " and ")
    s = re.sub(r"^[\W_]+|[\W_]+$", "", s)  # leading/trailing punctuation, bullets, colons
    return re.sub(r"\s+", " ", s)


def heading_to_section(line: str) -> str | None:
    """Return the canonical section name if `line` is a section heading."""
    if not line or len(line) > 50 or len(line.split()) > 6:
        return None
    if line.strip().endswith((".", ",")):
        return None
    return _ALIAS_TO_SECTION.get(normalize_heading(line))


@dataclass
class SectionResult:
    header: str = ""  # text before the first heading (name, contact details)
    sections: dict[str, str] = field(default_factory=dict)
    order: list[str] = field(default_factory=list)


def detect_sections(text: str) -> SectionResult:
    result = SectionResult()
    current: str | None = None
    buffers: dict[str, list[str]] = {}
    header_lines: list[str] = []
    for line in text.split("\n"):
        section = heading_to_section(line)
        if section:
            current = section
            buffers.setdefault(section, [])
            if section not in result.order:
                result.order.append(section)
            continue
        if current is None:
            header_lines.append(line)
        else:
            buffers[current].append(line)
    result.header = "\n".join(header_lines).strip()
    result.sections = {k: "\n".join(v).strip() for k, v in buffers.items() if "\n".join(v).strip()}
    result.order = [s for s in result.order if s in result.sections]
    return result
