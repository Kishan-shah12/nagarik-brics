"""Gemini AI service for multilingual NLP processing and recommendation generation.

Integrates with the Google Gemini API via the `google-genai` SDK to perform:
    - Multilingual translation (BRICS languages → English)
    - Sentiment analysis (categorical + continuous score)
    - Infrastructure category classification
    - Urgency scoring
    - Keyword extraction
    - Project recommendation generation with budget estimates

All NLP processing is performed remotely via the Gemini API.
No local ML models, .pkl files, or heavy dependencies are used.

CONSTRAINT: 100% reliance on the external Gemini API.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone

from google import genai
from supabase import create_client, Client

from app.config import Settings
from app.schemas import (
    BRICSCountry,
    BudgetConfidence,
    BudgetEstimate,
    HotspotCluster,
    HotspotIntensity,
    InfrastructureCategory,
    InfrastructureIndexReference,
    InternalProcessRequest,
    InternalProcessResponse,
    LocationCoords,
    PriorityBreakdown,
    ProjectRecommendation,
    RecommendationLocation,
    RecommendationStatus,
    SentimentLabel,
)

logger = logging.getLogger(__name__)


# ==========================================================================
# Mock Infrastructure Index Data (Seeded for MVP)
# ==========================================================================
# In production, this would come from a database populated by
# UNDP, World Bank, and national statistics bureaus.

INFRASTRUCTURE_INDICES: dict[str, dict[str, dict[str, float]]] = {
    "IN": {
        "Uttar Pradesh": {
            "HDI": 48.2,
            "SDG 6.1 - Safe Water Access": 42.3,
            "SDG 7.1 - Electricity Access": 78.1,
            "SDG 9.1 - Infrastructure Quality": 38.5,
            "Road Quality Index": 41.2,
        },
        "Maharashtra": {
            "HDI": 69.5,
            "SDG 6.1 - Safe Water Access": 71.2,
            "SDG 7.1 - Electricity Access": 92.3,
            "SDG 9.1 - Infrastructure Quality": 67.8,
            "Road Quality Index": 62.1,
        },
        "Tamil Nadu": {
            "HDI": 72.1,
            "SDG 6.1 - Safe Water Access": 68.9,
            "SDG 7.1 - Electricity Access": 95.2,
            "SDG 9.1 - Infrastructure Quality": 71.3,
            "Road Quality Index": 69.4,
        },
        "Bihar": {
            "HDI": 38.7,
            "SDG 6.1 - Safe Water Access": 35.1,
            "SDG 7.1 - Electricity Access": 52.4,
            "SDG 9.1 - Infrastructure Quality": 28.9,
            "Road Quality Index": 31.6,
        },
    },
    "BR": {
        "São Paulo": {
            "HDI": 78.3,
            "SDG 6.1 - Safe Water Access": 82.1,
            "SDG 9.1 - Infrastructure Quality": 65.4,
            "Road Quality Index": 55.8,
            "Digital Connectivity Index": 74.2,
        },
        "Bahia": {
            "HDI": 52.1,
            "SDG 6.1 - Safe Water Access": 48.9,
            "SDG 9.1 - Infrastructure Quality": 39.2,
            "Road Quality Index": 35.4,
            "Digital Connectivity Index": 41.8,
        },
    },
    "ZA": {
        "Gauteng": {
            "HDI": 71.8,
            "SDG 6.1 - Safe Water Access": 88.2,
            "SDG 7.1 - Electricity Access": 84.5,
            "SDG 9.1 - Infrastructure Quality": 62.1,
            "Road Quality Index": 58.3,
        },
        "Eastern Cape": {
            "HDI": 44.2,
            "SDG 6.1 - Safe Water Access": 39.5,
            "SDG 7.1 - Electricity Access": 61.2,
            "SDG 9.1 - Infrastructure Quality": 31.8,
            "Road Quality Index": 28.9,
        },
    },
    "RU": {
        "Moscow Oblast": {
            "HDI": 82.4,
            "SDG 6.1 - Safe Water Access": 91.3,
            "SDG 9.1 - Infrastructure Quality": 78.5,
            "Road Quality Index": 72.1,
            "Digital Connectivity Index": 85.6,
        },
        "Dagestan": {
            "HDI": 51.3,
            "SDG 6.1 - Safe Water Access": 55.2,
            "SDG 9.1 - Infrastructure Quality": 35.1,
            "Road Quality Index": 32.8,
            "Digital Connectivity Index": 38.4,
        },
    },
    "CN": {
        "Beijing": {
            "HDI": 89.1,
            "SDG 6.1 - Safe Water Access": 95.2,
            "SDG 9.1 - Infrastructure Quality": 91.3,
            "Road Quality Index": 88.4,
            "Digital Connectivity Index": 92.7,
        },
        "Guizhou": {
            "HDI": 54.8,
            "SDG 6.1 - Safe Water Access": 62.3,
            "SDG 9.1 - Infrastructure Quality": 48.5,
            "Road Quality Index": 45.2,
            "Digital Connectivity Index": 51.3,
        },
    },
}

NATIONAL_AVERAGES: dict[str, dict[str, float]] = {
    "IN": {"HDI": 64.5, "SDG 6.1 - Safe Water Access": 61.2, "SDG 7.1 - Electricity Access": 85.4, "SDG 9.1 - Infrastructure Quality": 52.3, "Road Quality Index": 51.8},
    "BR": {"HDI": 65.2, "SDG 6.1 - Safe Water Access": 65.5, "SDG 9.1 - Infrastructure Quality": 52.3, "Road Quality Index": 45.6, "Digital Connectivity Index": 58.0},
    "ZA": {"HDI": 58.0, "SDG 6.1 - Safe Water Access": 63.9, "SDG 7.1 - Electricity Access": 72.9, "SDG 9.1 - Infrastructure Quality": 47.0, "Road Quality Index": 43.6},
    "RU": {"HDI": 66.9, "SDG 6.1 - Safe Water Access": 73.3, "SDG 9.1 - Infrastructure Quality": 56.8, "Road Quality Index": 52.5, "Digital Connectivity Index": 62.0},
    "CN": {"HDI": 72.0, "SDG 6.1 - Safe Water Access": 78.8, "SDG 9.1 - Infrastructure Quality": 69.9, "Road Quality Index": 66.8, "Digital Connectivity Index": 72.0},
}

# Category → SDG mapping
CATEGORY_SDG_MAP: dict[str, list[str]] = {
    "water_sanitation": ["SDG 6 - Clean Water and Sanitation", "SDG 3 - Good Health and Well-Being"],
    "transportation": ["SDG 9 - Industry, Innovation and Infrastructure", "SDG 11 - Sustainable Cities"],
    "energy_power": ["SDG 7 - Affordable and Clean Energy", "SDG 13 - Climate Action"],
    "healthcare": ["SDG 3 - Good Health and Well-Being"],
    "education": ["SDG 4 - Quality Education"],
    "housing": ["SDG 11 - Sustainable Cities", "SDG 1 - No Poverty"],
    "digital_connectivity": ["SDG 9 - Industry, Innovation and Infrastructure"],
    "waste_management": ["SDG 11 - Sustainable Cities", "SDG 12 - Responsible Consumption"],
    "public_safety": ["SDG 16 - Peace, Justice and Strong Institutions"],
    "other": ["SDG 11 - Sustainable Cities"],
}

# Category → relevant infrastructure index mapping
CATEGORY_INDEX_MAP: dict[str, str] = {
    "water_sanitation": "SDG 6.1 - Safe Water Access",
    "transportation": "Road Quality Index",
    "energy_power": "SDG 7.1 - Electricity Access",
    "healthcare": "HDI",
    "education": "HDI",
    "housing": "HDI",
    "digital_connectivity": "Digital Connectivity Index",
    "waste_management": "SDG 9.1 - Infrastructure Quality",
    "public_safety": "SDG 9.1 - Infrastructure Quality",
    "other": "HDI",
}

# Currency codes per BRICS nation
COUNTRY_CURRENCY: dict[str, str] = {
    "BR": "BRL",
    "RU": "RUB",
    "IN": "INR",
    "CN": "CNY",
    "ZA": "ZAR",
}


class GeminiService:
    """Gemini-powered NLP and recommendation engine.

    Handles all AI processing for the NagarikBRICS platform using the
    Google Gemini API. All NLP is performed remotely — zero local models.

    Attributes:
        client: Initialized google-genai client instance.
        model: Gemini model identifier for content generation.
        feedback_store: In-memory store of processed feedback records.
        recommendation_store: In-memory store of generated recommendations.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the Gemini service with API credentials.

        Args:
            settings: Application settings containing the Gemini API key.
        """
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model: str = settings.gemini_model
        
        if settings.supabase_url and settings.supabase_key:
            self.supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
            self.use_supabase = True
        else:
            self.use_supabase = False
            self.feedback_store: list[dict] = []
            self.recommendation_store: list[ProjectRecommendation] = []

        logger.info(
            "GeminiService initialized with model: %s", self.model
        )


    def _generate_with_fallback(self, **kwargs) -> "genai.types.GenerateContentResponse":
        fallback_models = [
            self.model,
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash",
            "gemini-2.5-flash-lite"
        ]
        
        last_exception = None
        for model in fallback_models:
            try:
                kwargs["model"] = model
                logger.info("Attempting generation with model: %s", model)
                return self.client.models.generate_content(**kwargs)
            except Exception as exc:
                last_exception = exc
                err_msg = str(exc).lower()
                if "429" in err_msg or "resource_exhausted" in err_msg or "quota" in err_msg:
                    logger.warning("Rate limit hit for model %s, falling back to next model.", model)
                    continue
                # If it is not a rate limit error, raise it immediately
                raise exc
        
        # If all models failed with rate limits
        if last_exception is not None:
            raise last_exception
        raise RuntimeError("No fallback models were available to attempt generation.")

    async def process_feedback(
        self, request: InternalProcessRequest
    ) -> InternalProcessResponse:
        """Process citizen feedback through the Gemini NLP pipeline.

        Performs translation, sentiment analysis, category classification,
        urgency scoring, and keyword extraction in a single Gemini call
        using structured output prompting.

        Args:
            request: Validated feedback from the Java Ingestion service.

        Returns:
            InternalProcessResponse with all AI-enriched fields.

        Raises:
            Exception: If the Gemini API call fails or returns
                unparseable output.
        """
        prompt = self._build_nlp_prompt(request)

        logger.info(
            "Processing feedback %s (lang=%s) via Gemini",
            request.feedback_id,
            request.language,
        )

        try:
            response = self._generate_with_fallback(
                model=self.model,
                contents=prompt,
            )

            result = self._parse_nlp_response(
                response.text, request
            )

            # Store for later hotspot analysis
            feedback_record = {
                "feedback_id": request.feedback_id,
                "raw_text": request.raw_text,
                "language": request.language,
                "translated_text": result.translated_text,
                "country_code": result.region_name
                    and request.country_code or request.country_code,
                "region_name": result.region_name,
                "sentiment": result.sentiment.value,
                "sentiment_score": result.sentiment_score,
                "category": result.category.value,
                "urgency_score": result.urgency_score,
                "keywords": result.keywords,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            if self.use_supabase:
                feedback_record["lat"] = request.location_coords.lat
                feedback_record["lng"] = request.location_coords.lng
                self.supabase.table("citizen_feedback").insert(feedback_record).execute()
            else:
                feedback_record["location_coords"] = {
                    "lat": request.location_coords.lat,
                    "lng": request.location_coords.lng,
                }
                self.feedback_store.append(feedback_record)

            logger.info(
                "Feedback %s processed: category=%s, urgency=%.1f, sentiment=%s",
                request.feedback_id,
                result.category.value,
                result.urgency_score,
                result.sentiment.value,
            )

            return result

        except Exception as exc:
            logger.error(
                "Gemini processing failed for feedback %s: %s",
                request.feedback_id,
                str(exc),
            )
            raise

    async def analyze_hotspots(
        self,
        country_code: str | None = None,
        category: str | None = None,
        min_urgency: float | None = None,
    ) -> tuple[list[HotspotCluster], int]:
        """Analyze stored feedback to identify geographic hotspots.

        Clusters feedback by geographic proximity and category, computing
        aggregate urgency and sentiment for each cluster. Applies optional
        filters before analysis.

        Args:
            country_code: Optional BRICS country filter.
            category: Optional infrastructure category filter.
            min_urgency: Optional minimum urgency threshold.

        Returns:
            Tuple of (hotspot_clusters, total_feedback_analyzed).
        """
        # Apply filters
        if self.use_supabase:
            try:
                resp = self.supabase.table("citizen_feedback").select("*").execute()
                filtered = []
                for f in resp.data:
                    f["location_coords"] = {"lat": f["lat"], "lng": f["lng"]}
                    filtered.append(f)
            except Exception as e:
                logger.error(f"Supabase query failed in analyze_hotspots: {e}")
                # Raise an exception that FastAPI will handle gracefully with CORS
                raise RuntimeError(f"Database access error: {e}")
        else:
            filtered = self.feedback_store.copy()

        if country_code:
            filtered = [
                f for f in filtered
                if f.get("country_code", "").upper() == country_code.upper()
            ]
        if category:
            filtered = [
                f for f in filtered
                if f.get("category") == category
            ]
        if min_urgency is not None:
            filtered = [
                f for f in filtered
                if f.get("urgency_score", 0) >= min_urgency
            ]

        total_analyzed = len(filtered)

        if not filtered:
            return [], total_analyzed

        # Cluster by (country_code, region_name, category)
        clusters: dict[str, list[dict]] = {}
        for fb in filtered:
            key = (
                f"{fb.get('country_code', 'XX')}"
                f"_{fb.get('region_name', 'Unknown')}"
                f"_{fb.get('category', 'other')}"
            )
            clusters.setdefault(key, []).append(fb)

        hotspots: list[HotspotCluster] = []
        for idx, (key, feedbacks) in enumerate(clusters.items()):
            avg_urgency = sum(
                f.get("urgency_score", 0) for f in feedbacks
            ) / len(feedbacks)
            avg_sentiment = sum(
                f.get("sentiment_score", 0) for f in feedbacks
            ) / len(feedbacks)

            # Compute center coordinates
            avg_lat = sum(
                f["location_coords"]["lat"] for f in feedbacks
            ) / len(feedbacks)
            avg_lng = sum(
                f["location_coords"]["lng"] for f in feedbacks
            ) / len(feedbacks)

            # Determine intensity from average urgency
            if avg_urgency >= 8.0:
                intensity = HotspotIntensity.CRITICAL
            elif avg_urgency >= 6.0:
                intensity = HotspotIntensity.HIGH
            elif avg_urgency >= 4.0:
                intensity = HotspotIntensity.MEDIUM
            else:
                intensity = HotspotIntensity.LOW

            cc = feedbacks[0].get("country_code", "IN")
            region = feedbacks[0].get("region_name", "Unknown")
            cat = feedbacks[0].get("category", "other")

            hotspots.append(
                HotspotCluster(
                    cluster_id=f"hs-{idx + 1:03d}",
                    center_coords=LocationCoords(lat=avg_lat, lng=avg_lng),
                    radius_km=round(len(feedbacks) * 2.5, 1),
                    country_code=BRICSCountry(cc) if cc in BRICSCountry._value2member_map_ else BRICSCountry.IN,
                    region_name=region,
                    dominant_category=InfrastructureCategory(cat) if cat in InfrastructureCategory._value2member_map_ else InfrastructureCategory.OTHER,
                    feedback_count=len(feedbacks),
                    avg_urgency_score=round(avg_urgency, 2),
                    avg_sentiment_score=round(avg_sentiment, 2),
                    intensity=intensity,
                )
            )

        # Sort by urgency descending
        hotspots.sort(key=lambda h: h.avg_urgency_score, reverse=True)

        return hotspots, total_analyzed

    async def generate_recommendations(
        self,
        hotspots: list[HotspotCluster] | None = None,
    ) -> list[ProjectRecommendation]:
        """Generate infrastructure project recommendations for citizen feedback.

        Ensures a 1-to-1 relationship between citizen feedback and project
        recommendations: exactly one project recommendation per citizen feedback.
        Prevents adding duplicate recommendations on site refresh.

        Args:
            hotspots: Optional list of identified hotspot clusters.

        Returns:
            List of generated project recommendations.
        """
        new_recommendations: list[ProjectRecommendation] = []

        # 1. Retrieve all existing recommendations to find which feedback IDs / clusters already have a recommendation
        existing_recs, _ = self.get_recommendations(page_size=1000)
        recommended_feedback_ids: set[str] = set()
        recommended_clusters: set[tuple[str, str, str]] = set()
        for r in existing_recs:
            if r.supporting_feedback_ids:
                recommended_feedback_ids.update(r.supporting_feedback_ids)
            recommended_clusters.add(
                (r.location.country_code.value, r.location.region_name, r.category.value)
            )

        # 2. Retrieve all citizen feedback records
        all_feedbacks: list[dict] = []
        if self.use_supabase:
            try:
                resp = self.supabase.table("citizen_feedback").select("*").execute()
                for f in (resp.data or []):
                    f["location_coords"] = {"lat": f.get("lat", 26.8467), "lng": f.get("lng", 80.9462)}
                    all_feedbacks.append(f)
            except Exception as e:
                logger.error(f"Supabase query failed in generate_recommendations: {e}")
        else:
            all_feedbacks = self.feedback_store.copy()

        # 3. Identify citizen feedbacks that do NOT have a recommendation yet
        unrecommended_feedbacks = []
        for fb in all_feedbacks:
            fid = fb.get("feedback_id")
            if not fid:
                continue
            if fid in recommended_feedback_ids:
                continue
            cc = str(fb.get("country_code") or "IN").upper()
            reg = str(fb.get("region_name") or "Unknown")
            cat = str(fb.get("category") or "other")
            if (cc, reg, cat) in recommended_clusters:
                continue
            unrecommended_feedbacks.append(fb)

        # If every citizen feedback already has a recommendation, do not generate duplicates on refresh!
        if not unrecommended_feedbacks:
            # If there are no raw feedbacks stored but synthetic actionable hotspots were passed with no existing recs
            if hotspots and not existing_recs:
                actionable = [
                    h for h in hotspots
                    if h.intensity in (HotspotIntensity.CRITICAL, HotspotIntensity.HIGH)
                ]
                for hotspot in actionable:
                    try:
                        rec = await self._generate_single_recommendation(hotspot)
                        new_recommendations.append(rec)
                    except Exception as exc:
                        logger.error("Failed to generate recommendation for %s: %s", hotspot.cluster_id, str(exc))
                if self.use_supabase:
                    for rec in new_recommendations:
                        self.supabase.table("project_recommendations").insert({
                            "recommendation_id": rec.recommendation_id,
                            "title": rec.title,
                            "category": rec.category.value,
                            "priority_score": rec.priority_score,
                            "priority_breakdown": rec.priority_breakdown.model_dump(),
                            "budget_usd": rec.budget_estimate.amount_usd,
                            "budget_local": rec.budget_estimate.amount_local,
                            "local_currency": rec.budget_estimate.local_currency_code,
                            "justification": rec.justification,
                            "country_code": rec.location.country_code.value,
                            "region_name": rec.location.region_name,
                            "lat": rec.location.center_coords.lat,
                            "lng": rec.location.center_coords.lng,
                            "supporting_feedback_count": rec.supporting_feedback_count,
                            "supporting_feedback_ids": rec.supporting_feedback_ids,
                            "status": rec.status.value,
                        }).execute()
                else:
                    self.recommendation_store.extend(new_recommendations)
                return new_recommendations

            logger.info("All citizen feedback records already have an aligned project recommendation. Skipping generation on refresh.")
            return []

        # 4. Generate exactly one project recommendation for each unrecommended citizen feedback
        for fb in unrecommended_feedbacks:
            try:
                rec = await self._generate_recommendation_for_feedback(fb)
                new_recommendations.append(rec)
                recommended_feedback_ids.add(fb.get("feedback_id"))
                recommended_clusters.add(
                    (rec.location.country_code.value, rec.location.region_name, rec.category.value)
                )
            except Exception as exc:
                logger.error(
                    "Failed to generate recommendation for feedback %s: %s",
                    fb.get("feedback_id"),
                    str(exc),
                )

        # 5. Persist the new recommendations
        if self.use_supabase:
            for rec in new_recommendations:
                try:
                    self.supabase.table("project_recommendations").insert({
                        "recommendation_id": rec.recommendation_id,
                        "title": rec.title,
                        "category": rec.category.value,
                        "priority_score": rec.priority_score,
                        "priority_breakdown": rec.priority_breakdown.model_dump(),
                        "budget_usd": rec.budget_estimate.amount_usd,
                        "budget_local": rec.budget_estimate.amount_local,
                        "local_currency": rec.budget_estimate.local_currency_code,
                        "justification": rec.justification,
                        "country_code": rec.location.country_code.value,
                        "region_name": rec.location.region_name,
                        "lat": rec.location.center_coords.lat,
                        "lng": rec.location.center_coords.lng,
                        "supporting_feedback_count": rec.supporting_feedback_count,
                        "supporting_feedback_ids": rec.supporting_feedback_ids,
                        "status": rec.status.value,
                    }).execute()
                except Exception as exc:
                    logger.error(f"Failed to insert recommendation into Supabase: {exc}")
        else:
            self.recommendation_store.extend(new_recommendations)

        return new_recommendations

    def get_recommendations(
        self,
        country_code: str | None = None,
        category: str | None = None,
        min_priority: float = 0.0,
        sort_by: str = "priority_score",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ProjectRecommendation], int]:
        """Retrieve stored recommendations with deduplication, filtering and pagination.

        Ensures each citizen feedback has at most one project recommendation.
        Removes any duplicate recommendations from previous runs.

        Args:
            country_code: Optional BRICS country filter.
            category: Optional infrastructure category filter.
            min_priority: Minimum priority score threshold (0–100).
            sort_by: Sort field (priority_score, budget_estimate, etc.).
            sort_order: Sort direction ("asc" or "desc").
            page: Page number (1-indexed).
            page_size: Items per page (1–100).

        Returns:
            Tuple of (paginated_recommendations, total_matching_count).
        """
        raw_recs: list[ProjectRecommendation] = []
        if self.use_supabase:
            query = self.supabase.table("project_recommendations").select("*")
            if country_code:
                query = query.eq("country_code", country_code.upper())
            if category:
                query = query.eq("category", category)
            query = query.gte("priority_score", min_priority)

            try:
                resp = query.execute()
            except Exception as e:
                logger.error(f"Supabase query failed in get_recommendations: {e}")
                raise RuntimeError(f"Database access error: {e}")

            for d in resp.data:
                try:
                    raw_sf_ids = d.get("supporting_feedback_ids")
                    if isinstance(raw_sf_ids, list):
                        parsed_sf_ids = [str(x) for x in raw_sf_ids]
                    elif isinstance(raw_sf_ids, str):
                        try:
                            decoded = json.loads(raw_sf_ids)
                            parsed_sf_ids = [str(x) for x in decoded] if isinstance(decoded, list) else [raw_sf_ids]
                        except Exception:
                            parsed_sf_ids = [raw_sf_ids] if raw_sf_ids else []
                    else:
                        parsed_sf_ids = []

                    created_at_val = datetime.now(timezone.utc)
                    if d.get("created_at"):
                        try:
                            created_at_val = datetime.fromisoformat(str(d["created_at"]).replace("Z", "+00:00"))
                        except Exception:
                            pass

                    rec = ProjectRecommendation(
                        recommendation_id=d["recommendation_id"],
                        title=d["title"],
                        category=InfrastructureCategory(d["category"]) if d["category"] in InfrastructureCategory._value2member_map_ else InfrastructureCategory.OTHER,
                        priority_score=d["priority_score"],
                        priority_breakdown=PriorityBreakdown.model_validate(
                            json.loads(d["priority_breakdown"]) if isinstance(d.get("priority_breakdown"), str) else (d.get("priority_breakdown") or {})
                        ),
                        budget_estimate=BudgetEstimate(
                            amount_usd=d["budget_usd"],
                            amount_local=d["budget_local"],
                            local_currency_code=d["local_currency"],
                            confidence=BudgetConfidence.MEDIUM,
                        ),
                        justification=d["justification"],
                        location=RecommendationLocation(
                            country_code=BRICSCountry(d["country_code"]) if d["country_code"] in BRICSCountry._value2member_map_ else BRICSCountry.IN,
                            region_name=d["region_name"],
                            center_coords=LocationCoords(lat=d["lat"], lng=d["lng"]),
                        ),
                        supporting_feedback_count=d.get("supporting_feedback_count", 1),
                        supporting_feedback_ids=parsed_sf_ids,
                        infrastructure_index_reference=InfrastructureIndexReference(index_name="Unknown", region_value=0.0, national_average=0.0, gap_percentage=0.0),
                        sdg_alignment=[],
                        status=RecommendationStatus(d["status"]) if d["status"] in RecommendationStatus._value2member_map_ else RecommendationStatus.PUBLISHED,
                        created_at=created_at_val,
                    )
                    raw_recs.append(rec)
                except Exception as e:
                    logger.error(f"Failed to parse recommendation from DB: {e}")
        else:
            raw_recs = self.recommendation_store.copy()

        # Deduplicate recommendations so each citizen feedback has exactly one recommendation
        seen_feedback_ids: set[str] = set()
        seen_keys: set[tuple] = set()
        unique_recs: list[ProjectRecommendation] = []
        duplicate_rec_ids: list[str] = []

        for r in raw_recs:
            is_dup = False
            # 1. Deduplicate by supporting feedback IDs
            if r.supporting_feedback_ids:
                for fid in r.supporting_feedback_ids:
                    if fid in seen_feedback_ids:
                        is_dup = True
                        break

            # 2. Also deduplicate by country + region + category (independent of varying AI titles)
            cluster_key = (r.location.country_code.value, r.location.region_name, r.category.value)
            if not is_dup and cluster_key in seen_keys:
                is_dup = True

            if is_dup:
                duplicate_rec_ids.append(r.recommendation_id)
            else:
                unique_recs.append(r)
                if r.supporting_feedback_ids:
                    seen_feedback_ids.update(r.supporting_feedback_ids)
                seen_keys.add(cluster_key)

        # Cleanup duplicate records in Supabase database or in-memory store
        if duplicate_rec_ids:
            if self.use_supabase:
                try:
                    self.supabase.table("project_recommendations").delete().in_("recommendation_id", duplicate_rec_ids).execute()
                    logger.info(f"Cleaned up {len(duplicate_rec_ids)} duplicate recommendations from Supabase database.")
                except Exception as e:
                    logger.warning(f"Failed to clean up duplicate recommendations from Supabase: {e}")
            else:
                self.recommendation_store = [r for r in self.recommendation_store if r.recommendation_id not in duplicate_rec_ids]

        filtered = unique_recs

        if country_code:
            filtered = [
                r for r in filtered
                if r.location.country_code.value == country_code.upper()
            ]
        if category:
            filtered = [
                r for r in filtered
                if r.category.value == category
            ]
        filtered = [
            r for r in filtered
            if r.priority_score >= min_priority
        ]

        # Sort
        reverse = sort_order == "desc"
        if sort_by == "priority_score":
            filtered.sort(key=lambda r: r.priority_score, reverse=reverse)
        elif sort_by == "budget_estimate":
            filtered.sort(
                key=lambda r: r.budget_estimate.amount_usd, reverse=reverse
            )
        elif sort_by == "feedback_count":
            filtered.sort(
                key=lambda r: r.supporting_feedback_count, reverse=reverse
            )
        elif sort_by == "created_at":
            filtered.sort(key=lambda r: r.created_at, reverse=reverse)

        total = len(filtered)

        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        paginated = filtered[start:end]

        return paginated, total

    # ======================================================================
    # Private Methods
    # ======================================================================

    def _build_nlp_prompt(self, request: InternalProcessRequest) -> str:
        """Build the Gemini prompt for multilingual NLP processing.

        Uses structured output prompting to get all NLP results in a
        single API call, minimizing latency and cost.

        Args:
            request: The feedback processing request.

        Returns:
            Formatted prompt string for Gemini.
        """
        return f"""You are an expert multilingual NLP analyst for the NagarikBRICS citizen feedback platform.
Analyze the following citizen feedback about public infrastructure.

FEEDBACK TEXT (language: {request.language}):
\"{request.raw_text}\"

LOCATION: lat={request.location_coords.lat}, lng={request.location_coords.lng}
COUNTRY: {request.country_code if request.country_code else "Infer from coordinates"}

Perform ALL of the following tasks and return ONLY a valid JSON object:

1. TRANSLATE: Translate the text to English. If already in English, return the original.
2. SENTIMENT: Classify sentiment as exactly one of: very_negative, negative, neutral, positive, very_positive
3. SENTIMENT SCORE: Assign a continuous score from -1.0 (extremely negative) to 1.0 (extremely positive)
4. CATEGORY: Classify the infrastructure category as exactly one of: water_sanitation, transportation, energy_power, healthcare, education, housing, digital_connectivity, waste_management, public_safety, other
5. URGENCY: Score urgency from 0.0 (informational) to 10.0 (life-threatening emergency)
6. KEYWORDS: Extract 3-7 key terms in English for search/clustering
7. REGION: Identify the state/province/district name based on the coordinates

Return ONLY this JSON (no markdown, no explanation):
{{
  "translated_text": "...",
  "sentiment": "...",
  "sentiment_score": 0.0,
  "category": "...",
  "urgency_score": 0.0,
  "keywords": ["...", "..."],
  "region_name": "..."
}}"""

    def _parse_nlp_response(
        self,
        response_text: str,
        request: InternalProcessRequest,
    ) -> InternalProcessResponse:
        """Parse and validate the Gemini NLP response.

        Extracts the JSON object from the response, handling cases where
        Gemini wraps the output in markdown code blocks. Applies fallback
        defaults for any missing or invalid fields.

        Args:
            response_text: Raw text response from Gemini.
            request: Original request for fallback values.

        Returns:
            Validated InternalProcessResponse.
        """
        # Strip markdown code blocks if present
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning(
                "Failed to parse Gemini response as JSON for %s, using defaults",
                request.feedback_id,
            )
            data = {}

        # Validate and constrain values
        sentiment_raw = data.get("sentiment", "neutral")
        if sentiment_raw not in SentimentLabel._value2member_map_:
            sentiment_raw = "neutral"

        category_raw = data.get("category", "other")
        if category_raw not in InfrastructureCategory._value2member_map_:
            category_raw = "other"

        sentiment_score = float(data.get("sentiment_score", 0.0))
        sentiment_score = max(-1.0, min(1.0, sentiment_score))

        urgency_score = float(data.get("urgency_score", 5.0))
        urgency_score = max(0.0, min(10.0, urgency_score))

        keywords = data.get("keywords", [])
        if not isinstance(keywords, list):
            keywords = []
        keywords = [str(k) for k in keywords[:10]]

        return InternalProcessResponse(
            feedback_id=request.feedback_id,
            translated_text=data.get("translated_text", request.raw_text),
            sentiment=SentimentLabel(sentiment_raw),
            sentiment_score=sentiment_score,
            category=InfrastructureCategory(category_raw),
            urgency_score=urgency_score,
            keywords=keywords,
            region_name=data.get("region_name", "Unknown"),
        )

    async def _generate_recommendation_for_feedback(
        self,
        feedback: dict,
    ) -> ProjectRecommendation:
        """Generate an infrastructure project recommendation for a single citizen feedback record.

        Ensures a 1-to-1 relationship between citizen feedback and project recommendations.

        Args:
            feedback: Stored citizen feedback dictionary.

        Returns:
            Fully populated ProjectRecommendation tied to this citizen feedback.
        """
        fb_id = str(feedback.get("feedback_id") or uuid.uuid4())
        country = feedback.get("country_code") or "IN"
        if country not in BRICSCountry._value2member_map_:
            country = "IN"
        region = feedback.get("region_name") or "Unknown"
        category = feedback.get("category") or "other"
        if category not in InfrastructureCategory._value2member_map_:
            category = "other"

        urgency_score = float(feedback.get("urgency_score", 5.0))
        sentiment_score = float(feedback.get("sentiment_score", 0.0))
        feedback_text = feedback.get("raw_text") or feedback.get("translated_text", "")

        lat = feedback.get("lat")
        lng = feedback.get("lng")
        if lat is None or lng is None:
            coords = feedback.get("location_coords") or {}
            lat = coords.get("lat", 26.8467)
            lng = coords.get("lng", 80.9462)

        # Look up infrastructure index
        index_name = CATEGORY_INDEX_MAP.get(category, "HDI")
        region_indices = INFRASTRUCTURE_INDICES.get(country, {}).get(region, {})
        national_avgs = NATIONAL_AVERAGES.get(country, {})

        region_value = region_indices.get(index_name, 50.0)
        national_avg = national_avgs.get(index_name, 60.0)
        gap_pct = round(
            ((national_avg - region_value) / national_avg) * 100, 2
        ) if national_avg > 0 else 0.0

        # Compute priority breakdown
        urgency_component = min(40.0, (urgency_score / 10.0) * 40.0)
        volume_component = 15.0  # Baseline weight for a validated citizen feedback
        gap_component = min(25.0, max(0.0, (gap_pct / 40.0) * 25.0))
        sentiment_component = min(10.0, abs(sentiment_score) * 10.0)
        total_priority = round(
            urgency_component + volume_component + gap_component + sentiment_component,
            1,
        )

        prompt = f"""You are a public policy advisor for BRICS nations.
Generate a project recommendation aligned with this citizen feedback request.

CITIZEN FEEDBACK:
- Country: {country}
- Region: {region}
- Category: {category.replace('_', ' ').title()}
- Citizen Report: "{feedback_text}"
- Urgency: {urgency_score}/10
- Sentiment: {sentiment_score} (-1 to +1)
- Infrastructure Index ({index_name}): Region={region_value}, National Avg={national_avg}, Gap={gap_pct}%

Return ONLY this JSON (no markdown, no explanation):
{{
  "title": "A concise project title addressing this citizen request (max 200 chars)",
  "justification": "A detailed 100-300 word justification addressing this citizen issue and referencing infrastructure indices",
  "budget_estimate_usd": 150000
}}"""

        try:
            response = self._generate_with_fallback(
                model=self.model,
                contents=prompt,
            )
            cleaned = response.text.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                cleaned = re.sub(r"\s*```$", "", cleaned)
            rec_data = json.loads(cleaned.strip())
        except Exception as e:
            logger.warning(f"Gemini fallback for feedback recommendation {fb_id}: {e}")
            rec_data = {
                "title": f"{category.replace('_', ' ').title()} Project — {region}",
                "justification": (
                    f"Direct response to citizen feedback ({feedback_text[:100]}...) from {region}, "
                    f"{country} with an urgency score of {urgency_score}/10. "
                    f"The region's {index_name} score of {region_value} indicates an infrastructure gap. "
                    f"Implementation is prioritized to resolve this citizen concern."
                ),
                "budget_estimate_usd": 120000,
            }

        budget_usd = max(0, float(rec_data.get("budget_estimate_usd", 120000)))
        currency = COUNTRY_CURRENCY.get(country, "USD")
        fx_rates = {"INR": 83.5, "BRL": 5.1, "ZAR": 18.5, "RUB": 92.0, "CNY": 7.2}
        local_amount = round(budget_usd * fx_rates.get(currency, 1.0))

        justification_text = rec_data.get("justification", "")
        if len(justification_text) < 50:
            justification_text = (
                f"Direct response to citizen feedback from {region}, {country} "
                f"with urgency {urgency_score}/10. Targeted infrastructure intervention to resolve "
                f"the reported issue and improve local community quality of life."
            )

        return ProjectRecommendation(
            recommendation_id=str(uuid.uuid4()),
            title=str(rec_data.get("title", f"{category.replace('_', ' ').title()} — {region}"))[:200],
            category=InfrastructureCategory(category) if category in InfrastructureCategory._value2member_map_ else InfrastructureCategory.OTHER,
            priority_score=total_priority,
            priority_breakdown=PriorityBreakdown(
                citizen_urgency_component=round(urgency_component, 1),
                feedback_volume_component=round(volume_component, 1),
                infrastructure_gap_component=round(gap_component, 1),
                sentiment_severity_component=round(sentiment_component, 1),
            ),
            budget_estimate=BudgetEstimate(
                amount_usd=budget_usd,
                amount_local=local_amount,
                local_currency_code=currency,
                confidence=BudgetConfidence.MEDIUM,
            ),
            justification=justification_text,
            location=RecommendationLocation(
                country_code=BRICSCountry(country),
                region_name=region,
                center_coords=LocationCoords(lat=lat, lng=lng),
            ),
            supporting_feedback_count=1,
            supporting_feedback_ids=[fb_id],
            infrastructure_index_reference=InfrastructureIndexReference(
                index_name=index_name,
                region_value=region_value,
                national_average=national_avg,
                gap_percentage=gap_pct,
            ),
            sdg_alignment=CATEGORY_SDG_MAP.get(category, []),
            status=RecommendationStatus.PUBLISHED,
            created_at=datetime.now(timezone.utc),
        )

    async def _generate_single_recommendation(
        self,
        hotspot: HotspotCluster,
    ) -> ProjectRecommendation:
        """Generate a single project recommendation for a hotspot.

        Cross-references the hotspot with infrastructure indices to compute
        a priority score breakdown, then uses Gemini to generate the
        project title, justification, and budget estimate.

        Args:
            hotspot: The hotspot cluster to generate a recommendation for.

        Returns:
            A fully populated ProjectRecommendation.
        """
        country = hotspot.country_code.value
        region = hotspot.region_name
        category = hotspot.dominant_category.value

        # Look up infrastructure index
        index_name = CATEGORY_INDEX_MAP.get(category, "HDI")
        region_indices = INFRASTRUCTURE_INDICES.get(country, {}).get(region, {})
        national_avgs = NATIONAL_AVERAGES.get(country, {})

        region_value = region_indices.get(index_name, 50.0)
        national_avg = national_avgs.get(index_name, 60.0)
        gap_pct = round(
            ((national_avg - region_value) / national_avg) * 100, 2
        ) if national_avg > 0 else 0.0

        # Compute priority breakdown
        urgency_component = min(40.0, (hotspot.avg_urgency_score / 10.0) * 40.0)
        volume_component = min(25.0, (hotspot.feedback_count / 50.0) * 25.0)
        gap_component = min(25.0, max(0.0, (gap_pct / 40.0) * 25.0))
        sentiment_component = min(
            10.0, (abs(hotspot.avg_sentiment_score) * 10.0)
        )
        total_priority = round(
            urgency_component + volume_component + gap_component + sentiment_component,
            1,
        )

        # Gather supporting feedback IDs
        if self.use_supabase:
            resp = self.supabase.table("citizen_feedback").select("feedback_id").eq("region_name", region).eq("category", category).execute()
            supporting_ids = [f["feedback_id"] for f in resp.data]
        else:
            supporting_ids = [
                f["feedback_id"]
                for f in self.feedback_store
                if (
                    f.get("region_name") == region
                    and f.get("category") == category
                )
            ]

        # Generate title and justification via Gemini
        prompt = f"""You are a public policy advisor for BRICS nations.
Generate a project recommendation for the following infrastructure hotspot.

HOTSPOT DETAILS:
- Country: {country}
- Region: {region}
- Category: {category.replace('_', ' ').title()}
- Feedback Count: {hotspot.feedback_count}
- Average Urgency: {hotspot.avg_urgency_score}/10
- Average Sentiment: {hotspot.avg_sentiment_score} (-1 to +1)
- Infrastructure Index ({index_name}): Region={region_value}, National Avg={national_avg}, Gap={gap_pct}%

Return ONLY this JSON (no markdown, no explanation):
{{
  "title": "A concise project title (max 200 chars)",
  "justification": "A detailed 100-300 word justification referencing citizen feedback themes and infrastructure index data",
  "budget_estimate_usd": 0
}}"""

        response = self._generate_with_fallback(
            model=self.model,
            contents=prompt,
        )

        # Parse Gemini response
        cleaned = response.text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            rec_data = json.loads(cleaned.strip())
        except json.JSONDecodeError:
            rec_data = {
                "title": f"{category.replace('_', ' ').title()} Improvement — {region}",
                "justification": (
                    f"Based on {hotspot.feedback_count} citizen reports from {region}, "
                    f"{country} with an average urgency of {hotspot.avg_urgency_score}/10. "
                    f"The region's {index_name} score of {region_value} is {gap_pct}% below "
                    f"the national average of {national_avg}. Immediate intervention is recommended "
                    f"to address the infrastructure gap and improve citizen well-being."
                ),
                "budget_estimate_usd": 150000,
            }

        budget_usd = max(0, float(rec_data.get("budget_estimate_usd", 150000)))
        currency = COUNTRY_CURRENCY.get(country, "USD")

        # Rough USD to local currency conversion (MVP approximation)
        fx_rates = {"INR": 83.5, "BRL": 5.1, "ZAR": 18.5, "RUB": 92.0, "CNY": 7.2}
        local_amount = round(budget_usd * fx_rates.get(currency, 1.0))

        justification_text = rec_data.get("justification", "")
        if len(justification_text) < 50:
            justification_text = (
                f"Based on {hotspot.feedback_count} citizen reports from {region}, "
                f"{country} with an average urgency of {hotspot.avg_urgency_score}/10 "
                f"and sentiment of {hotspot.avg_sentiment_score}. The region's {index_name} "
                f"score of {region_value} is {gap_pct}% below the national average of "
                f"{national_avg}. Immediate intervention is recommended to address the "
                f"infrastructure gap and improve citizen quality of life."
            )

        return ProjectRecommendation(
            recommendation_id=str(uuid.uuid4()),
            title=str(rec_data.get("title", f"{category.replace('_', ' ').title()} — {region}"))[:200],
            category=InfrastructureCategory(category) if category in InfrastructureCategory._value2member_map_ else InfrastructureCategory.OTHER,
            priority_score=total_priority,
            priority_breakdown=PriorityBreakdown(
                citizen_urgency_component=round(urgency_component, 1),
                feedback_volume_component=round(volume_component, 1),
                infrastructure_gap_component=round(gap_component, 1),
                sentiment_severity_component=round(sentiment_component, 1),
            ),
            budget_estimate=BudgetEstimate(
                amount_usd=budget_usd,
                amount_local=local_amount,
                local_currency_code=currency,
                confidence=BudgetConfidence.MEDIUM,
            ),
            justification=justification_text,
            location=RecommendationLocation(
                country_code=hotspot.country_code,
                region_name=region,
                center_coords=hotspot.center_coords,
            ),
            supporting_feedback_count=hotspot.feedback_count,
            supporting_feedback_ids=supporting_ids[:20],
            infrastructure_index_reference=InfrastructureIndexReference(
                index_name=index_name,
                region_value=region_value,
                national_average=national_avg,
                gap_percentage=gap_pct,
            ),
            sdg_alignment=CATEGORY_SDG_MAP.get(category, []),
            status=RecommendationStatus.PUBLISHED,
            created_at=datetime.now(timezone.utc),
        )

    async def chat(self, prompt: str, language: str) -> str:
        """Handle AI chat widget requests."""
        logger.info(f"Processing chat prompt in {language}")
        try:
            sys_prompt = f"You are a helpful civic AI assistant for the NagarikBRICS platform. Reply in {language}."
            response = self._generate_with_fallback(
                model=self.model,
                contents=f"{sys_prompt}\n\nUser: {prompt}",
            )
            return response.text
        except Exception as exc:
            logger.error(f"Chat failed: {exc}")
            raise
