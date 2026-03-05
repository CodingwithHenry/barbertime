import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import get_db
from app.core.deps import get_current_shop
from app.core.limiter import limiter
from app.core.security import hash_password, verify_password, create_access_token
from app.models.shop import Shop
from app.models.verification_code import VerificationCode, VerificationPurpose
from app.schemas.shop import ShopRegister, ShopLogin, TokenResponse
from app.services import email as email_service

router = APIRouter(prefix="/auth", tags=["auth"])

CODE_TTL_MINUTES = 15


# ── helpers ──────────────────────────────────────────────────────────────────

async def _issue_code(to: str, purpose: VerificationPurpose, db: AsyncSession) -> None:
    """Invalidate old codes for this email+purpose, create a new one, send it."""
    await db.execute(
        update(VerificationCode)
        .where(
            VerificationCode.email == to,
            VerificationCode.purpose == purpose,
            VerificationCode.used == False,  # noqa: E712
        )
        .values(used=True)
    )
    code_str = email_service.generate_code()
    code = VerificationCode(
        email=to,
        code=code_str,
        purpose=purpose,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=CODE_TTL_MINUTES),
    )
    db.add(code)
    await db.commit()
    await email_service.send_code(to, code_str, purpose)


async def _consume_code(email: str, code_str: str, purpose: VerificationPurpose, db: AsyncSession) -> bool:
    """Return True and mark used if code is valid, False otherwise."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(VerificationCode)
        .where(
            VerificationCode.email == email,
            VerificationCode.code == code_str,
            VerificationCode.purpose == purpose,
            VerificationCode.expires_at > now,
            VerificationCode.used == False,  # noqa: E712
        )
        .with_for_update()
    )
    code = result.scalar_one_or_none()
    if not code:
        return False
    code.used = True
    await db.commit()
    return True


# ── request schemas ───────────────────────────────────────────────────────────

class VerifyEmailRequest(BaseModel):
    code: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: ShopRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shop).where(Shop.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    shop = Shop(
        email=body.email,
        hashed_password=hash_password(body.password),
        name=body.name,
        slug=str(uuid.uuid4()),
        is_verified=False,
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    await _issue_code(shop.email, VerificationPurpose.email_verify, db)

    return TokenResponse(access_token=create_access_token(shop.id))


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: ShopLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shop).where(Shop.email == body.email))
    shop = result.scalar_one_or_none()
    if not shop or not verify_password(body.password, shop.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(shop.id))


@router.post("/verify-email")
@limiter.limit("10/minute")
async def verify_email(
    request: Request,
    body: VerifyEmailRequest,
    shop: Shop = Depends(get_current_shop),
    db: AsyncSession = Depends(get_db),
):
    if shop.is_verified:
        return {"message": "Already verified"}
    ok = await _consume_code(shop.email, body.code, VerificationPurpose.email_verify, db)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    shop.is_verified = True
    await db.commit()
    return {"message": "Email verified"}


@router.post("/resend-verification")
@limiter.limit("3/minute")
async def resend_verification(
    request: Request,
    shop: Shop = Depends(get_current_shop),
    db: AsyncSession = Depends(get_db),
):
    if shop.is_verified:
        raise HTTPException(status_code=400, detail="Already verified")
    await _issue_code(shop.email, VerificationPurpose.email_verify, db)
    return {"message": "Code sent"}


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Shop).where(Shop.email == body.email, Shop.is_active == True))
    shop = result.scalar_one_or_none()
    # Always return 200 — don't reveal whether the email exists
    if shop:
        await _issue_code(shop.email, VerificationPurpose.password_reset, db)
    return {"message": "If that email is registered, a code has been sent."}


@router.post("/reset-password")
@limiter.limit("10/minute")
async def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    ok = await _consume_code(body.email, body.code, VerificationPurpose.password_reset, db)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    result = await db.execute(select(Shop).where(Shop.email == body.email))
    shop = result.scalar_one_or_none()
    if not shop:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    if len(body.new_password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    shop.hashed_password = hash_password(body.new_password)
    await db.commit()
    return {"message": "Password updated"}
