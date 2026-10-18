"""Generate sample PDF and DOCX resumes from the fictional text resume (no real people)."""
from pathlib import Path

import pymupdf
from docx import Document

HERE = Path(__file__).parent


def make_pdf(text: str, path: Path) -> None:
    doc = pymupdf.open()
    page = doc.new_page()
    y = 60
    for line in text.split("\n"):
        if y > 780:
            page = doc.new_page()
            y = 60
        page.insert_text((50, y), line, fontsize=10)
        y += 14
    doc.save(path)
    doc.close()


def make_docx(text: str, path: Path) -> None:
    d = Document()
    for line in text.split("\n"):
        d.add_paragraph(line)
    d.save(path)


if __name__ == "__main__":
    t = (HERE / "resume_priya_raman.txt").read_text(encoding="utf-8")
    make_pdf(t, HERE / "resume_priya_raman.pdf")
    make_docx(t, HERE / "resume_priya_raman.docx")
    print("Created resume_priya_raman.pdf and .docx")
