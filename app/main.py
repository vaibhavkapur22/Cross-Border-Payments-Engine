from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import engine, Base
from app.api.quotes import router as quotes_router
from app.api.transfers import router as transfers_router
from app.api.admin import router as admin_router
from app.api.comparison import router as comparison_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Cross-Border Payments Engine",
    description="Stablecoin-powered USD→INR remittance engine with SWIFT comparison",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(quotes_router, prefix="/quotes", tags=["Quotes"])
app.include_router(transfers_router, prefix="/transfers", tags=["Transfers"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(comparison_router, tags=["Comparison"])


@app.get("/health")
async def health():
    return {"status": "ok"}
