import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
import os

from app.core.config import settings
from app.core.limiter import limiter
from app.routes import auth, shops, employees, reservations, discounts, stripe_routes, public, ws
from app.services.reservation_cleanup import run_cleanup_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("/app/uploads", exist_ok=True)
    cleanup_task = asyncio.create_task(run_cleanup_loop())
    yield
    cleanup_task.cancel()


app = FastAPI(title="BarberTime API", lifespan=lifespan)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Too many requests, please try again later."})

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(shops.router, prefix="/api/v1")
app.include_router(employees.router, prefix="/api/v1")
app.include_router(reservations.router, prefix="/api/v1")
app.include_router(discounts.router, prefix="/api/v1")
app.include_router(stripe_routes.router, prefix="/api/v1")
app.include_router(public.router, prefix="/api/v1")
app.include_router(ws.router)

app.mount("/uploads", StaticFiles(directory="/app/uploads"), name="uploads")


@app.get("/health")
async def health():
    return {"status": "ok"}
