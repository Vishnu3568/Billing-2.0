import io
import pytest
from starlette.testclient import TestClient
from app.main import app
from app.core.database import db_manager


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        db = db_manager.get_database()
        # Clean up any test records
        db["companies"].delete_many({"name": {"$regex": "^TEST_"}})
        db["duty_slips"].delete_many({"duty_slip_no": {"$in": ["1", "2", "3", "4", "99", "101", "102", "103", "104", "105"]}})

        # Create a test company to attach duty slips to
        res = c.post("/api/v1/companies", json={"name": "TEST_Logistics_Corp"})
        assert res.status_code == 201
        test_company_id = res.json()["id"]

        yield c, test_company_id

        # Post-test cleanup
        db["companies"].delete_many({"name": {"$regex": "^TEST_"}})
        db["duty_slips"].delete_many({"duty_slip_no": {"$in": ["1", "2", "3", "4", "99", "101", "102", "103", "104", "105"]}})


def test_create_front_and_back_duty_slip(client):
    c, company_id = client
    front_bytes = b"FAKE_FRONT_IMAGE_CONTENT"
    back_bytes = b"FAKE_BACK_IMAGE_CONTENT"

    files = {
        "front_file": ("front.jpg", io.BytesIO(front_bytes), "image/jpeg"),
        "back_file": ("back.jpg", io.BytesIO(back_bytes), "image/jpeg"),
    }
    data = {
        "company_id": company_id,
        "duty_slip_no": "1",
        "notes": "Urgent trip"
    }

    response = c.post("/api/v1/duty-slips", data=data, files=files)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["duty_slip_no"] == "1"
    assert res_data["company_id"] == company_id
    assert res_data["company_name"] == "TEST_Logistics_Corp"
    assert res_data["status"] == "uploaded"
    assert res_data["notes"] == "Urgent trip"
    assert res_data["has_back_scan"] is True
    assert res_data["front_scan"]["original_filename"] == "front.jpg"
    assert res_data["front_scan"]["content_type"] == "image/jpeg"
    assert res_data["back_scan"]["original_filename"] == "back.jpg"
    assert res_data["back_scan"]["content_type"] == "image/jpeg"
    assert "url" in res_data["front_scan"]
    assert "url" in res_data["back_scan"]


def test_create_front_only_duty_slip(client):
    c, company_id = client
    front_bytes = b"FAKE_FRONT_ONLY_IMAGE_CONTENT"

    files = {
        "front_file": ("front_single.png", io.BytesIO(front_bytes), "image/png"),
    }
    data = {
        "company_id": company_id,
        "duty_slip_no": "2",
        "notes": "Single-sided slip"
    }

    response = c.post("/api/v1/duty-slips", data=data, files=files)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["duty_slip_no"] == "2"
    assert res_data["has_back_scan"] is False
    assert res_data["front_scan"]["original_filename"] == "front_single.png"
    assert res_data["back_scan"] is None

    # Check that back endpoint returns 404
    ds_id = res_data["id"]
    back_res = c.get(f"/api/v1/duty-slips/{ds_id}/back")
    assert back_res.status_code == 404


def test_create_duty_slip_invalid_company(client):
    c, _ = client
    files = {
        "front_file": ("front.jpg", io.BytesIO(b"front"), "image/jpeg"),
    }
    data = {
        "company_id": "6a9d9b8ff5d7e1a340d24699",
        "duty_slip_no": "3"
    }
    response = c.post("/api/v1/duty-slips", data=data, files=files)
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"]


def test_create_duty_slip_empty_number(client):
    c, company_id = client
    files = {
        "front_file": ("front.jpg", io.BytesIO(b"front"), "image/jpeg"),
    }
    data = {
        "company_id": company_id,
        "duty_slip_no": "    "
    }
    response = c.post("/api/v1/duty-slips", data=data, files=files)
    assert response.status_code == 422


def test_create_duty_slip_invalid_file_extension(client):
    c, company_id = client
    # Invalid front file
    files_front = {
        "front_file": ("script.exe", io.BytesIO(b"binary"), "image/jpeg"),
    }
    res_front = c.post("/api/v1/duty-slips", data={"company_id": company_id, "duty_slip_no": "4"}, files=files_front)
    assert res_front.status_code == 422
    assert "Unsupported file extension" in res_front.json()["detail"]


def test_duplicate_duty_slip_rejected(client):
    c, company_id = client
    files1 = {
        "front_file": ("front.jpg", io.BytesIO(b"front"), "image/jpeg"),
    }
    data1 = {"company_id": company_id, "duty_slip_no": "99"}
    res1 = c.post("/api/v1/duty-slips", data=data1, files=files1)
    assert res1.status_code == 201

    # Attempt duplicate for same company
    files2 = {
        "front_file": ("front.jpg", io.BytesIO(b"front2"), "image/jpeg"),
    }
    data2 = {"company_id": company_id, "duty_slip_no": "99"}
    res2 = c.post("/api/v1/duty-slips", data=data2, files=files2)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_list_and_filter_duty_slips(client):
    c, company_id = client
    response = c.get(f"/api/v1/duty-slips?company_id={company_id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    slip_numbers = [d["duty_slip_no"] for d in data]
    assert "1" in slip_numbers
    assert "2" in slip_numbers
    assert "99" in slip_numbers


def test_get_single_duty_slip_and_scans(client):
    c, company_id = client
    files = {
        "front_file": ("test_f.png", io.BytesIO(b"PNG_FRONT_BYTES"), "image/png"),
        "back_file": ("test_b.png", io.BytesIO(b"PNG_BACK_BYTES"), "image/png"),
    }
    data = {"company_id": company_id, "duty_slip_no": "101"}
    create_res = c.post("/api/v1/duty-slips", data=data, files=files)
    assert create_res.status_code == 201
    created_id = create_res.json()["id"]

    # 1. Get metadata
    get_res = c.get(f"/api/v1/duty-slips/{created_id}")
    assert get_res.status_code == 200
    assert get_res.json()["duty_slip_no"] == "101"

    # 2. Get Front Scan
    front_res = c.get(f"/api/v1/duty-slips/{created_id}/front")
    assert front_res.status_code == 200
    assert front_res.content == b"PNG_FRONT_BYTES"
    assert "image/png" in front_res.headers["content-type"]

    # 3. Get Back Scan
    back_res = c.get(f"/api/v1/duty-slips/{created_id}/back")
    assert back_res.status_code == 200
    assert back_res.content == b"PNG_BACK_BYTES"
    assert "image/png" in back_res.headers["content-type"]


def test_update_metadata(client):
    c, company_id = client
    files = {
        "front_file": ("front.jpg", io.BytesIO(b"front"), "image/jpeg"),
    }
    create_res = c.post("/api/v1/duty-slips", data={"company_id": company_id, "duty_slip_no": "102"}, files=files)
    assert create_res.status_code == 201
    ds_id = create_res.json()["id"]

    update_payload = {"notes": "Updated note after verification"}
    update_res = c.put(f"/api/v1/duty-slips/{ds_id}", json=update_payload)
    assert update_res.status_code == 200
    assert update_res.json()["notes"] == "Updated note after verification"


def test_non_existent_duty_slip(client):
    c, _ = client
    response = c.get("/api/v1/duty-slips/6a9d9b8ff5d7e1a340d24600")
    assert response.status_code == 404

    front_res = c.get("/api/v1/duty-slips/6a9d9b8ff5d7e1a340d24600/front")
    assert front_res.status_code == 404


def test_delete_duty_slip(client):
    c, company_id = client
    files = {
        "front_file": ("front.jpg", io.BytesIO(b"front"), "image/jpeg"),
    }
    create_res = c.post("/api/v1/duty-slips", data={"company_id": company_id, "duty_slip_no": "103"}, files=files)
    assert create_res.status_code == 201
    ds_id = create_res.json()["id"]

    # Delete
    del_res = c.delete(f"/api/v1/duty-slips/{ds_id}")
    assert del_res.status_code == 200

    # Verify not found
    get_res = c.get(f"/api/v1/duty-slips/{ds_id}")
    assert get_res.status_code == 404

