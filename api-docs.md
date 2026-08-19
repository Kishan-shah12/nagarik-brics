# NagarikBRICS — API Contract Specification

> **Version**: `1.0.0-mvp`
> **Base URLs**:
> - Java Ingestion: `http://localhost:8081`
> - Python AI Core: `http://localhost:8080`

> **Convention**: All endpoints are prefixed with `/api/v1`. All request/response bodies are `application/json`. All timestamps are ISO 8601 UTC. All IDs are UUID v4.

---

## Table of Contents

1. [Java Ingestion Service](#1-java-ingestion-service-port-8081)
   - [POST /api/v1/feedback/submit](#11-post-apiv1feedbacksubmit)
2. [Python AI Core Service](#2-python-ai-core-service-port-8080)
   - [POST /api/v1/ai/analyze-hotspots](#21-post-apiv1aianalyze-hotspots)
   - [GET /api/v1/ai/recommendations](#22-get-apiv1airecommendations)
3. [Health Check Endpoints](#3-health-check-endpoints)
4. [Error Reference](#4-error-reference)
5. [Inter-Service Communication](#5-inter-service-communication)

---

## 1. Java Ingestion Service (Port 8081)

### 1.1 POST `/api/v1/feedback/submit`

**Purpose**: Accept and validate citizen feedback, forward to AI Core for NLP processing, and return the enriched record.

**Auth**: None (MVP — demo mode)

#### Request

**Headers**:

| Header | Required | Value |
|---|---|---|
| `Content-Type` | ✅ | `application/json` |
| `X-Request-Id` | ❌ | UUID v4 — auto-generated if omitted |
| `Accept-Language` | ❌ | Preferred response language (default: `en`) |

**Body** — `CitizenFeedbackRequest`:

```json
{
  "raw_text": "हमारे गाँव में पिछले दो महीने से पानी नहीं आ रहा है।",
  "language": "hi",
  "location_coords": {
    "lat": 26.8467,
    "lng": 80.9462
  },
  "country_code": "IN",
  "source_channel": "web_form",
  "submitter_id": null
}
```

| Field | Type | Required | Constraints |
|---|---|---|---|
| `raw_text` | string | ✅ | 10–5000 characters |
| `language` | string | ✅ | ISO 639-1. Supported: `hi`, `pt`, `en`, `ru`, `zh`, `zu`, `af`, `ta`, `bn`, `mr`, `te`, `ur`, `kn`, `gu`, `ml` |
| `location_coords` | object | ✅ | `lat`: [-90, 90], `lng`: [-180, 180] |
| `location_coords.lat` | number | ✅ | Decimal degrees (WGS 84) |
| `location_coords.lng` | number | ✅ | Decimal degrees (WGS 84) |
| `country_code` | string | ❌ | ISO 3166-1 alpha-2. One of: `BR`, `RU`, `IN`, `CN`, `ZA`. Auto-inferred from coords if omitted |
| `source_channel` | string | ❌ | Default: `api`. One of: `api`, `web_form`, `sms`, `whatsapp`, `partner_import` |
| `submitter_id` | string \| null | ❌ | Anonymous identifier. No PII |

#### Response — `201 Created`

```json
{
  "status": "success",
  "data": {
    "feedback_id": "a3f1e8b2-7c4d-4e9a-b6f5-2d1c8a9e3b7f",
    "raw_text": "हमारे गाँव में पिछले दो महीने से पानी नहीं आ रहा है।",
    "language": "hi",
    "translated_text": "Water has not been coming to our village for the last two months.",
    "location_coords": { "lat": 26.8467, "lng": 80.9462 },
    "country_code": "IN",
    "region_name": "Uttar Pradesh",
    "sentiment": "very_negative",
    "sentiment_score": -0.92,
    "category": "water_sanitation",
    "urgency_score": 9.2,
    "keywords": ["water", "village", "two months"],
    "source_channel": "web_form",
    "submitter_id": null,
    "status": "processed",
    "created_at": "2026-08-19T14:30:00Z",
    "processed_at": "2026-08-19T14:30:04Z"
  },
  "meta": {
    "request_id": "c1d2e3f4-5a6b-7c8d-9e0f-1a2b3c4d5e6f",
    "timestamp": "2026-08-19T14:30:04Z",
    "processing_time_ms": 4012
  }
}
```

#### Error Responses

| Status | Code | When |
|---|---|---|
| `400` | `VALIDATION_FAILED` | Missing/invalid required fields |
| `400` | `UNSUPPORTED_LANGUAGE` | Language code not in supported set |
| `400` | `COORDS_OUT_OF_RANGE` | Coordinates outside valid range |
| `500` | `PROCESSING_FAILED` | AI Core unreachable or Gemini error |
| `429` | `RATE_LIMIT_EXCEEDED` | > 100 requests/minute from same source |

**Example — 400 Validation Error**:

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Request payload failed schema validation.",
    "details": [
      { "field": "raw_text", "issue": "Must be at least 10 characters. Received 4." },
      { "field": "location_coords.lat", "issue": "Must be between -90 and 90. Received 200." }
    ]
  },
  "meta": {
    "request_id": "c1d2e3f4-5a6b-7c8d-9e0f-1a2b3c4d5e6f",
    "timestamp": "2026-08-19T14:30:00Z"
  }
}
```

#### Sequence Diagram

```
Client                Java Ingestion             Python AI Core
  │                        │                           │
  │── POST /feedback/submit ─▶│                        │
  │                        │── validate schema ──▶     │
  │                        │── generate UUID ──▶       │
  │                        │── POST /internal/process ─▶│
  │                        │                           │── Gemini: translate
  │                        │                           │── Gemini: classify
  │                        │                           │── Gemini: sentiment
  │                        │                           │── Gemini: urgency
  │                        │◀── ProcessedFeedback ─────│
  │                        │── store record ──▶        │
  │◀── 201 + record ──────│                           │
```

---

## 2. Python AI Core Service (Port 8080)

### 2.1 POST `/api/v1/ai/analyze-hotspots`

**Purpose**: Analyze all stored feedback to identify geographic and thematic hotspots. Triggers the correlation engine to cross-reference citizen signals with infrastructure indices and generate/update project recommendations.

**Auth**: None (MVP — demo mode)

**Invocation**: Called by the frontend dashboard when a policymaker clicks "Refresh Analysis", or periodically by a scheduled job.

#### Request

**Headers**:

| Header | Required | Value |
|---|---|---|
| `Content-Type` | ✅ | `application/json` |
| `X-Request-Id` | ❌ | UUID v4 — auto-generated if omitted |

**Body** — Analysis Filters (all optional):

```json
{
  "filters": {
    "country_code": "IN",
    "category": "water_sanitation",
    "date_range": {
      "from": "2026-07-01T00:00:00Z",
      "to": "2026-08-19T23:59:59Z"
    },
    "min_urgency_score": 5.0
  }
}
```

| Field | Type | Required | Constraints |
|---|---|---|---|
| `filters` | object | ❌ | Omit or pass `{}` for unfiltered analysis |
| `filters.country_code` | string | ❌ | ISO 3166-1 alpha-2. One of: `BR`, `RU`, `IN`, `CN`, `ZA` |
| `filters.category` | string | ❌ | One of the 10 supported categories |
| `filters.date_range` | object | ❌ | ISO 8601 `from` and `to` timestamps |
| `filters.min_urgency_score` | number | ❌ | 0–10. Only include feedback at or above this urgency |

#### Response — `200 OK`

```json
{
  "status": "success",
  "data": {
    "analysis_id": "f1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
    "hotspots": [
      {
        "cluster_id": "hs-001",
        "center_coords": { "lat": 26.8467, "lng": 80.9462 },
        "radius_km": 15.2,
        "country_code": "IN",
        "region_name": "Uttar Pradesh, Lucknow Rural",
        "dominant_category": "water_sanitation",
        "feedback_count": 47,
        "avg_urgency_score": 9.2,
        "avg_sentiment_score": -0.87,
        "intensity": "critical"
      },
      {
        "cluster_id": "hs-002",
        "center_coords": { "lat": -23.5505, "lng": -46.6333 },
        "radius_km": 8.7,
        "country_code": "BR",
        "region_name": "São Paulo, Zona Leste",
        "dominant_category": "transportation",
        "feedback_count": 31,
        "avg_urgency_score": 7.1,
        "avg_sentiment_score": -0.65,
        "intensity": "high"
      }
    ],
    "total_feedback_analyzed": 312,
    "recommendations_generated": 5
  },
  "meta": {
    "request_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "timestamp": "2026-08-19T15:00:00Z",
    "processing_time_ms": 8420
  }
}
```

| Response Field | Type | Description |
|---|---|---|
| `analysis_id` | UUID | Unique ID for this analysis run |
| `hotspots` | array | Clustered geographic hotspots, sorted by intensity |
| `hotspots[].cluster_id` | string | Stable identifier for this hotspot cluster |
| `hotspots[].center_coords` | object | Geographic center of the cluster |
| `hotspots[].radius_km` | number | Approximate radius of the cluster in kilometers |
| `hotspots[].dominant_category` | string | Most frequent infrastructure category in cluster |
| `hotspots[].feedback_count` | integer | Number of feedback records in cluster |
| `hotspots[].avg_urgency_score` | number | Average urgency (0–10) across cluster |
| `hotspots[].avg_sentiment_score` | number | Average sentiment (-1 to +1) across cluster |
| `hotspots[].intensity` | string | `critical` (≥8.0 urgency), `high` (≥6.0), `medium` (≥4.0), `low` (<4.0) |
| `total_feedback_analyzed` | integer | Total feedback records included in analysis |
| `recommendations_generated` | integer | Number of new recommendations created |

#### Error Responses

| Status | Code | When |
|---|---|---|
| `400` | `INVALID_FILTER` | Filter field contains an invalid value |
| `500` | `PROCESSING_FAILED` | Gemini API error or internal failure |

---

### 2.2 GET `/api/v1/ai/recommendations`

**Purpose**: Retrieve the current list of AI-generated infrastructure project recommendations, sorted by priority score descending.

**Auth**: None (MVP — demo mode)

#### Request

**Headers**:

| Header | Required | Value |
|---|---|---|
| `Accept` | ❌ | `application/json` (default) |
| `X-Request-Id` | ❌ | UUID v4 — auto-generated if omitted |

**Query Parameters**:

| Parameter | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `country_code` | string | ❌ | all | `BR`, `RU`, `IN`, `CN`, `ZA` |
| `category` | string | ❌ | all | One of the 9 infrastructure categories |
| `min_priority` | number | ❌ | 0 | 0–100 |
| `status` | string | ❌ | `published` | `draft`, `published`, `accepted`, `rejected` |
| `sort_by` | string | ❌ | `priority_score` | `priority_score`, `budget_estimate`, `feedback_count`, `created_at` |
| `sort_order` | string | ❌ | `desc` | `asc`, `desc` |
| `page` | integer | ❌ | 1 | ≥ 1 |
| `page_size` | integer | ❌ | 20 | 1–100 |

**Example Request**:

```
GET /api/v1/ai/recommendations?country_code=IN&category=water_sanitation&min_priority=50&page=1&page_size=10
```

#### Response — `200 OK`

```json
{
  "status": "success",
  "data": {
    "recommendations": [
      {
        "recommendation_id": "d7e2f1a9-3b5c-4d8e-a1f6-9c4b2e8d5a3f",
        "title": "Emergency Water Pipeline Restoration — Lucknow Rural District",
        "category": "water_sanitation",
        "priority_score": 87.5,
        "priority_breakdown": {
          "citizen_urgency_component": 36.8,
          "feedback_volume_component": 22.0,
          "infrastructure_gap_component": 21.5,
          "sentiment_severity_component": 7.2
        },
        "budget_estimate": {
          "amount_usd": 245000,
          "amount_local": 20500000,
          "local_currency_code": "INR",
          "confidence": "medium"
        },
        "justification": "Over the past 60 days, 47 citizen reports from Lucknow Rural District have flagged a complete water supply failure. Average urgency score is 9.2/10, with 89% expressing very negative sentiment. The region's SDG 6.1 index is 42.3, 31% below the national average of 61.2. Immediate restoration is recommended.",
        "location": {
          "country_code": "IN",
          "region_name": "Uttar Pradesh, Lucknow Rural",
          "center_coords": { "lat": 26.8467, "lng": 80.9462 }
        },
        "supporting_feedback_count": 47,
        "supporting_feedback_ids": [
          "a3f1e8b2-7c4d-4e9a-b6f5-2d1c8a9e3b7f"
        ],
        "infrastructure_index_reference": {
          "index_name": "SDG 6.1 - Safe Water Access",
          "region_value": 42.3,
          "national_average": 61.2,
          "gap_percentage": 30.88
        },
        "sdg_alignment": [
          "SDG 6 - Clean Water and Sanitation",
          "SDG 3 - Good Health and Well-Being"
        ],
        "status": "published",
        "created_at": "2026-08-19T15:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 10,
      "total_items": 1,
      "total_pages": 1
    }
  },
  "meta": {
    "request_id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
    "timestamp": "2026-08-19T15:05:00Z",
    "processing_time_ms": 45
  }
}
```

#### Error Responses

| Status | Code | When |
|---|---|---|
| `400` | `INVALID_FILTER` | Query parameter contains an invalid value |
| `404` | `NOT_FOUND` | No recommendations match the filters |

---

## 3. Health Check Endpoints

Both services expose health checks for Docker and monitoring.

### Java Ingestion — `GET /actuator/health`

```json
{
  "status": "UP",
  "components": {
    "aiCore": {
      "status": "UP",
      "details": { "url": "http://python-ai-core:8080" }
    },
    "diskSpace": {
      "status": "UP",
      "details": { "free": "4.2 GB" }
    }
  }
}
```

### Python AI Core — `GET /health`

```json
{
  "status": "healthy",
  "version": "1.0.0-mvp",
  "gemini_api": "connected",
  "feedback_count": 312,
  "recommendation_count": 5,
  "uptime_seconds": 86400
}
```

---

## 4. Error Reference

All errors across both services use the standard envelope defined in [SCHEMA.md](./SCHEMA.md#42-error-envelope).

### Complete Error Code Table

| Code | HTTP | Service | Description |
|---|---|---|---|
| `VALIDATION_FAILED` | 400 | Java | Request body failed JSON schema validation |
| `UNSUPPORTED_LANGUAGE` | 400 | Java | Language code not in supported set |
| `COORDS_OUT_OF_RANGE` | 400 | Java | Coordinates outside [-90,90] lat or [-180,180] lng |
| `INVALID_FILTER` | 400 | Python | Query parameter or filter body invalid |
| `NOT_FOUND` | 404 | Both | Requested resource does not exist |
| `RATE_LIMIT_EXCEEDED` | 429 | Java | > 100 req/min from same IP or submitter_id |
| `PROCESSING_FAILED` | 500 | Both | Internal error (Gemini API, DB, network) |
| `SERVICE_UNAVAILABLE` | 503 | Both | Service is starting up or shutting down |

---

## 5. Inter-Service Communication

The Java Ingestion service communicates with the Python AI Core via an **internal HTTP endpoint** that is NOT exposed to the public.

### Internal: POST `/internal/process`

**Called by**: Java Ingestion → Python AI Core (over Docker bridge network)
**NOT exposed** on public ports.

#### Request

```json
{
  "feedback_id": "a3f1e8b2-7c4d-4e9a-b6f5-2d1c8a9e3b7f",
  "raw_text": "हमारे गाँव में पिछले दो महीने से पानी नहीं आ रहा है।",
  "language": "hi",
  "location_coords": { "lat": 26.8467, "lng": 80.9462 },
  "country_code": "IN"
}
```

#### Response — `200 OK`

```json
{
  "feedback_id": "a3f1e8b2-7c4d-4e9a-b6f5-2d1c8a9e3b7f",
  "translated_text": "Water has not been coming to our village for the last two months.",
  "sentiment": "very_negative",
  "sentiment_score": -0.92,
  "category": "water_sanitation",
  "urgency_score": 9.2,
  "keywords": ["water", "village", "two months"],
  "region_name": "Uttar Pradesh"
}
```

### Network Diagram

```
                    Public Network                    Docker Bridge (nagarik-network)
                    ──────────────                    ──────────────────────────────────
                         │
  Browser (port 80) ─────┤
                         │
                         ├── :8081 ──▶ java-ingestion ──▶ (internal) ──▶ python-ai-core
                         │
                         ├── :8080 ──▶ python-ai-core
                         │
  Nginx proxies          │
  /api/v1/feedback/* ────┼──▶ java-ingestion:8081
  /api/v1/ai/*     ──────┼──▶ python-ai-core:8080
```

---

*All endpoints conform to the schemas defined in [SCHEMA.md](./SCHEMA.md). Any deviation is a contract violation and must be versioned.*
