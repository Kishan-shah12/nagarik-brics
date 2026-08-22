"""NagarikBRICS Python AI Core — FastAPI Application.

This is the intelligence layer of the NagarikBRICS platform. It provides:
    - POST /internal/process — NLP processing (called by Java Ingestion)
    - POST /api/v1/ai/analyze-hotspots — Hotspot analysis for policymakers
    - GET  /api/v1/ai/recommendations — Ranked project recommendations
    - GET  /health — Service health check

All NLP processing is powered by the Google Gemini API via the google-genai SDK.
No local ML models are used — 100% cloud-based inference.

Security:
    - CORS middleware with configurable origins
    - Lightweight IP-based rate limiting
    - Strict Pydantic v2 input validation
    - No hardcoded secrets (loaded via pydantic-settings)
"""

from __future__ import annotations

import logging
import math
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.gemini_service import GeminiService
from app.schemas import (
    AnalyzeHotspotsRequest,
    AnalyzeHotspotsResponseData,
    ApiMeta,
    ApiResponse,
    HealthResponse,
    InternalProcessRequest,
    InternalProcessResponse,
    Pagination,
    ProjectRecommendation,
    RecommendationsResponseData,
    ChatRequest,
    ChatResponse,
)

# ==========================================================================
# Logging Configuration
# ==========================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ==========================================================================
# Application Factory
# ==========================================================================


@lru_cache(maxsize=1)
def _cached_settings() -> Settings:
    """Create and cache application settings (singleton).

    Returns:
        Validated Settings instance.
    """
    return get_settings()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Sets up CORS middleware, rate limiting state, the Gemini service
    singleton, and all route handlers.

    Returns:
        Configured FastAPI application instance.
    """
    settings = _cached_settings()

    application = FastAPI(
        title="NagarikBRICS AI Core",
        description="Multilingual NLP & recommendation engine for citizen infrastructure feedback.",
        version="1.0.0-mvp",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ---- CORS Middleware ----
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- Application State ----
    application.state.settings = settings
    application.state.gemini_service = GeminiService(settings)
    application.state.start_time = time.time()

    # Rate limiter state: { ip_address: [timestamp, ...] }
    application.state.rate_limit_store: dict[str, list[float]] = defaultdict(list)

    return application


app: FastAPI = create_app()


# ==========================================================================
# Rate Limiting Middleware
# ==========================================================================


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Lightweight IP-based rate limiter.

    Enforces a maximum number of requests per minute per client IP.
    Uses an in-memory sliding window — suitable for single-instance MVP.

    Args:
        request: Incoming HTTP request.
        call_next: Next middleware/handler in the chain.

    Returns:
        HTTP response (429 if rate limited, otherwise normal response).
    """
    # Skip rate limiting for health checks
    if request.url.path in ("/health", "/docs", "/redoc", "/openapi.json"):
        return await call_next(request)

    settings: Settings = request.app.state.settings
    client_ip: str = request.client.host if request.client else "unknown"
    now: float = time.time()
    window: float = 60.0  # 1-minute sliding window

    store: dict[str, list[float]] = request.app.state.rate_limit_store

    # Clean expired entries
    store[client_ip] = [
        ts for ts in store[client_ip] if now - ts < window
    ]

    if len(store[client_ip]) >= settings.rate_limit_per_minute:
        logger.warning("Rate limit exceeded for IP: %s", client_ip)
        error_response = {
            "status": "error",
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": f"Rate limit of {settings.rate_limit_per_minute} requests/minute exceeded.",
            },
            "meta": {
                "request_id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
        return JSONResponse(status_code=429, content=error_response)

    store[client_ip].append(now)
    return await call_next(request)


# ==========================================================================
# Helper Functions
# ==========================================================================


def _build_meta(request_id: str | None, processing_time_ms: int | None = None) -> ApiMeta:
    """Build standardized API response metadata.

    Args:
        request_id: Client-provided or auto-generated request ID.
        processing_time_ms: Processing duration in milliseconds.

    Returns:
        Populated ApiMeta instance.
    """
    return ApiMeta(
        request_id=request_id or str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        processing_time_ms=processing_time_ms,
    )


# ==========================================================================
# Health Check Endpoint
# ==========================================================================


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Service health check",
)
async def health_check(request: Request) -> HealthResponse:
    """Return the current health status of the AI Core service.

    Checks Gemini API connectivity and reports feedback/recommendation
    counts and uptime.

    Args:
        request: Incoming HTTP request.

    Returns:
        HealthResponse with service status and metrics.
    """
    gemini_svc: GeminiService = request.app.state.gemini_service
    uptime = int(time.time() - request.app.state.start_time)

    # Test Gemini connectivity
    gemini_status = "connected"
    try:
        gemini_svc.client.models.get(model=gemini_svc.model)
    except Exception:
        gemini_status = "disconnected"

    feedback_count = len(gemini_svc.feedback_store) if not gemini_svc.use_supabase else 0
    recommendation_count = len(gemini_svc.recommendation_store) if not gemini_svc.use_supabase else 0

    return {
        "status": "healthy",
        "version": "1.0.0-mvp",
        "gemini_api": gemini_status,
        "use_supabase": gemini_svc.use_supabase,
        "feedback_count": feedback_count,
        "recommendation_count": recommendation_count,
        "uptime_seconds": uptime,
    }


# ==========================================================================
# Internal Process Endpoint (called by Java Ingestion)
# ==========================================================================


@app.post(
    "/internal/process",
    response_model=InternalProcessResponse,
    tags=["Internal"],
    summary="Process feedback via Gemini NLP pipeline",
)
async def internal_process(
    payload: InternalProcessRequest,
    request: Request,
) -> InternalProcessResponse:
    """Process citizen feedback through the Gemini NLP pipeline.

    This is an INTERNAL endpoint called by the Java Ingestion service
    over the Docker bridge network. It is NOT exposed publicly.

    Performs in a single Gemini API call:
        1. Translation to English
        2. Sentiment classification + scoring
        3. Infrastructure category classification
        4. Urgency scoring (0–10)
        5. Keyword extraction
        6. Region identification

    Args:
        payload: Validated InternalProcessRequest from Java service.
        request: Incoming HTTP request.

    Returns:
        InternalProcessResponse with all AI-enriched fields.

    Raises:
        HTTPException: 500 if Gemini processing fails.
    """
    gemini_svc: GeminiService = request.app.state.gemini_service

    try:
        result = await gemini_svc.process_feedback(payload)
        return result
    except Exception as exc:
        logger.error(f"Feedback processing failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail={"code": "PROCESSING_FAILED", "message": f"Error: {str(exc)}"}
        )


# ==========================================================================
# Hotspot Analysis Endpoint
# ==========================================================================


@app.post(
    "/api/v1/ai/analyze-hotspots",
    tags=["AI Analysis"],
    summary="Analyze feedback hotspots and generate recommendations",
)
async def analyze_hotspots(
    request: Request,
    body: AnalyzeHotspotsRequest | None = None,
) -> dict:
    """Analyze stored feedback to identify geographic and thematic hotspots.

    Clusters citizen feedback by location and category, computes aggregate
    urgency and sentiment metrics, cross-references with infrastructure
    indices, and generates project recommendations for high/critical hotspots.

    Args:
        body: Optional request body with analysis filters.
        request: Incoming HTTP request.

    Returns:
        Standard API response envelope containing hotspot clusters
        and the number of recommendations generated.
    """
    start_time = time.time()
    gemini_svc: GeminiService = request.app.state.gemini_service
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))

    # Extract filters
    country_code: str | None = None
    category: str | None = None
    min_urgency: float | None = None

    if body and body.filters:
        if body.filters.country_code:
            country_code = body.filters.country_code.value
        if body.filters.category:
            category = body.filters.category.value
        min_urgency = body.filters.min_urgency_score

    # Run hotspot analysis
    hotspots, total_analyzed = await gemini_svc.analyze_hotspots(
        country_code=country_code,
        category=category,
        min_urgency=min_urgency,
    )

    # Generate recommendations for actionable hotspots
    new_recs = await gemini_svc.generate_recommendations(hotspots)

    analysis_id = str(uuid.uuid4())
    processing_time = int((time.time() - start_time) * 1000)

    response_data = AnalyzeHotspotsResponseData(
        analysis_id=analysis_id,
        hotspots=hotspots,
        total_feedback_analyzed=total_analyzed,
        recommendations_generated=len(new_recs),
    )

    return {
        "status": "success",
        "data": response_data.model_dump(),
        "meta": _build_meta(request_id, processing_time).model_dump(mode="json"),
    }


# ==========================================================================
# Recommendations Endpoint
# ==========================================================================


@app.get(
    "/api/v1/ai/recommendations",
    tags=["AI Analysis"],
    summary="Retrieve ranked infrastructure project recommendations",
)
async def get_recommendations(
    request: Request,
    country_code: str | None = Query(
        default=None,
        pattern=r"^(BR|RU|IN|CN|ZA)$",
        description="Filter by BRICS country code.",
    ),
    category: str | None = Query(
        default=None,
        description="Filter by infrastructure category.",
    ),
    min_priority: float = Query(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Minimum priority score (0–100).",
    ),
    status: str = Query(
        default="published",
        pattern=r"^(draft|published|accepted|rejected)$",
        description="Filter by recommendation status.",
    ),
    sort_by: str = Query(
        default="priority_score",
        pattern=r"^(priority_score|budget_estimate|feedback_count|created_at)$",
        description="Sort field.",
    ),
    sort_order: str = Query(
        default="desc",
        pattern=r"^(asc|desc)$",
        description="Sort direction.",
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="Page number (1-indexed).",
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Items per page.",
    ),
) -> dict:
    """Retrieve the current list of AI-generated project recommendations.

    Returns recommendations sorted by priority score descending (default),
    with optional filtering by country, category, minimum priority, and
    status. Supports pagination.

    Args:
        request: Incoming HTTP request.
        country_code: BRICS country filter (BR, RU, IN, CN, ZA).
        category: Infrastructure category filter.
        min_priority: Minimum priority score threshold.
        status: Recommendation status filter.
        sort_by: Field to sort results by.
        sort_order: Sort direction (asc/desc).
        page: Page number for pagination.
        page_size: Number of items per page.

    Returns:
        Standard API response envelope with paginated recommendations.
    """
    start_time = time.time()
    gemini_svc: GeminiService = request.app.state.gemini_service
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))

    paginated, total = gemini_svc.get_recommendations(
        country_code=country_code,
        category=category,
        min_priority=min_priority,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 0
    processing_time = int((time.time() - start_time) * 1000)

    response_data = RecommendationsResponseData(
        recommendations=paginated,
        pagination=Pagination(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
        ),
    )

    return {
        "status": "success",
        "data": response_data.model_dump(mode="json"),
        "meta": _build_meta(request_id, processing_time).model_dump(mode="json"),
    }

@app.post(
    "/api/v1/ai/chat",
    response_model=ChatResponse,
    tags=["AI Analysis"],
    summary="AI Assistant Chat Endpoint",
)
async def ai_chat(
    request: Request,
    body: ChatRequest,
) -> dict:
    gemini_svc: GeminiService = request.app.state.gemini_service
    try:
        reply = await gemini_svc.chat(body.prompt, body.language)
        return {"reply": reply}
    except Exception as exc:
        logger.error(f"Chat failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail={"code": "CHAT_FAILED", "message": str(exc)}
        )

@app.get("/api/v1/ai/feedback/recent", tags=["AI Analysis"], summary="Get recent feedback")
async def get_recent_feedback(request: Request):
    gemini_svc: GeminiService = request.app.state.gemini_service
    if not gemini_svc.use_supabase:
        return {"data": []}
    try:
        resp = gemini_svc.supabase.table("citizen_feedback").select("*").order("created_at", desc=True).limit(5).execute()
        # format data for frontend
        data = []
        for r in resp.data:
            data.append({
                "source": "App",
                "message": r.get("raw_text", ""),
                "tag": r.get("category", ""),
                "urgency": r.get("urgency_score", 1)
            })
        return {"data": data}
    except Exception as exc:
        logger.error(f"Failed to fetch recent feedback: {exc}")
        return {"data": []}
