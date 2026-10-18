"""PDF text extraction with PyMuPDF."""
import logging

import pymupdf

from app.core.exceptions import CorruptedDocumentError, EmptyDocumentError

logger = logging.getLogger(__name__)


def extract_pdf(data: bytes) -> dict:
    """Return {"text", "page_count", "file_type"} or raise a clean AppError."""
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:  # PyMuPDF raises several error types for invalid input
        logger.warning("PDF could not be opened: %s", exc.__class__.__name__)
        raise CorruptedDocumentError("The PDF could not be read. It may be corrupted.") from exc

    try:
        if doc.needs_pass:
            raise CorruptedDocumentError("The PDF is password protected and cannot be processed.")
        pages = []
        for page in doc:
            # sort=True returns text blocks in reading order (top-to-bottom, left-to-right)
            pages.append(page.get_text("text", sort=True))
        page_count = doc.page_count
    except CorruptedDocumentError:
        raise
    except Exception as exc:
        logger.warning("PDF text extraction failed: %s", exc.__class__.__name__)
        raise CorruptedDocumentError("Text could not be extracted from this PDF.") from exc
    finally:
        doc.close()

    text = "\n".join(pages).strip()
    if not text:
        raise EmptyDocumentError(
            "No text found in this PDF. Scanned/image-only PDFs need OCR, which is not supported yet."
        )
    return {"text": text, "page_count": page_count, "file_type": "pdf"}
