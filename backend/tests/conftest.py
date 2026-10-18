import os
import tempfile

# Settings must be in place BEFORE the app is imported.
_TMP = tempfile.mkdtemp(prefix="resume_tests_")
os.environ.update({
    "JWT_SECRET_KEY": "test-secret-key-for-pytest-only-0123456789",
    "DATABASE_URL": f"sqlite:///{_TMP}/test.db",
    "UPLOAD_DIR": f"{_TMP}/uploads",
    "ENVIRONMENT": "test",
    "MAX_UPLOAD_MB": "1",
})

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api.deps import get_embedder  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.database.session import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.services.embedding_service import EmbeddingService  # noqa: E402
from app.services.job_analyzer import JobAnalyzer  # noqa: E402
from app.services.nlp_processor import ResumeNLPProcessor, get_nlp  # noqa: E402
from app.services.skill_extractor import get_skill_extractor  # noqa: E402
from tests.helpers import HashingEncoder  # noqa: E402


@pytest.fixture(scope="session")
def embedder():
    return EmbeddingService(HashingEncoder())


@pytest.fixture(scope="session")
def extractor():
    return get_skill_extractor()


@pytest.fixture(scope="session")
def processor():
    return ResumeNLPProcessor()


@pytest.fixture(scope="session")
def job_analyzer():
    return JobAnalyzer()


@pytest.fixture(scope="session")
def nlp():
    return get_nlp()


@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture()
def client(embedder):
    app.dependency_overrides[get_embedder] = lambda: embedder
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_client(client):
    client.post("/api/auth/register", json={"email": "student@example.com", "full_name": "Test Student",
                                            "password": "Passw0rdTest"})
    r = client.post("/api/auth/login", json={"email": "student@example.com", "password": "Passw0rdTest"})
    client.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    return client
