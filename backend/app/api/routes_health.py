from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_embedder
from app.database.session import get_db
from app.services.embedding_service import EmbeddingService
from app.services.nlp_processor import nlp_model_status

router = APIRouter(tags=["Health"])


@router.get("/health")
def health(db: Session = Depends(get_db), embedder: EmbeddingService = Depends(get_embedder)):
    """Liveness + dependency status. Returns 200 even if the transformer is not loaded yet
    (it loads lazily); a DB failure results in a 503 via the global handler."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok", "spacy": nlp_model_status(), "embedding_model": embedder.status}
