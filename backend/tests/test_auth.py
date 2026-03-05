"""Tests for /api/v1/auth/* endpoints."""
import pytest
from sqlalchemy import select

from app.models.verification_code import VerificationPurpose
from tests.conftest import _TestSession, get_verification_code


# ── register ──────────────────────────────────────────────────────────────────

async def test_register_returns_token(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "password": "password123",
        "name": "My Shop",
    })
    assert resp.status_code == 201
    assert "access_token" in resp.json()


async def test_register_duplicate_email(client):
    body = {"email": "dup@example.com", "password": "password123", "name": "Shop"}
    await client.post("/api/v1/auth/register", json=body)
    resp = await client.post("/api/v1/auth/register", json=body)
    assert resp.status_code == 400


async def test_register_creates_unverified_shop(client):
    await client.post("/api/v1/auth/register", json={
        "email": "unverified@example.com",
        "password": "password123",
        "name": "Shop",
    })
    from app.models.shop import Shop
    async with _TestSession() as db:
        result = await db.execute(select(Shop).where(Shop.email == "unverified@example.com"))
        shop = result.scalar_one()
    assert shop.is_verified is False


async def test_register_issues_verification_code(client):
    await client.post("/api/v1/auth/register", json={
        "email": "codegen@example.com",
        "password": "password123",
        "name": "Shop",
    })
    code = await get_verification_code("codegen@example.com", VerificationPurpose.email_verify)
    assert len(code) == 6
    assert code.isdigit()


# ── login ─────────────────────────────────────────────────────────────────────

async def test_login_success(client, register):
    await register(email="login@example.com", password="mypassword")
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "mypassword",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_wrong_password(client, register):
    await register(email="login2@example.com", password="correct")
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login2@example.com",
        "password": "wrong",
    })
    assert resp.status_code == 401


async def test_login_unknown_email(client):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "password123",
    })
    assert resp.status_code == 401


# ── email verification ────────────────────────────────────────────────────────

async def test_verify_email_success(client, auth_headers):
    from app.models.shop import Shop
    async with _TestSession() as db:
        result = await db.execute(select(Shop))
        shop = result.scalars().first()
        email = shop.email

    code = await get_verification_code(email, VerificationPurpose.email_verify)
    resp = await client.post("/api/v1/auth/verify-email", json={"code": code}, headers=auth_headers)
    assert resp.status_code == 200

    async with _TestSession() as db:
        result = await db.execute(select(Shop).where(Shop.email == email))
        shop = result.scalar_one()
    assert shop.is_verified is True


async def test_verify_email_wrong_code(client, auth_headers):
    resp = await client.post("/api/v1/auth/verify-email", json={"code": "000000"}, headers=auth_headers)
    assert resp.status_code == 400


async def test_verify_email_already_verified(client, auth_headers):
    from app.models.shop import Shop
    async with _TestSession() as db:
        result = await db.execute(select(Shop))
        shop = result.scalars().first()
        email = shop.email

    code = await get_verification_code(email, VerificationPurpose.email_verify)
    await client.post("/api/v1/auth/verify-email", json={"code": code}, headers=auth_headers)
    # Second call should still succeed gracefully
    resp = await client.post("/api/v1/auth/verify-email", json={"code": code}, headers=auth_headers)
    assert resp.status_code == 200


async def test_resend_verification(client, auth_headers):
    resp = await client.post("/api/v1/auth/resend-verification", headers=auth_headers)
    assert resp.status_code == 200

    from app.models.shop import Shop
    async with _TestSession() as db:
        result = await db.execute(select(Shop))
        shop = result.scalars().first()
    # A fresh code should now exist
    code = await get_verification_code(shop.email, VerificationPurpose.email_verify)
    assert len(code) == 6


# ── password reset ────────────────────────────────────────────────────────────

async def test_forgot_password_returns_200_for_unknown_email(client):
    """Should not reveal whether the email exists."""
    resp = await client.post("/api/v1/auth/forgot-password", json={"email": "ghost@example.com"})
    assert resp.status_code == 200


async def test_forgot_password_issues_code(client, register):
    await register(email="reset@example.com")
    await client.post("/api/v1/auth/forgot-password", json={"email": "reset@example.com"})
    code = await get_verification_code("reset@example.com", VerificationPurpose.password_reset)
    assert len(code) == 6


async def test_reset_password_success(client, register):
    await register(email="chpw@example.com", password="oldpass1")
    await client.post("/api/v1/auth/forgot-password", json={"email": "chpw@example.com"})
    code = await get_verification_code("chpw@example.com", VerificationPurpose.password_reset)

    resp = await client.post("/api/v1/auth/reset-password", json={
        "email": "chpw@example.com",
        "code": code,
        "new_password": "newpass99",
    })
    assert resp.status_code == 200

    # Can log in with the new password
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "chpw@example.com",
        "password": "newpass99",
    })
    assert login_resp.status_code == 200


async def test_reset_password_wrong_code(client, register):
    await register(email="wrcode@example.com")
    resp = await client.post("/api/v1/auth/reset-password", json={
        "email": "wrcode@example.com",
        "code": "000000",
        "new_password": "newpass99",
    })
    assert resp.status_code == 400


async def test_reset_password_too_short(client, register):
    await register(email="short@example.com")
    await client.post("/api/v1/auth/forgot-password", json={"email": "short@example.com"})
    code = await get_verification_code("short@example.com", VerificationPurpose.password_reset)
    resp = await client.post("/api/v1/auth/reset-password", json={
        "email": "short@example.com",
        "code": code,
        "new_password": "abc",
    })
    assert resp.status_code == 422


# ── protected endpoint requires token ─────────────────────────────────────────

async def test_get_me_requires_auth(client):
    resp = await client.get("/api/v1/shops/me")
    assert resp.status_code == 403


async def test_get_me_returns_shop(client, auth_headers):
    resp = await client.get("/api/v1/shops/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "barber@example.com"
