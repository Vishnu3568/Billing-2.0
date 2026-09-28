import pytest
from starlette.testclient import TestClient
from app.main import app
from app.core.database import db_manager


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        # Pre-test cleanup
        db = db_manager.get_database()
        db["companies"].delete_many({"name": {"$regex": "^TEST_"}})
        yield c
        # Post-test cleanup (while client/lifespan is still active)
        db["companies"].delete_many({"name": {"$regex": "^TEST_"}})


def test_create_company_success(client):
    payload = {"name": "TEST_Acme Corp"}
    response = client.post("/api/v1/companies", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "TEST_Acme Corp"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_list_companies(client):
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    names = [c["name"] for c in data]
    assert "TEST_Acme Corp" in names


def test_get_company_by_id(client):
    # Create a specific company to test ID lookup
    res = client.post("/api/v1/companies", json={"name": "TEST_Lookup Corp"})
    assert res.status_code == 201
    created_id = res.json()["id"]

    response = client.get(f"/api/v1/companies/{created_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_id
    assert data["name"] == "TEST_Lookup Corp"


def test_get_company_invalid_id(client):
    response = client.get("/api/v1/companies/invalid_id_format")
    assert response.status_code == 404


def test_update_company(client):
    res = client.post("/api/v1/companies", json={"name": "TEST_Before Update"})
    assert res.status_code == 201
    comp_id = res.json()["id"]

    # Update name
    update_res = client.put(f"/api/v1/companies/{comp_id}", json={"name": "TEST_After Update"})
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "TEST_After Update"

    # Verify retrieval
    get_res = client.get(f"/api/v1/companies/{comp_id}")
    assert get_res.json()["name"] == "TEST_After Update"


def test_duplicate_company_rejected(client):
    client.post("/api/v1/companies", json={"name": "TEST_Unique Company"})
    # Attempt duplicate
    dup_res = client.post("/api/v1/companies", json={"name": "TEST_Unique Company"})
    assert dup_res.status_code == 409
    assert "already exists" in dup_res.json()["detail"]


def test_whitespace_normalization_and_duplicate(client):
    client.post("/api/v1/companies", json={"name": "TEST_Trim Company"})
    # Attempt duplicate with whitespace
    dup_res = client.post("/api/v1/companies", json={"name": "   TEST_Trim Company   "})
    assert dup_res.status_code == 409


def test_empty_company_name_rejected(client):
    # Empty string
    res1 = client.post("/api/v1/companies", json={"name": ""})
    assert res1.status_code == 422

    # Whitespace only
    res2 = client.post("/api/v1/companies", json={"name": "    "})
    assert res2.status_code == 422


def test_deactivate_company(client):
    res = client.post("/api/v1/companies", json={"name": "TEST_Deactivate Corp"})
    assert res.status_code == 201
    comp_id = res.json()["id"]

    del_res = client.delete(f"/api/v1/companies/{comp_id}")
    assert del_res.status_code == 200
    assert del_res.json()["is_active"] is False

    # Verify state via GET
    get_res = client.get(f"/api/v1/companies/{comp_id}")
    assert get_res.json()["is_active"] is False
