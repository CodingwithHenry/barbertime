"""Tests for /api/v1/discounts/* endpoints."""
import pytest


async def _create_discount(client, headers, title="10% Off", **kwargs):
    body = {"title": title, **kwargs}
    resp = await client.post("/api/v1/discounts/", headers=headers, json=body)
    assert resp.status_code == 201
    return resp.json()


# ── CRUD ──────────────────────────────────────────────────────────────────────

async def test_list_discounts_empty(client, auth_headers):
    resp = await client.get("/api/v1/discounts/", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_create_discount(client, auth_headers):
    d = await _create_discount(client, auth_headers, title="Free Beard Trim")
    assert d["title"] == "Free Beard Trim"
    assert d["is_active"] is True
    assert d["uses_count"] == 0


async def test_create_discount_with_max_uses(client, auth_headers):
    d = await _create_discount(client, auth_headers, max_uses=5)
    assert d["max_uses"] == 5


async def test_list_discounts(client, auth_headers):
    await _create_discount(client, auth_headers, "Deal 1")
    await _create_discount(client, auth_headers, "Deal 2")
    resp = await client.get("/api/v1/discounts/", headers=auth_headers)
    assert len(resp.json()) == 2


async def test_update_discount_pause(client, auth_headers):
    d = await _create_discount(client, auth_headers)
    resp = await client.patch(f"/api/v1/discounts/{d['id']}", headers=auth_headers, json={"is_active": False})
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


async def test_update_discount_resume(client, auth_headers):
    d = await _create_discount(client, auth_headers)
    await client.patch(f"/api/v1/discounts/{d['id']}", headers=auth_headers, json={"is_active": False})
    resp = await client.patch(f"/api/v1/discounts/{d['id']}", headers=auth_headers, json={"is_active": True})
    assert resp.json()["is_active"] is True


async def test_delete_discount(client, auth_headers):
    d = await _create_discount(client, auth_headers)
    resp = await client.delete(f"/api/v1/discounts/{d['id']}", headers=auth_headers)
    assert resp.status_code == 204

    list_resp = await client.get("/api/v1/discounts/", headers=auth_headers)
    assert list_resp.json() == []


# ── redeem ────────────────────────────────────────────────────────────────────

async def test_redeem_increments_count(client, auth_headers):
    d = await _create_discount(client, auth_headers)
    resp = await client.post(f"/api/v1/discounts/{d['id']}/redeem", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["uses_count"] == 1


async def test_redeem_multiple_times(client, auth_headers):
    d = await _create_discount(client, auth_headers)
    await client.post(f"/api/v1/discounts/{d['id']}/redeem", headers=auth_headers)
    resp = await client.post(f"/api/v1/discounts/{d['id']}/redeem", headers=auth_headers)
    assert resp.json()["uses_count"] == 2


async def test_redeem_exhausts_when_max_uses_reached(client, auth_headers):
    d = await _create_discount(client, auth_headers, max_uses=2)
    await client.post(f"/api/v1/discounts/{d['id']}/redeem", headers=auth_headers)
    resp = await client.post(f"/api/v1/discounts/{d['id']}/redeem", headers=auth_headers)
    data = resp.json()
    assert data["uses_count"] == 2
    assert data["is_active"] is False  # auto-deactivated when max reached


async def test_redeem_other_shop_discount_forbidden(client, register):
    token_a = await register(email="shop_a@example.com")
    token_b = await register(email="shop_b@example.com")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    d = await _create_discount(client, headers_a)
    resp = await client.post(f"/api/v1/discounts/{d['id']}/redeem", headers=headers_b)
    assert resp.status_code == 404
