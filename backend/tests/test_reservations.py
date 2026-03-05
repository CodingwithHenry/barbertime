"""Tests for /api/v1/reservations/* endpoints."""
import pytest
from sqlalchemy import select

from app.models.shop import ShopStatus
from tests.conftest import _TestSession


async def _open_shop(client, auth_headers):
    """Set the shop to open so reservations are accepted."""
    await client.patch("/api/v1/shops/me/status", headers=auth_headers, json={
        "status": "open",
        "wait_time": 15,
    })
    # Get the shop id
    resp = await client.get("/api/v1/shops/me", headers=auth_headers)
    return resp.json()["id"]


# ── create reservation ────────────────────────────────────────────────────────

async def test_create_reservation(client, auth_headers):
    shop_id = await _open_shop(client, auth_headers)
    resp = await client.post(f"/api/v1/reservations/{shop_id}", json={"phone_number": "+49123456789"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "active"
    assert data["shop_id"] == shop_id
    assert "expires_at" in data


async def test_reservation_normalizes_phone(client, auth_headers):
    shop_id = await _open_shop(client, auth_headers)
    resp = await client.post(f"/api/v1/reservations/{shop_id}", json={"phone_number": "+49 123 456 789"})
    assert resp.status_code == 201


async def test_reservation_invalid_phone(client, auth_headers):
    shop_id = await _open_shop(client, auth_headers)
    resp = await client.post(f"/api/v1/reservations/{shop_id}", json={"phone_number": "abc"})
    assert resp.status_code == 422


async def test_reservation_closed_shop(client, auth_headers):
    """Cannot reserve when shop is closed."""
    resp = await client.get("/api/v1/shops/me", headers=auth_headers)
    shop_id = resp.json()["id"]
    # Shop defaults to closed on creation
    resp = await client.post(f"/api/v1/reservations/{shop_id}", json={"phone_number": "+49123456789"})
    assert resp.status_code == 400


async def test_reservation_nonexistent_shop(client):
    resp = await client.post("/api/v1/reservations/999999", json={"phone_number": "+49123456789"})
    assert resp.status_code == 404


async def test_reservation_rate_limit_one_per_day(client, auth_headers):
    shop_id = await _open_shop(client, auth_headers)
    phone = "+49111222333"
    await client.post(f"/api/v1/reservations/{shop_id}", json={"phone_number": phone})
    resp = await client.post(f"/api/v1/reservations/{shop_id}", json={"phone_number": phone})
    assert resp.status_code == 429


async def test_reservation_with_preferred_employee(client, auth_headers):
    shop_id = await _open_shop(client, auth_headers)
    emp_resp = await client.post("/api/v1/employees/", headers=auth_headers, json={"name": "Alice"})
    emp_id = emp_resp.json()["id"]
    resp = await client.post(f"/api/v1/reservations/{shop_id}", json={
        "phone_number": "+49123456789",
        "employee_id": emp_id,
    })
    assert resp.status_code == 201
    assert resp.json()["employee_id"] == emp_id


# ── list / manage reservations (barber dashboard) ─────────────────────────────

async def test_list_reservations_authenticated(client, auth_headers):
    shop_id = await _open_shop(client, auth_headers)
    await client.post(f"/api/v1/reservations/{shop_id}", json={"phone_number": "+49123456789"})
    resp = await client.get("/api/v1/reservations/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_list_reservations_unauthenticated(client):
    resp = await client.get("/api/v1/reservations/")
    assert resp.status_code == 403


async def test_update_reservation_status_done(client, auth_headers):
    shop_id = await _open_shop(client, auth_headers)
    await client.post(f"/api/v1/reservations/{shop_id}", json={"phone_number": "+49123456789"})
    res_list = (await client.get("/api/v1/reservations/", headers=auth_headers)).json()
    res_id = res_list[0]["id"]

    resp = await client.patch(
        f"/api/v1/reservations/{res_id}/status",
        headers=auth_headers,
        params={"new_status": "done"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


async def test_update_reservation_status_no_show(client, auth_headers):
    shop_id = await _open_shop(client, auth_headers)
    await client.post(f"/api/v1/reservations/{shop_id}", json={"phone_number": "+49777888999"})
    res_list = (await client.get("/api/v1/reservations/", headers=auth_headers)).json()
    res_id = res_list[0]["id"]

    resp = await client.patch(
        f"/api/v1/reservations/{res_id}/status",
        headers=auth_headers,
        params={"new_status": "no_show"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "no_show"


async def test_done_reservation_not_in_active_list(client, auth_headers):
    shop_id = await _open_shop(client, auth_headers)
    await client.post(f"/api/v1/reservations/{shop_id}", json={"phone_number": "+49123456789"})
    res_id = (await client.get("/api/v1/reservations/", headers=auth_headers)).json()[0]["id"]

    await client.patch(
        f"/api/v1/reservations/{res_id}/status",
        headers=auth_headers,
        params={"new_status": "done"},
    )
    active = (await client.get("/api/v1/reservations/", headers=auth_headers)).json()
    assert all(r["id"] != res_id for r in active)
