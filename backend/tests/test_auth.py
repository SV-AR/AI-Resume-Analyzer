from app.core.security import create_access_token, hash_password, verify_password

REG = {"email": "a@example.com", "full_name": "Asha Student", "password": "Passw0rd123"}


def test_password_hashing_is_salted_and_verifiable():
    h1, h2 = hash_password("Secret123"), hash_password("Secret123")
    assert h1 != h2 and "Secret123" not in h1
    assert verify_password("Secret123", h1) and not verify_password("Wrong123", h1)
    assert verify_password("x" * 200, hash_password("x" * 200))  # no 72-byte truncation surprises


def test_register_login_and_me(client):
    r = client.post("/api/auth/register", json=REG)
    assert r.status_code == 201
    assert "password" not in r.text and "hashed" not in r.text
    r = client.post("/api/auth/login", json={"email": REG["email"], "password": REG["password"]})
    assert r.status_code == 200 and r.json()["token_type"] == "bearer"
    token = r.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200 and me.json()["email"] == REG["email"]


def test_duplicate_email_conflict_case_insensitive(client):
    client.post("/api/auth/register", json=REG)
    r = client.post("/api/auth/register", json={**REG, "email": "A@Example.com"})
    assert r.status_code == 409


def test_wrong_password_and_unknown_user_have_same_error(client):
    client.post("/api/auth/register", json=REG)
    bad = client.post("/api/auth/login", json={"email": REG["email"], "password": "Nope12345"})
    unknown = client.post("/api/auth/login", json={"email": "who@example.com", "password": "Nope12345"})
    assert bad.status_code == unknown.status_code == 401
    assert bad.json() == unknown.json()


def test_weak_or_invalid_registration_rejected(client):
    assert client.post("/api/auth/register", json={**REG, "password": "short1"}).status_code == 422
    assert client.post("/api/auth/register", json={**REG, "password": "onlyletters"}).status_code == 422
    assert client.post("/api/auth/register", json={**REG, "email": "not-an-email"}).status_code == 422
    assert client.post("/api/auth/register", json={"email": "a@b.co"}).status_code == 422


def test_swagger_form_token_endpoint(client):
    client.post("/api/auth/register", json=REG)
    r = client.post("/api/auth/token", data={"username": REG["email"], "password": REG["password"]})
    assert r.status_code == 200 and r.json()["access_token"]


def test_protected_endpoints_require_token(client):
    for method, url in [("get", "/api/resumes"), ("get", "/api/dashboard"), ("get", "/api/jobs/1"),
                        ("get", "/api/matching/1"), ("post", "/api/jobs/analyze"), ("post", "/api/resumes/upload")]:
        assert getattr(client, method)(url).status_code == 401, url


def test_invalid_and_tampered_tokens_rejected(client):
    assert client.get("/api/resumes", headers={"Authorization": "Bearer garbage"}).status_code == 401
    token = create_access_token("1", expires_minutes=-1)  # already expired
    assert client.get("/api/resumes", headers={"Authorization": f"Bearer {token}"}).status_code == 401
    good = create_access_token("999")  # valid signature, user does not exist
    assert client.get("/api/resumes", headers={"Authorization": f"Bearer {good}"}).status_code == 401
