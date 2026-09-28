import io
import pytest
from starlette.testclient import TestClient
from app.main import app
from app.core.database import db_manager
from app.services.ocr.mock_provider import MockOCRProvider
from app.services.ocr.service import ExtractionService
from app.services.storage.local import LocalStorageService


from app.core.config import settings


@pytest.fixture(scope="module")
def client():
    original_provider = settings.OCR_PROVIDER
    settings.OCR_PROVIDER = "mock"
    with TestClient(app) as c:
        db = db_manager.get_database()
        # Clean up test records
        test_slips = list(db["duty_slips"].find({"duty_slip_no": {"$in": ["10", "11", "12", "13", "14", "15", "16"]}}))
        test_slip_ids = [s["_id"] for s in test_slips]
        db["extractions"].delete_many({"duty_slip_id": {"$in": test_slip_ids}})
        db["duty_slips"].delete_many({"duty_slip_no": {"$in": ["10", "11", "12", "13", "14", "15", "16"]}})
        db["companies"].delete_many({"name": {"$regex": "^TEST_"}})

        # Create test company
        res_comp = c.post("/api/v1/companies", json={"name": "TEST_OCR_Company"})
        assert res_comp.status_code == 201
        company_id = res_comp.json()["id"]

        # Create test duty slip #10 (Front + Back)
        files = {
            "front_file": ("front.jpg", io.BytesIO(b"FRONT_IMAGE_BYTES"), "image/jpeg"),
            "back_file": ("back.jpg", io.BytesIO(b"BACK_IMAGE_BYTES"), "image/jpeg"),
        }
        res_ds = c.post("/api/v1/duty-slips", data={"company_id": company_id, "duty_slip_no": "10"}, files=files)
        assert res_ds.status_code == 201
        duty_slip_id = res_ds.json()["id"]

        yield c, company_id, duty_slip_id

        # Post-test cleanup
        test_slips = list(db["duty_slips"].find({"duty_slip_no": {"$in": ["10", "11", "12", "13", "14", "15", "16"]}}))
        test_slip_ids = [s["_id"] for s in test_slips]
        db["extractions"].delete_many({"duty_slip_id": {"$in": test_slip_ids}})
        db["duty_slips"].delete_many({"duty_slip_no": {"$in": ["10", "11", "12", "13", "14", "15", "16"]}})
        db["companies"].delete_many({"name": {"$regex": "^TEST_"}})
        settings.OCR_PROVIDER = original_provider


def test_extract_valid_duty_slip_with_real_fields(client):
    c, _, duty_slip_id = client
    response = c.post(f"/api/v1/duty-slips/{duty_slip_id}/extract")
    assert response.status_code == 200
    data = response.json()

    assert data["duty_slip_id"] == duty_slip_id
    assert data["stored_duty_slip_no"] == "10"
    assert data["fields"]["duty_slip_no"]["value"] is None
    assert data["fields"]["duty_slip_no"]["needs_review"] is True
    assert data["fields"]["duty_slip_no"]["review_reason"] == "unreadable_field"
    assert "fields" in data
    # Ground truth document values
    assert data["fields"]["vehicle_number"]["value"] == "TS09GC6246 A/c Sedan"
    assert data["fields"]["driver_name"]["value"] == "K. Mohan Krishna"
    assert data["fields"]["meter_start"]["value"] == 432435
    assert data["fields"]["meter_return"]["value"] == 432582
    assert data["fields"]["total_km"]["value"] == 147
    assert data["fields"]["starting_time"]["value"] == "08:00 AM"
    assert data["fields"]["closing_time"]["value"] == "05:30 PM"
    assert data["fields"]["reporting_place"]["value"] == "Office"
    assert data["fields"]["tour_location"]["value"] == "To Local"
    assert data["fields"]["party_name"]["value"] == "Mr Uday Kumar"
    assert data["fields"]["extra_km"]["value"] == 67
    assert data["fields"]["extra_hours"]["value"] == 1.5
    # Back side handwritten calculations
    assert data["fields"]["base_package"]["value"] == "8/80 = 2500"
    assert data["fields"]["extra_km_charge"]["value"] == "67 x 15 = 1005"
    assert data["fields"]["extra_hour_charge"]["value"] == "1.5 x 150 = 225"
    assert data["fields"]["bata"]["value"] == 250
    assert data["fields"]["toll"]["value"] == 40
    assert data["fields"]["total_amount"]["value"] == 4020
    assert data["fields"]["base_package"]["source_side"] == "back"
    # Calculated validation consistency summary (8hr / 80km package)
    assert data["validation_summary"]["calculated_total_hours"] == 9.5
    assert data["validation_summary"]["calculated_extra_hours"] == 1.5
    assert data["validation_summary"]["calculated_total_km"] == 147
    assert data["validation_summary"]["calculated_extra_km"] == 67
    assert data["validation_summary"]["calculated_extra_km_amount"] == 1005
    assert data["validation_summary"]["calculated_extra_hour_amount"] == 225
    assert data["validation_summary"]["calculated_total_amount"] == 4020
    assert data["validation_summary"]["is_km_consistent"] is True
    assert data["validation_summary"]["is_time_consistent"] is True
    assert data["validation_summary"]["is_math_consistent"] is True

    # Verify Duty Slip status updated
    ds_res = c.get(f"/api/v1/duty-slips/{duty_slip_id}")
    assert ds_res.json()["status"] in ("extracted", "needs_review")


def test_extract_front_only_duty_slip(client):
    c, company_id, _ = client
    # Create Front-Only duty slip #15
    files = {
        "front_file": ("front_only.jpg", io.BytesIO(b"FRONT_IMAGE_BYTES"), "image/jpeg"),
    }
    res_ds = c.post("/api/v1/duty-slips", data={"company_id": company_id, "duty_slip_no": "15"}, files=files)
    assert res_ds.status_code == 201
    ds_id = res_ds.json()["id"]

    # Extract
    res_extract = c.post(f"/api/v1/duty-slips/{ds_id}/extract")
    assert res_extract.status_code == 200
    data = res_extract.json()
    assert data["duty_slip_id"] == ds_id
    assert data["fields"]["vehicle_number"]["value"] == "TS09GC6246 A/c Sedan"
    assert data["fields"]["reporting_place"]["value"] == "Office"


def test_get_extraction_result(client):
    c, _, duty_slip_id = client
    response = c.get(f"/api/v1/duty-slips/{duty_slip_id}/extraction")
    assert response.status_code == 200
    data = response.json()
    assert data["duty_slip_id"] == duty_slip_id
    assert data["fields"]["date"]["value"] == "02-09-2026"


def test_extract_nonexistent_duty_slip(client):
    c, _, _ = client
    response = c.post("/api/v1/duty-slips/6a9d9b8ff5d7e1a340d24699/extract")
    assert response.status_code == 404


def test_get_extraction_nonexistent_duty_slip(client):
    c, _, _ = client
    response = c.get("/api/v1/duty-slips/6a9d9b8ff5d7e1a340d24699/extraction")
    assert response.status_code == 404


def test_ocr_duty_slip_number_mismatch(client):
    c, company_id, _ = client
    files = {
        "front_file": ("front.jpg", io.BytesIO(b"FRONT_IMAGE_BYTES"), "image/jpeg"),
    }
    res_ds = c.post("/api/v1/duty-slips", data={"company_id": company_id, "duty_slip_no": "12"}, files=files)
    assert res_ds.status_code == 201
    ds_id = res_ds.json()["id"]

    # Mock OCR detects duty slip # "17" (mismatch)
    custom_mock_fields = {
        "duty_slip_no": {"value": "17", "confidence": 0.90, "needs_review": False},
        "vehicle_number": {"value": "TS09GC6243 A/C Sedan", "confidence": 0.95, "needs_review": False},
        "date": {"value": "02-09-2026", "confidence": 0.95, "needs_review": False}
    }
    db = db_manager.get_database()
    custom_service = ExtractionService(db, LocalStorageService(), MockOCRProvider(custom_mock_fields))
    result = custom_service.extract_duty_slip(ds_id)

    assert result.needs_review is True
    assert "duty_slip_number_mismatch" in result.review_reasons
    assert result.fields.duty_slip_no.needs_review is True


def test_ocr_low_confidence_and_unreadable_fields(client):
    c, company_id, _ = client
    files = {
        "front_file": ("front.jpg", io.BytesIO(b"FRONT_IMAGE_BYTES"), "image/jpeg"),
    }
    res_ds = c.post("/api/v1/duty-slips", data={"company_id": company_id, "duty_slip_no": "13"}, files=files)
    assert res_ds.status_code == 201
    ds_id = res_ds.json()["id"]

    # Mock OCR with low confidence and unreadable fields (never guessing values!)
    custom_mock_fields = {
        "duty_slip_no": {"value": "13", "confidence": 0.95, "needs_review": False},
        "vehicle_number": {"value": None, "confidence": 0.35, "needs_review": True, "review_reason": "unreadable_field"},
        "driver_name": {"value": "Ramesh", "confidence": 0.65, "needs_review": True, "review_reason": "low_confidence"}
    }
    db = db_manager.get_database()
    custom_service = ExtractionService(db, LocalStorageService(), MockOCRProvider(custom_mock_fields))
    result = custom_service.extract_duty_slip(ds_id)

    assert result.needs_review is True
    assert result.fields.vehicle_number.value is None
    assert result.fields.vehicle_number.needs_review is True
    assert result.fields.driver_name.needs_review is True
    assert "unreadable_field" in result.review_reasons
    assert "low_confidence" in result.review_reasons


def test_ocr_km_meter_validation_failure(client):
    c, company_id, _ = client
    files = {
        "front_file": ("front.jpg", io.BytesIO(b"FRONT_IMAGE_BYTES"), "image/jpeg"),
    }
    res_ds = c.post("/api/v1/duty-slips", data={"company_id": company_id, "duty_slip_no": "14"}, files=files)
    assert res_ds.status_code == 201
    ds_id = res_ds.json()["id"]

    # Meter return is less than meter start
    custom_mock_fields = {
        "duty_slip_no": {"value": "14", "confidence": 0.95, "needs_review": False},
        "meter_start": {"value": 432582, "confidence": 0.95, "needs_review": False},
        "meter_return": {"value": 432435, "confidence": 0.95, "needs_review": False},
        "total_km": {"value": 147, "confidence": 0.95, "needs_review": False}
    }
    db = db_manager.get_database()
    custom_service = ExtractionService(db, LocalStorageService(), MockOCRProvider(custom_mock_fields))
    result = custom_service.extract_duty_slip(ds_id)

    assert result.needs_review is True
    assert "validation_failure" in result.review_reasons
    assert result.fields.meter_return.needs_review is True


def test_ocr_back_calculation_math_failure(client):
    c, company_id, _ = client
    files = {
        "front_file": ("front.jpg", io.BytesIO(b"FRONT_IMAGE_BYTES"), "image/jpeg"),
        "back_file": ("back.jpg", io.BytesIO(b"BACK_IMAGE_BYTES"), "image/jpeg"),
    }
    res_ds = c.post("/api/v1/duty-slips", data={"company_id": company_id, "duty_slip_no": "11"}, files=files)
    assert res_ds.status_code == 201
    ds_id = res_ds.json()["id"]

    # 2500 + 1005 + 225 + 250 + 40 = 4020, but total is written as 5000 (math mismatch)
    custom_mock_fields = {
        "duty_slip_no": {"value": "11", "confidence": 0.95, "needs_review": False},
        "base_package": {"value": "8/80 = 2500", "confidence": 0.95, "needs_review": False},
        "extra_km_charge": {"value": "67 x 15 = 1005", "confidence": 0.95, "needs_review": False},
        "extra_hour_charge": {"value": "1.5 x 150 = 225", "confidence": 0.95, "needs_review": False},
        "bata": {"value": 250, "confidence": 0.95, "needs_review": False},
        "toll": {"value": 40, "confidence": 0.95, "needs_review": False},
        "total_amount": {"value": 5000, "confidence": 0.95, "needs_review": False}
    }
    db = db_manager.get_database()
    custom_service = ExtractionService(db, LocalStorageService(), MockOCRProvider(custom_mock_fields))
    result = custom_service.extract_duty_slip(ds_id)

    assert result.needs_review is True
    assert "validation_failure" in result.review_reasons
    assert result.fields.total_amount.needs_review is True


def test_ocr_extra_hours_and_km_conflict(client):
    c, company_id, _ = client
    # Create Duty Slip #16
    files = {
        "front_file": ("front.jpg", io.BytesIO(b"FRONT_IMAGE_BYTES"), "image/jpeg"),
    }
    res_ds = c.post("/api/v1/duty-slips", data={"company_id": company_id, "duty_slip_no": "16"}, files=files)
    assert res_ds.status_code == 201
    ds_id = res_ds.json()["id"]

    # Starting 08:00 AM, Closing 05:30 PM (9.5 hrs, extra = 1.5), but document extracted extra_hours is 3.5
    # Total KM = 147 (extra = 67), but document extracted extra_km is 90
    custom_mock_fields = {
        "duty_slip_no": {"value": "16", "confidence": 0.95, "needs_review": False},
        "starting_time": {"value": "08:00 AM", "confidence": 0.95, "needs_review": False},
        "closing_time": {"value": "05:30 PM", "confidence": 0.95, "needs_review": False},
        "total_km": {"value": 147, "confidence": 0.95, "needs_review": False},
        "extra_hours": {"value": 3.5, "confidence": 0.95, "needs_review": False},  # Mismatch with 1.5
        "extra_km": {"value": 90, "confidence": 0.95, "needs_review": False},      # Mismatch with 67
    }
    db = db_manager.get_database()
    custom_service = ExtractionService(db, LocalStorageService(), MockOCRProvider(custom_mock_fields))
    result = custom_service.extract_duty_slip(ds_id)

    assert result.needs_review is True
    assert "validation_failure" in result.review_reasons
    # Preserve document written value (do not overwrite!)
    assert result.fields.extra_hours.value == 3.5
    assert result.fields.extra_hours.needs_review is True
    assert result.fields.extra_km.value == 90
    assert result.fields.extra_km.needs_review is True
    assert result.validation_summary.is_time_consistent is False
    assert result.validation_summary.is_km_consistent is False
    assert result.validation_summary.calculated_extra_hours == 1.5
    assert result.validation_summary.calculated_extra_km == 67.0


