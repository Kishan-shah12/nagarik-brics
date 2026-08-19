"""Pydantic v2 schemas for the NagarikBRICS AI Core service.

Strict data validation models for all API request/response payloads.
Every schema enforces type safety, length limits, regex patterns, and
enum constraints to prevent injection payloads and malformed data.

These schemas mirror the JSON contracts defined in SCHEMA.md and
api-docs.md, ensuring type-safe serialization across the entire
NagarikBRICS platform.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ==========================================================================
# Enumerations
# ==========================================================================


class SupportedLanguage(str, Enum):
    """ISO 639-1 language codes supported by the NagarikBRICS platform.

    Covers the primary languages across all five BRICS nations plus
    major regional languages of India.
    """

    HI = "hi"   # Hindi (India)
    PT = "pt"   # Portuguese (Brazil)
    EN = "en"   # English (BRICS-wide)
    RU = "ru"   # Russian (Russia)
    ZH = "zh"   # Chinese (China)
    ZU = "zu"   # Zulu (South Africa)
    AF = "af"   # Afrikaans (South Africa)
    TA = "ta"   # Tamil (India)
    BN = "bn"   # Bengali (India)
    MR = "mr"   # Marathi (India)
    TE = "te"   # Telugu (India)
    UR = "ur"   # Urdu (India)
    KN = "kn"   # Kannada (India)
    GU = "gu"   # Gujarati (India)
    ML = "ml"   # Malayalam (India)


class BRICSCountry(str, Enum):
    """ISO 3166-1 alpha-2 codes for BRICS member nations."""

    BR = "BR"  # Brazil
    RU = "RU"  # Russia
    IN = "IN"  # India
    CN = "CN"  # China
    ZA = "ZA"  # South Africa


class InfrastructureCategory(str, Enum):
    """Infrastructure categories for feedback classification.

    Maps to the infrastructure sectors tracked by the NagarikBRICS
    heatmap and recommendation engine.
    """

    WATER_SANITATION = "water_sanitation"
    TRANSPORTATION = "transportation"
    ENERGY_POWER = "energy_power"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    HOUSING = "housing"
    DIGITAL_CONNECTIVITY = "digital_connectivity"
    WASTE_MANAGEMENT = "waste_management"
    PUBLIC_SAFETY = "public_safety"
    OTHER = "other"


class SentimentLabel(str, Enum):
    """Sentiment classification labels produced by Gemini NLP."""

    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class HotspotIntensity(str, Enum):
    """Intensity classification for geographic feedback hotspots.

    Mapped from average urgency_score:
        critical: >= 8.0
        high:     >= 6.0
        medium:   >= 4.0
        low:      < 4.0
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BudgetConfidence(str, Enum):
    """AI confidence level for budget estimates."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecommendationStatus(str, Enum):
    """Lifecycle status of a project recommendation."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class SourceChannel(str, Enum):
    """Feedback submission channel identifiers."""

    API = "api"
    WEB_FORM = "web_form"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PARTNER_IMPORT = "partner_import"


class FeedbackStatus(str, Enum):
    """Processing pipeline status for feedback records."""

    RECEIVED = "received"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


# ==========================================================================
# Shared Sub-Models
# ==========================================================================


class LocationCoords(BaseModel):
    """GPS coordinates in WGS 84 decimal degrees.

    Attributes:
        lat: Latitude in range [-90.0, 90.0].
        lng: Longitude in range [-180.0, 180.0].
    """

    lat: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitude in decimal degrees (WGS 84).",
    )
    lng: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitude in decimal degrees (WGS 84).",
    )


# ==========================================================================
# Internal Process Request (from Java Ingestion)
# ==========================================================================


class InternalProcessRequest(BaseModel):
    """Payload received from the Java Ingestion service for NLP processing.

    This is the internal contract between java-ingestion and python-ai-core.
    It arrives via POST /internal/process over the Docker bridge network.

    Attributes:
        feedback_id: UUID assigned by the Java service.
        raw_text: Original citizen feedback (10–5000 chars).
        language: ISO 639-1 language code.
        location_coords: GPS coordinates of the issue.
        country_code: BRICS nation code (may be empty string).
    """

    feedback_id: str = Field(
        ...,
        min_length=36,
        max_length=36,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        description="UUID v4 feedback identifier.",
    )
    raw_text: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Original citizen feedback text.",
    )
    language: str = Field(
        ...,
        min_length=2,
        max_length=3,
        pattern=r"^[a-z]{2,3}$",
        description="ISO 639-1 language code.",
    )
    location_coords: LocationCoords = Field(
        ...,
        description="GPS coordinates of the infrastructure issue.",
    )
    country_code: str = Field(
        default="",
        max_length=2,
        pattern=r"^[A-Z]{0,2}$",
        description="ISO 3166-1 alpha-2 country code.",
    )


class InternalProcessResponse(BaseModel):
    """NLP processing result returned to the Java Ingestion service.

    Contains all AI-enriched fields extracted by the Gemini pipeline.

    Attributes:
        feedback_id: Echo of the input feedback UUID.
        translated_text: English translation of the raw text.
        sentiment: Categorical sentiment label.
        sentiment_score: Continuous sentiment score [-1.0, 1.0].
        category: Infrastructure category classification.
        urgency_score: AI-assessed urgency [0.0, 10.0].
        keywords: Extracted key terms for clustering.
        region_name: Reverse-geocoded region name.
    """

    feedback_id: str
    translated_text: str
    sentiment: SentimentLabel
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    category: InfrastructureCategory
    urgency_score: float = Field(..., ge=0.0, le=10.0)
    keywords: list[str] = Field(default_factory=list, max_length=10)
    region_name: str = Field(default="Unknown")


# ==========================================================================
# Hotspot Analysis
# ==========================================================================


class AnalysisFilters(BaseModel):
    """Optional filters for hotspot analysis.

    All fields are optional. Omitting a filter means no constraint
    is applied for that dimension.

    Attributes:
        country_code: Filter by BRICS nation.
        category: Filter by infrastructure category.
        date_range: Filter by submission date range.
        min_urgency_score: Minimum urgency threshold.
    """

    country_code: Optional[BRICSCountry] = None
    category: Optional[InfrastructureCategory] = None
    date_range: Optional[DateRange] = None
    min_urgency_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=10.0,
    )


class DateRange(BaseModel):
    """Date range filter for analysis queries.

    Attributes:
        from_date: Start of the range (inclusive).
        to_date: End of the range (inclusive).
    """

    from_date: datetime = Field(..., alias="from")
    to_date: datetime = Field(..., alias="to")

    model_config = {"populate_by_name": True}


# Forward reference resolution
AnalysisFilters.model_rebuild()


class AnalyzeHotspotsRequest(BaseModel):
    """Request payload for POST /api/v1/ai/analyze-hotspots.

    Attributes:
        filters: Optional analysis filters. Omit for unfiltered analysis.
    """

    filters: Optional[AnalysisFilters] = None


class HotspotCluster(BaseModel):
    """A geographic cluster of citizen feedback indicating an infrastructure hotspot.

    Attributes:
        cluster_id: Stable identifier for this hotspot.
        center_coords: Geographic center of the cluster.
        radius_km: Approximate radius in kilometers.
        country_code: BRICS nation code.
        region_name: Human-readable region name.
        dominant_category: Most frequent infrastructure category.
        feedback_count: Number of feedback records in cluster.
        avg_urgency_score: Average urgency across cluster.
        avg_sentiment_score: Average sentiment across cluster.
        intensity: Computed intensity classification.
    """

    cluster_id: str
    center_coords: LocationCoords
    radius_km: float = Field(..., ge=0.0)
    country_code: BRICSCountry
    region_name: str
    dominant_category: InfrastructureCategory
    feedback_count: int = Field(..., ge=1)
    avg_urgency_score: float = Field(..., ge=0.0, le=10.0)
    avg_sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    intensity: HotspotIntensity


class AnalyzeHotspotsResponseData(BaseModel):
    """Data payload for the hotspot analysis response.

    Attributes:
        analysis_id: Unique identifier for this analysis run.
        hotspots: List of identified hotspot clusters.
        total_feedback_analyzed: Total feedback records included.
        recommendations_generated: Number of new recommendations.
    """

    analysis_id: str
    hotspots: list[HotspotCluster]
    total_feedback_analyzed: int = Field(..., ge=0)
    recommendations_generated: int = Field(..., ge=0)


# ==========================================================================
# Recommendations
# ==========================================================================


class PriorityBreakdown(BaseModel):
    """Transparent breakdown of how the priority_score was computed.

    The four components sum to the total priority_score (0–100).

    Attributes:
        citizen_urgency_component: Weighted avg urgency (max 40 pts).
        feedback_volume_component: Normalized feedback count (max 25 pts).
        infrastructure_gap_component: Index gap analysis (max 25 pts).
        sentiment_severity_component: Negative sentiment severity (max 10 pts).
    """

    citizen_urgency_component: float = Field(..., ge=0.0, le=40.0)
    feedback_volume_component: float = Field(..., ge=0.0, le=25.0)
    infrastructure_gap_component: float = Field(..., ge=0.0, le=25.0)
    sentiment_severity_component: float = Field(..., ge=0.0, le=10.0)


class BudgetEstimate(BaseModel):
    """AI-generated budget estimate with confidence level.

    Attributes:
        amount_usd: Estimated cost in US dollars.
        amount_local: Estimated cost in local currency.
        local_currency_code: ISO 4217 currency code.
        confidence: AI confidence in the estimate.
    """

    amount_usd: float = Field(..., ge=0.0)
    amount_local: Optional[float] = Field(default=None, ge=0.0)
    local_currency_code: Optional[str] = Field(
        default=None,
        pattern=r"^(INR|BRL|ZAR|RUB|CNY)$",
    )
    confidence: BudgetConfidence


class InfrastructureIndexReference(BaseModel):
    """Infrastructure index data used in gap analysis.

    Attributes:
        index_name: Name of the development index.
        region_value: Region's current score.
        national_average: National average for comparison.
        gap_percentage: How far below average (positive = needs attention).
    """

    index_name: str
    region_value: float = Field(..., ge=0.0, le=100.0)
    national_average: float = Field(..., ge=0.0, le=100.0)
    gap_percentage: float


class RecommendationLocation(BaseModel):
    """Geographic location for a project recommendation.

    Attributes:
        country_code: BRICS nation code.
        region_name: State/province/district name.
        center_coords: Geographic center of the feedback cluster.
    """

    country_code: BRICSCountry
    region_name: str
    center_coords: LocationCoords


class ProjectRecommendation(BaseModel):
    """AI-generated infrastructure project recommendation.

    Full schema as defined in SCHEMA.md. Contains all fields needed
    for the policymaker dashboard.

    Attributes:
        recommendation_id: Unique UUID identifier.
        title: Human-readable project title.
        category: Infrastructure category addressed.
        priority_score: Composite score (0–100).
        priority_breakdown: Transparent scoring breakdown.
        budget_estimate: Cost estimate with confidence.
        justification: Plain-language AI justification.
        location: Geographic location details.
        supporting_feedback_count: Number of supporting feedback records.
        supporting_feedback_ids: UUIDs of contributing feedback.
        infrastructure_index_reference: Index data used in analysis.
        sdg_alignment: UN SDG goals this project supports.
        status: Lifecycle status.
        created_at: Generation timestamp.
    """

    recommendation_id: str
    title: str = Field(..., max_length=200)
    category: InfrastructureCategory
    priority_score: float = Field(..., ge=0.0, le=100.0)
    priority_breakdown: PriorityBreakdown
    budget_estimate: BudgetEstimate
    justification: str = Field(..., min_length=50, max_length=2000)
    location: RecommendationLocation
    supporting_feedback_count: int = Field(..., ge=1)
    supporting_feedback_ids: list[str] = Field(default_factory=list)
    infrastructure_index_reference: Optional[InfrastructureIndexReference] = None
    sdg_alignment: list[str] = Field(default_factory=list)
    status: RecommendationStatus = RecommendationStatus.PUBLISHED
    created_at: datetime

    @field_validator("supporting_feedback_ids", mode="before")
    @classmethod
    def validate_feedback_ids(cls, v: list[str]) -> list[str]:
        """Validate that each feedback ID matches UUID v4 format.

        Args:
            v: List of feedback ID strings.

        Returns:
            Validated list of UUID strings.

        Raises:
            ValueError: If any ID does not match UUID format.
        """
        for fid in v:
            try:
                uuid.UUID(fid, version=4)
            except ValueError:
                raise ValueError(
                    f"Invalid feedback ID format: '{fid}'. Must be UUID v4."
                )
        return v


class Pagination(BaseModel):
    """Pagination metadata for list responses.

    Attributes:
        page: Current page number.
        page_size: Items per page.
        total_items: Total matching items.
        total_pages: Total number of pages.
    """

    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    total_items: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)


class RecommendationsResponseData(BaseModel):
    """Data payload for GET /api/v1/ai/recommendations.

    Attributes:
        recommendations: List of project recommendations.
        pagination: Pagination metadata.
    """

    recommendations: list[ProjectRecommendation]
    pagination: Pagination


# ==========================================================================
# Standard API Envelope
# ==========================================================================


class ApiMeta(BaseModel):
    """Request metadata for API response tracing.

    Attributes:
        request_id: Unique request identifier (UUID v4).
        timestamp: Response generation timestamp.
        processing_time_ms: Processing duration in milliseconds.
    """

    request_id: str
    timestamp: datetime
    processing_time_ms: Optional[int] = None


class ApiResponse(BaseModel):
    """Standard API response envelope.

    Used by all endpoints to ensure consistent response structure.

    Attributes:
        status: Either "success" or "error".
        data: Response payload (None for errors).
        error: Error details (None for success).
        meta: Request tracing metadata.
    """

    status: str = Field(..., pattern=r"^(success|error)$")
    data: Optional[dict | list | BaseModel] = None
    error: Optional[dict] = None
    meta: ApiMeta

    model_config = {"arbitrary_types_allowed": True}


# ==========================================================================
# Health Check
# ==========================================================================


class HealthResponse(BaseModel):
    """Health check response schema.

    Attributes:
        status: Service health status.
        version: Application version string.
        gemini_api: Gemini API connection status.
        feedback_count: Number of stored feedback records.
        recommendation_count: Number of generated recommendations.
        uptime_seconds: Service uptime in seconds.
    """

    status: str
    version: str
    gemini_api: str
    feedback_count: int = Field(..., ge=0)
    recommendation_count: int = Field(..., ge=0)
    uptime_seconds: int = Field(..., ge=0)
