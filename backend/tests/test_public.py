"""Tests for /api/v1/public/* endpoints (customer-facing)."""
import pytest
from sqlalchemy import select

from tests.conftest import _TestSession


async def _make_shop_visible(client, auth_headers):
    """Set subscription to active and status to open so the shop appears in public listing."""
    async with _TestSession() as db:
        from app.models.shop import Shop
        result = await db.execute(select(Shop))
        shop = result.scalars().first()
        shop.subscription_status = "active"
        shop.latitude = 52.52
        shop.longitude = 13.40
        await db.commit()
    await client.patch("/api/v1/shops/me/status", headers=auth_headers, json={
        "status": "open",
        "wait_time": 10,
    })


# ── public shop list ──────────────────────────────────────────────────────────

async def test_list_shops_empty_when_none_subscribed(client):
    resp = await client.get("/api/v1/public/shops")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_shops_shows_subscribed(client, auth_headers):
    await _make_shop_visible(client, auth_headers)
    resp = await client.get("/api/v1/public/shops")
    assert resp.status_code == 200
    shops = resp.json()
    assert len(shops) == 1
    assert shops[0]["status"] == "open"
    assert shops[0]["wait_time"] == 10


async def test_list_shops_hides_inactive_subscription(client, auth_headers):
    """Shops with subscription_status = 'inactive' must not appear."""
    # Shop has subscription_status='inactive' by default — should stay hidden
    await client.patch("/api/v1/shops/me/status", headers=auth_headers, json={
        "status": "open",
        "wait_time": 5,
    })
    resp = await client.get("/api/v1/public/shops")
    assert resp.json() == []


async def test_list_shops_sorted_by_proximity(client, register):
    """Shops closer to the query coordinates should come first."""
    token_near = await register(email="near@example.com", name="Near Shop")
    token_far = await register(email="far@example.com", name="Far Shop")

    async with _TestSession() as db:
        from app.models.shop import Shop
        result = await db.execute(select(Shop))
        shops = result.scalars().all()
        for shop in shops:
            shop.subscription_status = "active"
            if shop.email == "near@example.com":
                shop.latitude = 52.52
                shop.longitude = 13.40
            else:
                shop.latitude = 48.14
                shop.longitude = 11.58
        await db.commit()

    # Query from Berlin (lat=52.52, lon=13.40) — near shop should be first
    resp = await client.get("/api/v1/public/shops?lat=52.52&lon=13.40")
    assert resp.status_code == 200
    shops = resp.json()
    assert len(shops) == 2
    assert shops[0]["name"] == "Near Shop"


# ── public shop detail ────────────────────────────────────────────────────────

async def test_get_shop_by_slug(client, auth_headers):
    await _make_shop_visible(client, auth_headers)
    me = (await client.get("/api/v1/shops/me", headers=auth_headers)).json()
    slug = me["slug"]

    resp = await client.get(f"/api/v1/public/shops/{slug}")
    assert resp.status_code == 200
    assert resp.json()["slug"] == slug


async def test_get_shop_not_found(client):
    resp = await client.get("/api/v1/public/shops/nonexistent-slug")
    assert resp.status_code == 404


async def test_slug_is_uuid_format(client, auth_headers):
    me = (await client.get("/api/v1/shops/me", headers=auth_headers)).json()
    import re
    uuid_re = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    assert uuid_re.match(me["slug"]), f"Slug {me['slug']!r} is not a UUID"


# ── public employees ──────────────────────────────────────────────────────────

async def test_get_shop_employees(client, auth_headers):
    await _make_shop_visible(client, auth_headers)
    me = (await client.get("/api/v1/shops/me", headers=auth_headers)).json()

    await client.post("/api/v1/employees/", headers=auth_headers, json={"name": "Alice"})
    await client.post("/api/v1/employees/", headers=auth_headers, json={"name": "Bob"})

    resp = await client.get(f"/api/v1/public/shops/{me['slug']}/employees")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_get_shop_employees_excludes_inactive(client, auth_headers):
    await _make_shop_visible(client, auth_headers)
    me = (await client.get("/api/v1/shops/me", headers=auth_headers)).json()

    emp_resp = await client.post("/api/v1/employees/", headers=auth_headers, json={"name": "Gone"})
    emp_id = emp_resp.json()["id"]
    await client.patch(f"/api/v1/employees/{emp_id}", headers=auth_headers, json={"is_active": False})

    resp = await client.get(f"/api/v1/public/shops/{me['slug']}/employees")
    assert resp.json() == []


# ── public discounts ──────────────────────────────────────────────────────────

async def test_get_shop_discounts(client, auth_headers):
    await _make_shop_visible(client, auth_headers)
    me = (await client.get("/api/v1/shops/me", headers=auth_headers)).json()

    await client.post("/api/v1/discounts/", headers=auth_headers, json={"title": "Summer Deal"})

    resp = await client.get(f"/api/v1/public/shops/{me['slug']}/discounts")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["title"] == "Summer Deal"


async def test_public_discounts_hides_inactive(client, auth_headers):
    await _make_shop_visible(client, auth_headers)
    me = (await client.get("/api/v1/shops/me", headers=auth_headers)).json()

    d_resp = await client.post("/api/v1/discounts/", headers=auth_headers, json={"title": "Hidden Deal"})
    d_id = d_resp.json()["id"]
    await client.patch(f"/api/v1/discounts/{d_id}", headers=auth_headers, json={"is_active": False})

    resp = await client.get(f"/api/v1/public/shops/{me['slug']}/discounts")
    assert resp.json() == []


async def test_public_discounts_hides_exhausted(client, auth_headers):
    await _make_shop_visible(client, auth_headers)
    me = (await client.get("/api/v1/shops/me", headers=auth_headers)).json()

    d_resp = await client.post("/api/v1/discounts/", headers=auth_headers, json={
        "title": "Only One",
        "max_uses": 1,
    })
    d_id = d_resp.json()["id"]
    await client.post(f"/api/v1/discounts/{d_id}/redeem", headers=auth_headers)

    resp = await client.get(f"/api/v1/public/shops/{me['slug']}/discounts")
    assert resp.json() == []


# ── health ────────────────────────────────────────────────────────────────────

async def test_health_endpoint(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
