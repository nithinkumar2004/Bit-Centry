"""
BidSentry — AI-Powered Tender Evaluation System
Main FastAPI application entry point.
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Import routes
from backend.routes.tenders import router as tenders_router
from backend.routes.bidders import router as bidders_router
from backend.routes.evaluations import router as evaluations_router
from backend.routes.audit import router as audit_router
from backend.db.mongodb import Database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting BidSentry...")
    await Database.connect()
    
    # Ensure upload directory exists
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(os.path.join(upload_dir, "tenders"), exist_ok=True)
    os.makedirs(os.path.join(upload_dir, "bidders"), exist_ok=True)
    
    logger.info("✅ BidSentry is ready!")
    yield
    
    # Shutdown
    await Database.disconnect()
    logger.info("👋 BidSentry stopped")


# Create FastAPI app
app = FastAPI(
    title="BidSentry API",
    description="AI-Powered Tender Evaluation System — Explainable, tamper-evident, audit-ready.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS — allow React dev server
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tenders_router)
app.include_router(bidders_router)
app.include_router(evaluations_router)
app.include_router(audit_router)


# Dashboard stats endpoint
@app.get("/api/dashboard/stats")
async def dashboard_stats():
    """Get dashboard statistics."""
    db = Database.get_db()
    
    tender_count = await db.tenders.count_documents({})
    bidder_count = await db.bidders.count_documents({})
    eval_count = await db.evaluations.count_documents({})
    audit_count = await db.audit_logs.count_documents({})

    # Calculate pass rate
    eligible_count = await db.evaluations.count_documents({"final_status": "Eligible"})
    pass_rate = (eligible_count / eval_count * 100) if eval_count > 0 else 0

    # Needs review count
    review_count = await db.evaluations.count_documents({"final_status": "Needs Manual Review"})

    # Recent activity (last 10)
    recent_logs = []
    cursor = db.audit_logs.find().sort("timestamp", -1).limit(10)
    async for log in cursor:
        recent_logs.append({
            "id": str(log["_id"]),
            "action": log.get("action", ""),
            "entity_type": log.get("entity_type", ""),
            "entity_id": log.get("entity_id", ""),
            "timestamp": log.get("timestamp", ""),
            "details": log.get("details", {})
        })

    return {
        "tender_count": tender_count,
        "bidder_count": bidder_count,
        "evaluation_count": eval_count,
        "audit_count": audit_count,
        "eligible_count": eligible_count,
        "not_eligible_count": await db.evaluations.count_documents({"final_status": "Not Eligible"}),
        "review_count": review_count,
        "pass_rate": round(pass_rate, 1),
        "recent_activity": recent_logs
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "BidSentry API", "version": "1.0.0"}


# Run with: uvicorn backend.main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
