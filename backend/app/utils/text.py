"""Text cleaning helpers shared by the document and NLP services."""
import re
import unicodedata

_BULLET_CHARS = "•●▪■◦○◆►➢✓✔–·*"
_BULLET_RE = re.compile(rf"^\s*[{re.escape(_BULLET_CHARS)}]\s*")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(text: str) -> str:
    """Normalise unicode, strip control characters, unify bullets, collapse blank lines.

    Line structure is preserved on purpose: section detection relies on it.
    """
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    text = _CONTROL_RE.sub("", text)
    lines = []
    for line in text.split("\n"):
        line = line.replace("\t", " ")
        line = _BULLET_RE.sub("- ", line) if _BULLET_RE.match(line) and not line.strip().startswith("--") else line
        line = re.sub(r"[ ]{2,}", " ", line).strip()
        lines.append(line)
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_bullet(line: str) -> bool:
    return line.lstrip().startswith(("- ", "• ", "* "))


def strip_bullet(line: str) -> str:
    return re.sub(r"^\s*(?:-|•|\*)\s+", "", line).strip()


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))
