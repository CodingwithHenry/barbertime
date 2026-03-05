"""Tests for /api/v1/employees/* endpoints."""
import io
import pytest
from unittest.mock import patch

import app.core.upload as _upload


async def _create_employee(client, headers, name="Alice", role="Barber"):
    resp = await client.post("/api/v1/employees/", headers=headers, json={"name": name, "role": role})
    assert resp.status_code == 201
    return resp.json()


# ── CRUD ──────────────────────────────────────────────────────────────────────

async def test_list_employees_empty(client, auth_headers):
    resp = await client.get("/api/v1/employees/", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_create_employee(client, auth_headers):
    emp = await _create_employee(client, auth_headers, name="Alice", role="Senior Barber")
    assert emp["name"] == "Alice"
    assert emp["role"] == "Senior Barber"
    assert emp["wait_time"] == 0
    assert emp["is_active"] is True


async def test_list_employees_after_create(client, auth_headers):
    await _create_employee(client, auth_headers, "Alice")
    await _create_employee(client, auth_headers, "Bob")
    resp = await client.get("/api/v1/employees/", headers=auth_headers)
    assert len(resp.json()) == 2


async def test_update_employee_name(client, auth_headers):
    emp = await _create_employee(client, auth_headers)
    resp = await client.patch(f"/api/v1/employees/{emp['id']}", headers=auth_headers, json={"name": "Alicia"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Alicia"


async def test_update_employee_wait_time(client, auth_headers):
    emp = await _create_employee(client, auth_headers)
    resp = await client.patch(f"/api/v1/employees/{emp['id']}", headers=auth_headers, json={"wait_time": 30})
    assert resp.status_code == 200
    assert resp.json()["wait_time"] == 30


async def test_toggle_away(client, auth_headers):
    emp = await _create_employee(client, auth_headers)
    resp = await client.patch(f"/api/v1/employees/{emp['id']}", headers=auth_headers, json={"is_active": False})
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


async def test_delete_employee(client, auth_headers):
    emp = await _create_employee(client, auth_headers)
    resp = await client.delete(f"/api/v1/employees/{emp['id']}", headers=auth_headers)
    assert resp.status_code == 204

    list_resp = await client.get("/api/v1/employees/", headers=auth_headers)
    assert list_resp.json() == []


async def test_update_other_shop_employee_forbidden(client, register):
    token_a = await register(email="shop_a@example.com")
    token_b = await register(email="shop_b@example.com")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    emp = await _create_employee(client, headers_a)

    resp = await client.patch(f"/api/v1/employees/{emp['id']}", headers=headers_b, json={"name": "Hacked"})
    assert resp.status_code == 404


# ── photo upload ──────────────────────────────────────────────────────────────

async def test_upload_employee_photo(client, auth_headers):
    emp = await _create_employee(client, auth_headers)
    with patch.object(_upload, "validate_image_bytes"):
        resp = await client.post(
            f"/api/v1/employees/{emp['id']}/photo",
            headers=auth_headers,
            files={"file": ("photo.png", io.BytesIO(b"\x89PNG\r\n"), "image/png")},
        )
    assert resp.status_code == 200
    assert resp.json()["photo_url"].startswith("/uploads/")


# ── wait time suggestion ──────────────────────────────────────────────────────

async def test_suggest_employee_wait_time(client, auth_headers):
    emp = await _create_employee(client, auth_headers)
    resp = await client.get(f"/api/v1/employees/{emp['id']}/suggest-wait-time", headers=auth_headers)
    assert resp.status_code == 200
    assert "suggested_wait_time" in resp.json()
