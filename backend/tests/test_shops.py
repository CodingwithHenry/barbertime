"""Tests for /api/v1/shops/* endpoints."""
import io
import struct
import pytest
from unittest.mock import patch

import app.core.upload as _upload


def _minimal_png() -> bytes:
    """Return a 1x1 PNG image as bytes (valid magic bytes)."""
    # Minimal valid PNG: signature + IHDR + IDAT + IEND
    import zlib
    sig = b"\x89PNG\r\n\x1a\n"
    def chunk(name, data):
        c = name + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat_data = zlib.compress(b"\x00\xff\xff\xff")
    idat = chunk(b"IDAT", idat_data)
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


# ── profile ───────────────────────────────────────────────────────────────────

async def test_get_me(client, auth_headers):
    resp = await client.get("/api/v1/shops/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Test Shop"
    assert "slug" in data
    assert "is_verified" in data


async def test_update_profile(client, auth_headers):
    resp = await client.patch("/api/v1/shops/me", headers=auth_headers, json={
        "name": "Updated Shop",
        "location": "123 Main St",
        "description": "Best cuts in town",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Shop"
    assert data["location"] == "123 Main St"


async def test_update_price_list(client, auth_headers):
    resp = await client.patch("/api/v1/shops/me", headers=auth_headers, json={
        "price_list": [{"name": "Haircut", "price": 25}],
    })
    assert resp.status_code == 200
    assert resp.json()["price_list"] == [{"name": "Haircut", "price": 25}]


async def test_update_opening_hours(client, auth_headers):
    hours = {"Monday": {"open": "09:00", "close": "18:00"}}
    resp = await client.patch("/api/v1/shops/me", headers=auth_headers, json={"opening_hours": hours})
    assert resp.status_code == 200
    assert resp.json()["opening_hours"] == hours


# ── status ────────────────────────────────────────────────────────────────────

async def test_update_status_open(client, auth_headers):
    resp = await client.patch("/api/v1/shops/me/status", headers=auth_headers, json={
        "status": "open",
        "wait_time": 20,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "open"
    assert data["wait_time"] == 20


async def test_update_status_closed(client, auth_headers):
    resp = await client.patch("/api/v1/shops/me/status", headers=auth_headers, json={
        "status": "closed",
        "wait_time": 0,
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"


async def test_update_status_busy(client, auth_headers):
    resp = await client.patch("/api/v1/shops/me/status", headers=auth_headers, json={
        "status": "busy",
        "wait_time": 45,
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "busy"


# ── wait time suggestion ──────────────────────────────────────────────────────

async def test_suggest_wait_time_defaults_to_15(client, auth_headers):
    """No staff set → suggestion should be 15."""
    resp = await client.get("/api/v1/shops/me/suggest-wait-time", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["suggested_wait_time"] == 15


async def test_suggest_wait_time_uses_staff_average(client, auth_headers):
    # Create two employees with wait times
    await client.post("/api/v1/employees/", headers=auth_headers, json={"name": "Alice", "role": "Barber"})
    await client.post("/api/v1/employees/", headers=auth_headers, json={"name": "Bob", "role": "Barber"})

    emp_list = (await client.get("/api/v1/employees/", headers=auth_headers)).json()
    await client.patch(f"/api/v1/employees/{emp_list[0]['id']}", headers=auth_headers, json={"wait_time": 10})
    await client.patch(f"/api/v1/employees/{emp_list[1]['id']}", headers=auth_headers, json={"wait_time": 20})

    resp = await client.get("/api/v1/shops/me/suggest-wait-time", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["suggested_wait_time"] == 15  # average of 10 and 20


# ── photo upload ──────────────────────────────────────────────────────────────

async def test_upload_shop_photo(client, auth_headers):
    png = _minimal_png()
    with patch.object(_upload, "validate_image_bytes"):  # skip magic-bytes check in unit tests
        resp = await client.post(
            "/api/v1/shops/me/photo",
            headers=auth_headers,
            files={"file": ("photo.png", io.BytesIO(png), "image/png")},
        )
    assert resp.status_code == 200
    assert resp.json()["photo_url"].startswith("/uploads/")


async def test_upload_non_image_rejected(client, auth_headers):
    """validate_image_bytes should reject non-images (no mock here)."""
    resp = await client.post(
        "/api/v1/shops/me/photo",
        headers=auth_headers,
        files={"file": ("bad.txt", io.BytesIO(b"not an image"), "text/plain")},
    )
    assert resp.status_code == 400
