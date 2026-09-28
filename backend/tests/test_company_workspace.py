import io
import pytest
from starlette.testclient import TestClient

from app.main import app
from app.core.database import db_manager
from app.core.config import settings


@pytest.fixture
def client():
    original_provider = settings.OCR_PROVIDER
    settings.OCR_PROVIDER = "mock"
    with TestClient(app) as c:
        db = db_manager.get_database()
        db["companies"].delete_many({"name": {"$regex": "^TEST_WORKSPACE_"}})
        db["duty_slips"].delete_many({"duty_slip_no": {"$in": ["80", "81"]}})
        yield c
    settings.OCR_PROVIDER = original_provider


def test_company_workspace_info_empty_master_doc(client):
    """
    Verify that a new company has has_master_doc=False and empty bills list.
    """
    comp_res = client.post("/api/v1/companies", json={"name": "TEST_WORKSPACE_Alpha"})
    assert comp_res.status_code == 201
    comp_id = comp_res.json()["id"]

    info_res = client.get(f"/api/v1/companies/{comp_id}/document/info")
    assert info_res.status_code == 200
    info_data = info_res.json()
    assert info_data["company_id"] == comp_id
    assert info_data["has_master_doc"] is False
    assert info_data["total_bills"] == 0
    assert info_data["bills"] == []
    assert info_data["docx_url"] is None
    assert info_data["pdf_url"] is None


def test_company_workspace_isolated_bills_and_slips(client):
    """
    Verify that Company A and Company B have completely isolated bills and duty slips.
    """
    # Create Company A & B
    comp_a = client.post("/api/v1/companies", json={"name": "TEST_WORKSPACE_Corp_A"}).json()
    comp_b = client.post("/api/v1/companies", json={"name": "TEST_WORKSPACE_Corp_B"}).json()

    # Create Duty Slip 80 for Company A
    ds_a = client.post(
        "/api/v1/duty-slips",
        data={"company_id": comp_a["id"], "duty_slip_no": "80"},
        files={"front_file": ("front_a.jpg", io.BytesIO(b"FRONT_A"), "image/jpeg")}
    ).json()

    # Create Duty Slip 81 for Company B
    ds_b = client.post(
        "/api/v1/duty-slips",
        data={"company_id": comp_b["id"], "duty_slip_no": "81"},
        files={"front_file": ("front_b.jpg", io.BytesIO(b"FRONT_B"), "image/jpeg")}
    ).json()

    # Extract, Review, Verify, and Generate Bill for Company A
    client.post(f"/api/v1/duty-slips/{ds_a['id']}/extract")
    client.put(f"/api/v1/duty-slips/{ds_a['id']}/extraction", json={
        "fields": {
            "duty_slip_no": "80",
            "vehicle_number": "KA01AB1234",
            "customer_name": "Alpha Customer",
            "total_amount": "5000",
            "date": "01-09-2026"
        },
        "reviewer": "RevA"
    })
    client.post(f"/api/v1/duty-slips/{ds_a['id']}/verify")
    client.post(f"/api/v1/duty-slips/{ds_a['id']}/generate-word", json={"bill_no": "Bill 01"})

    # Check Company A Workspace Info
    info_a = client.get(f"/api/v1/companies/{comp_a['id']}/document/info").json()
    assert info_a["has_master_doc"] is True
    assert info_a["total_bills"] == 1
    assert len(info_a["bills"]) == 1
    assert info_a["bills"][0]["bill_no"] == "Bill 01"
    assert info_a["bills"][0]["duty_slip_no"] == "80"
    assert info_a["bills"][0]["customer_name"] == "Alpha Customer"
    assert info_a["bills"][0]["total_amount"] == 5000.0

    # Check Company B Workspace Info -> Must be completely empty/unaffected!
    info_b = client.get(f"/api/v1/companies/{comp_b['id']}/document/info").json()
    assert info_b["has_master_doc"] is False
    assert info_b["total_bills"] == 0
    assert len(info_b["bills"]) == 0

    # Check Duty Slips filtering for Company A vs B
    slips_a = client.get(f"/api/v1/duty-slips?company_id={comp_a['id']}").json()
    assert len(slips_a) == 1
    assert slips_a[0]["duty_slip_no"] == "80"

    slips_b = client.get(f"/api/v1/duty-slips?company_id={comp_b['id']}").json()
    assert len(slips_b) == 1
    assert slips_b[0]["duty_slip_no"] == "81"
