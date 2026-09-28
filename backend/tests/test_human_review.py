import io
import pytest
from starlette.testclient import TestClient
from app.main import app
from app.core.database import db_manager
from app.core.config import settings


@pytest.fixture(scope="module")
def client():
    original_provider = settings.OCR_PROVIDER
    settings.OCR_PROVIDER = "mock"
    with TestClient(app) as c:
        db = db_manager.get_database()
        # Clean up test records
        test_slips = list(db["duty_slips"].find({"duty_slip_no": {"$in": ["50", "51", "52", "53", "54", "55"]}}))
        test_slip_ids = [s["_id"] for s in test_slips]
        db["extractions"].delete_many({"duty_slip_id": {"$in": test_slip_ids}})
        db["duty_slips"].delete_many({"duty_slip_no": {"$in": ["50", "51", "52", "53", "54", "55"]}})
        db["companies"].delete_many({"name": {"$regex": "^TEST_REVIEW_"}})

        # Create test company
        res_comp = c.post("/api/v1/companies", json={"name": "TEST_REVIEW_Company"})
        assert res_comp.status_code == 201
        company_id = res_comp.json()["id"]

        # Create test dual-side duty slip #50
        files_dual = {
            "front_file": ("front.jpg", io.BytesIO(b"FRONT_IMAGE_BYTES"), "image/jpeg"),
            "back_file": ("back.jpg", io.BytesIO(b"BACK_IMAGE_BYTES"), "image/jpeg"),
        }
        res_ds50 = c.post("/api/v1/duty-slips", data={"company_id": company_id, "duty_slip_no": "50"}, files=files_dual)
        assert res_ds50.status_code == 201
        duty_slip_50_id = res_ds50.json()["id"]

        # Create test front-only duty slip #51
        files_front = {
            "front_file": ("front.jpg", io.BytesIO(b"FRONT_ONLY_IMAGE"), "image/jpeg"),
        }
        res_ds51 = c.post("/api/v1/duty-slips", data={"company_id": company_id, "duty_slip_no": "51"}, files=files_front)
        assert res_ds51.status_code == 201
        duty_slip_51_id = res_ds51.json()["id"]

        yield c, company_id, duty_slip_50_id, duty_slip_51_id

        # Teardown
        db["companies"].delete_many({"name": {"$regex": "^TEST_REVIEW_"}})
        test_slips = list(db["duty_slips"].find({"duty_slip_no": {"$in": ["50", "51", "52", "53", "54", "55"]}}))
        test_slip_ids = [s["_id"] for s in test_slips]
        db["duty_slips"].delete_many({"duty_slip_no": {"$in": ["50", "51", "52", "53", "54", "55"]}})
        db["extractions"].delete_many({"duty_slip_id": {"$in": test_slip_ids}})
        settings.OCR_PROVIDER = original_provider


def test_case_1_no_edits_then_verify(client):
    c, _, duty_slip_id, _ = client
    # 1. Run extraction
    extract_res = c.post(f"/api/v1/duty-slips/{duty_slip_id}/extract")
    assert extract_res.status_code == 200

    # 2. Directly verify without modifying fields
    verify_res = c.post(
        f"/api/v1/duty-slips/{duty_slip_id}/verify",
        json={"reviewer": "test_reviewer_1", "notes": "Looks good"}
    )
    assert verify_res.status_code == 200
    data = verify_res.json()

    assert data["status"] == "verified"
    assert data["verified_by"] == "test_reviewer_1"
    assert data["verified_at"] is not None
    # Confirm original OCR values remain intact
    assert data["fields"]["vehicle_number"]["value"] == "TS09GC6246 A/c Sedan"
    assert data["fields"]["vehicle_number"]["edited"] is False
    assert len(data["audit_log"]) == 0

    # Check duty slip record status
    ds_res = c.get(f"/api/v1/duty-slips/{duty_slip_id}")
    assert ds_res.json()["status"] == "verified"


def test_case_2_edit_one_field_preserves_original_ocr(client):
    c, company_id, _, _ = client
    # Create fresh duty slip #52
    files = {
        "front_file": ("front.jpg", io.BytesIO(b"FRONT_IMAGE_52"), "image/jpeg"),
        "back_file": ("back.jpg", io.BytesIO(b"BACK_IMAGE_52"), "image/jpeg"),
    }
    ds_res = c.post("/api/v1/duty-slips", data={"company_id": company_id, "duty_slip_no": "52"}, files=files)
    ds_id = ds_res.json()["id"]

    # Extract
    c.post(f"/api/v1/duty-slips/{ds_id}/extract")

    # Update 1 field: vehicle_number
    update_res = c.put(
        f"/api/v1/duty-slips/{ds_id}/extraction",
        json={
            "fields": {
                "vehicle_number": "TS09GC6246 A/c Sedan (Corrected)"
            },
            "reviewer": "reviewer_alice",
            "notes": "Fixed vehicle description"
        }
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()

    # Original value preserved
    assert updated_data["fields"]["vehicle_number"]["original_value"] == "TS09GC6246 A/c Sedan"
    # Corrected value active
    assert updated_data["fields"]["vehicle_number"]["value"] == "TS09GC6246 A/c Sedan (Corrected)"
    assert updated_data["fields"]["vehicle_number"]["edited"] is True
    assert updated_data["fields"]["vehicle_number"]["edited_by"] == "reviewer_alice"
    assert updated_data["fields"]["vehicle_number"]["edited_at"] is not None

    # Audit log recorded
    assert len(updated_data["audit_log"]) == 1
    audit = updated_data["audit_log"][0]
    assert audit["field_name"] == "vehicle_number"
    assert audit["original_value"] == "TS09GC6246 A/c Sedan"
    assert audit["corrected_value"] == "TS09GC6246 A/c Sedan (Corrected)"
    assert audit["edited_by"] == "reviewer_alice"


def test_case_3_edit_multiple_fields_independently(client):
    c, company_id, _, _ = client
    # Create fresh duty slip #53
    files = {
        "front_file": ("front.jpg", io.BytesIO(b"FRONT_IMAGE_53"), "image/jpeg"),
        "back_file": ("back.jpg", io.BytesIO(b"BACK_IMAGE_53"), "image/jpeg"),
    }
    ds_res = c.post("/api/v1/duty-slips", data={"company_id": company_id, "duty_slip_no": "53"}, files=files)
    ds_id = ds_res.json()["id"]

    c.post(f"/api/v1/duty-slips/{ds_id}/extract")

    # Edit multiple fields: driver_name, duty_slip_no (physical number), and remarks
    update_res = c.put(
        f"/api/v1/duty-slips/{ds_id}/extraction",
        json={
            "fields": {
                "driver_name": "K. Mohan Krishna (Senior)",
                "duty_slip_no": "PHYSICAL-47",
                "remarks": "Reviewed and approved"
            },
            "reviewer": "reviewer_bob"
        }
    )
    assert update_res.status_code == 200
    data = update_res.json()

    assert data["fields"]["driver_name"]["value"] == "K. Mohan Krishna (Senior)"
    assert data["fields"]["driver_name"]["edited"] is True
    assert data["fields"]["duty_slip_no"]["value"] == "PHYSICAL-47"
    assert data["fields"]["duty_slip_no"]["edited"] is True
    assert data["fields"]["remarks"]["value"] == "Reviewed and approved"
    assert data["fields"]["remarks"]["edited"] is True

    # Other fields intact
    assert data["fields"]["total_km"]["edited"] is False

    # Check audit log length
    assert len(data["audit_log"]) == 3


def test_case_4_unresolved_required_field_blocks_verification(client):
    c, company_id, _, _ = client
    # Create fresh duty slip #54
    files = {
        "front_file": ("front.jpg", io.BytesIO(b"FRONT_IMAGE_54"), "image/jpeg"),
        "back_file": ("back.jpg", io.BytesIO(b"BACK_IMAGE_54"), "image/jpeg"),
    }
    ds_res = c.post("/api/v1/duty-slips", data={"company_id": company_id, "duty_slip_no": "54"}, files=files)
    ds_id = ds_res.json()["id"]

    c.post(f"/api/v1/duty-slips/{ds_id}/extract")

    # Set required field (driver_name) to None
    c.put(
        f"/api/v1/duty-slips/{ds_id}/extraction",
        json={
            "fields": {
                "driver_name": None
            },
            "reviewer": "reviewer_charlie"
        }
    )

    # Attempt to verify -> should fail with 422
    verify_res = c.post(f"/api/v1/duty-slips/{ds_id}/verify")
    assert verify_res.status_code == 422
    assert "Required fields missing" in verify_res.json()["detail"]


def test_case_5_validation_conflict_blocks_verification(client):
    c, company_id, _, _ = client
    # Create fresh duty slip #55
    files = {
        "front_file": ("front.jpg", io.BytesIO(b"FRONT_IMAGE_55"), "image/jpeg"),
        "back_file": ("back.jpg", io.BytesIO(b"BACK_IMAGE_55"), "image/jpeg"),
    }
    ds_res = c.post("/api/v1/duty-slips", data={"company_id": company_id, "duty_slip_no": "55"}, files=files)
    ds_id = ds_res.json()["id"]

    c.post(f"/api/v1/duty-slips/{ds_id}/extract")

    # Introduce conflict: meter_return 432582 - meter_start 432435 = 147 KM, but set total_km to 500
    c.put(
        f"/api/v1/duty-slips/{ds_id}/extraction",
        json={
            "fields": {
                "total_km": 500
            },
            "reviewer": "reviewer_dan"
        }
    )

    # Re-fetch extraction and verify consistency flag is False
    ext_res = c.get(f"/api/v1/duty-slips/{ds_id}/extraction")
    assert ext_res.json()["validation_summary"]["is_km_consistent"] is False

    # Attempt to verify -> should fail with 422
    verify_res = c.post(f"/api/v1/duty-slips/{ds_id}/verify")
    assert verify_res.status_code == 422
    assert "consistency conflict" in verify_res.json()["detail"]


    # Now fix the conflict: set total_km back to 147
    c.put(
        f"/api/v1/duty-slips/{ds_id}/extraction",
        json={
            "fields": {
                "total_km": 147
            },
            "reviewer": "reviewer_dan"
        }
    )

    # Verify now succeeds
    verify_res2 = c.post(f"/api/v1/duty-slips/{ds_id}/verify")
    assert verify_res2.status_code == 200
    assert verify_res2.json()["status"] == "verified"


def test_case_6_front_only_review_and_verification(client):
    c, _, _, front_only_ds_id = client
    # Extract front-only
    extract_res = c.post(f"/api/v1/duty-slips/{front_only_ds_id}/extract")
    assert extract_res.status_code == 200

    # Human review: add physical document number
    update_res = c.put(
        f"/api/v1/duty-slips/{front_only_ds_id}/extraction",
        json={
            "fields": {
                "duty_slip_no": "FO-101"
            },
            "reviewer": "reviewer_eva"
        }
    )
    assert update_res.status_code == 200
    assert update_res.json()["fields"]["duty_slip_no"]["value"] == "FO-101"

    # Verify
    verify_res = c.post(f"/api/v1/duty-slips/{front_only_ds_id}/verify")
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "verified"
