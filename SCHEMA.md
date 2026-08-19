# NagarikBRICS — Data Schema Specification

> Strict JSON schemas for all core data structures in the MVP.
> All services (Java Ingestion, Python AI Core, JS Frontend) MUST conform to these contracts.

---

## 1. `CitizenFeedback` — Input Schema

This is the payload accepted by the **Java Ingestion API** and stored as the canonical feedback record.

### 1.1 Request Payload (from citizen / data partner)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://nagarikbrics.org/schemas/citizen-feedback-request.json",
  "title": "CitizenFeedbackRequest",
  "description": "Raw citizen feedback submitted via API or web form.",
  "type": "object",
  "required": ["raw_text", "language", "location_coords"],
  "properties": {
    "raw_text": {
      "type": "string",
      "minLength": 10,
      "maxLength": 5000,
      "description": "The citizen's feedback in their native language. Minimum 10 characters to ensure meaningful input."
    },
    "language": {
      "type": "string",
      "description": "ISO 639-1 language code of the feedback text.",
      "enum": ["hi", "pt", "en", "ru", "zh", "zu", "af", "ta", "bn", "mr", "te", "ur", "kn", "gu", "ml"],
      "examples": ["hi", "pt", "en"]
    },
    "location_coords": {
      "type": "object",
      "required": ["lat", "lng"],
      "properties": {
        "lat": {
          "type": "number",
          "minimum": -90,
          "maximum": 90,
          "description": "Latitude in decimal degrees (WGS 84)."
        },
        "lng": {
          "type": "number",
          "minimum": -180,
          "maximum": 180,
          "description": "Longitude in decimal degrees (WGS 84)."
        }
      },
      "description": "GPS coordinates of the infrastructure issue location."
    },
    "country_code": {
      "type": "string",
      "enum": ["BR", "RU", "IN", "CN", "ZA"],
      "description": "ISO 3166-1 alpha-2 country code. Auto-inferred from coordinates if omitted."
    },
    "source_channel": {
      "type": "string",
      "enum": ["api", "web_form", "sms", "whatsapp", "partner_import"],
      "default": "api",
      "description": "Channel through which the feedback was submitted."
    },
    "submitter_id": {
      "type": ["string", "null"],
      "description": "Optional anonymous identifier for the submitter. No PII."
    }
  },
  "additionalProperties": false
}
```

### 1.2 Stored Record (after ingestion + AI processing)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://nagarikbrics.org/schemas/citizen-feedback-record.json",
  "title": "CitizenFeedbackRecord",
  "description": "Fully processed citizen feedback record with AI-extracted fields.",
  "type": "object",
  "required": [
    "feedback_id",
    "raw_text",
    "language",
    "location_coords",
    "sentiment",
    "category",
    "urgency_score",
    "translated_text",
    "created_at",
    "processed_at",
    "status"
  ],
  "properties": {
    "feedback_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier for this feedback record (UUID v4)."
    },
    "raw_text": {
      "type": "string",
      "description": "Original citizen feedback text, unmodified."
    },
    "language": {
      "type": "string",
      "description": "ISO 639-1 language code of the original text."
    },
    "translated_text": {
      "type": "string",
      "description": "English translation of raw_text (produced by Gemini). Identical to raw_text if language is 'en'."
    },
    "location_coords": {
      "type": "object",
      "required": ["lat", "lng"],
      "properties": {
        "lat": { "type": "number" },
        "lng": { "type": "number" }
      }
    },
    "country_code": {
      "type": "string",
      "enum": ["BR", "RU", "IN", "CN", "ZA"]
    },
    "region_name": {
      "type": "string",
      "description": "Human-readable region/state/province name, reverse-geocoded from coordinates."
    },
    "sentiment": {
      "type": "string",
      "enum": ["very_negative", "negative", "neutral", "positive", "very_positive"],
      "description": "Sentiment of the feedback as classified by Gemini."
    },
    "sentiment_score": {
      "type": "number",
      "minimum": -1.0,
      "maximum": 1.0,
      "description": "Continuous sentiment score. -1.0 = extremely negative, +1.0 = extremely positive."
    },
    "category": {
      "type": "string",
      "enum": [
        "water_sanitation",
        "transportation",
        "energy_power",
        "healthcare",
        "education",
        "housing",
        "digital_connectivity",
        "waste_management",
        "public_safety",
        "other"
      ],
      "description": "Infrastructure category classified by Gemini."
    },
    "urgency_score": {
      "type": "number",
      "minimum": 0,
      "maximum": 10,
      "description": "AI-assessed urgency. 0 = informational, 10 = life-threatening emergency."
    },
    "keywords": {
      "type": "array",
      "items": { "type": "string" },
      "maxItems": 10,
      "description": "Key terms extracted by Gemini for search and clustering."
    },
    "source_channel": {
      "type": "string",
      "enum": ["api", "web_form", "sms", "whatsapp", "partner_import"]
    },
    "submitter_id": {
      "type": ["string", "null"]
    },
    "status": {
      "type": "string",
      "enum": ["received", "processing", "processed", "failed"],
      "description": "Processing pipeline status."
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of when the feedback was received."
    },
    "processed_at": {
      "type": ["string", "null"],
      "format": "date-time",
      "description": "ISO 8601 timestamp of when AI processing completed. Null if not yet processed."
    }
  },
  "additionalProperties": false
}
```

### 1.3 Example Record

```json
{
  "feedback_id": "a3f1e8b2-7c4d-4e9a-b6f5-2d1c8a9e3b7f",
  "raw_text": "हमारे गाँव में पिछले दो महीने से पानी नहीं आ रहा है। बच्चे बीमार हो रहे हैं।",
  "language": "hi",
  "translated_text": "Water has not been coming to our village for the last two months. Children are getting sick.",
  "location_coords": { "lat": 26.8467, "lng": 80.9462 },
  "country_code": "IN",
  "region_name": "Uttar Pradesh",
  "sentiment": "very_negative",
  "sentiment_score": -0.92,
  "category": "water_sanitation",
  "urgency_score": 9.2,
  "keywords": ["water", "village", "children", "sick", "two months"],
  "source_channel": "web_form",
  "submitter_id": null,
  "status": "processed",
  "created_at": "2026-08-19T14:30:00Z",
  "processed_at": "2026-08-19T14:30:04Z"
}
```

---

## 2. `InfrastructureProjectRecommendation` — Output Schema

Generated by the **Python AI Core** (Gemini + correlation engine) and consumed by the **Frontend Dashboard**.

### 2.1 Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://nagarikbrics.org/schemas/infrastructure-project-recommendation.json",
  "title": "InfrastructureProjectRecommendation",
  "description": "AI-generated infrastructure project recommendation for policymakers.",
  "type": "object",
  "required": [
    "recommendation_id",
    "title",
    "category",
    "priority_score",
    "budget_estimate",
    "justification",
    "location",
    "supporting_feedback_count",
    "created_at"
  ],
  "properties": {
    "recommendation_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier for this recommendation (UUID v4)."
    },
    "title": {
      "type": "string",
      "maxLength": 200,
      "description": "Concise, human-readable project title. E.g., 'Emergency Water Pipeline Restoration — Lucknow Rural District'."
    },
    "category": {
      "type": "string",
      "enum": [
        "water_sanitation",
        "transportation",
        "energy_power",
        "healthcare",
        "education",
        "housing",
        "digital_connectivity",
        "waste_management",
        "public_safety"
      ],
      "description": "Infrastructure category this project addresses."
    },
    "priority_score": {
      "type": "number",
      "minimum": 0,
      "maximum": 100,
      "description": "Composite priority score (0–100). Computed from: citizen urgency (40%), feedback volume (25%), infrastructure index gap (25%), sentiment severity (10%)."
    },
    "priority_breakdown": {
      "type": "object",
      "description": "Transparent breakdown of how the priority_score was computed.",
      "properties": {
        "citizen_urgency_component": {
          "type": "number",
          "minimum": 0,
          "maximum": 40,
          "description": "Weighted average urgency from citizen feedback (max 40 points)."
        },
        "feedback_volume_component": {
          "type": "number",
          "minimum": 0,
          "maximum": 25,
          "description": "Normalized feedback count for this category + region (max 25 points)."
        },
        "infrastructure_gap_component": {
          "type": "number",
          "minimum": 0,
          "maximum": 25,
          "description": "Gap between region's infrastructure index and national average (max 25 points)."
        },
        "sentiment_severity_component": {
          "type": "number",
          "minimum": 0,
          "maximum": 10,
          "description": "Severity derived from aggregate negative sentiment (max 10 points)."
        }
      }
    },
    "budget_estimate": {
      "type": "object",
      "required": ["amount_usd", "confidence"],
      "properties": {
        "amount_usd": {
          "type": "number",
          "minimum": 0,
          "description": "Estimated project cost in USD."
        },
        "amount_local": {
          "type": ["number", "null"],
          "description": "Estimated cost in local currency (INR, BRL, ZAR, RUB, CNY)."
        },
        "local_currency_code": {
          "type": ["string", "null"],
          "enum": ["INR", "BRL", "ZAR", "RUB", "CNY", null],
          "description": "ISO 4217 currency code for the local amount."
        },
        "confidence": {
          "type": "string",
          "enum": ["low", "medium", "high"],
          "description": "AI confidence in the budget estimate. 'low' = order-of-magnitude guess, 'high' = based on comparable completed projects."
        }
      },
      "description": "AI-generated budget estimate with confidence level."
    },
    "justification": {
      "type": "string",
      "minLength": 50,
      "maxLength": 2000,
      "description": "Plain-language justification for this recommendation, generated by Gemini. Must reference citizen feedback themes and infrastructure index data."
    },
    "location": {
      "type": "object",
      "required": ["country_code", "region_name", "center_coords"],
      "properties": {
        "country_code": {
          "type": "string",
          "enum": ["BR", "RU", "IN", "CN", "ZA"]
        },
        "region_name": {
          "type": "string",
          "description": "State/province/district name."
        },
        "center_coords": {
          "type": "object",
          "required": ["lat", "lng"],
          "properties": {
            "lat": { "type": "number" },
            "lng": { "type": "number" }
          },
          "description": "Geographic center of the feedback cluster."
        }
      }
    },
    "supporting_feedback_count": {
      "type": "integer",
      "minimum": 1,
      "description": "Number of citizen feedback records that contributed to this recommendation."
    },
    "supporting_feedback_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "description": "UUIDs of the citizen feedback records that informed this recommendation. Enables drill-down from dashboard."
    },
    "infrastructure_index_reference": {
      "type": "object",
      "description": "Infrastructure index data point used in the correlation analysis.",
      "properties": {
        "index_name": {
          "type": "string",
          "description": "Name of the index used (e.g., 'HDI', 'SDG 6.1 - Safe Water Access', 'National Infrastructure Score')."
        },
        "region_value": {
          "type": "number",
          "description": "The region's current value for this index."
        },
        "national_average": {
          "type": "number",
          "description": "The national average for comparison."
        },
        "gap_percentage": {
          "type": "number",
          "description": "Percentage below national average. Positive = below average (needs attention)."
        }
      }
    },
    "sdg_alignment": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": "^SDG \\d{1,2}",
        "description": "UN Sustainable Development Goal alignment."
      },
      "description": "List of SDGs this project contributes to.",
      "examples": [["SDG 6 - Clean Water and Sanitation", "SDG 3 - Good Health and Well-Being"]]
    },
    "status": {
      "type": "string",
      "enum": ["draft", "published", "accepted", "rejected", "implemented"],
      "default": "draft",
      "description": "Lifecycle status of the recommendation."
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of when the recommendation was generated."
    }
  },
  "additionalProperties": false
}
```

### 2.2 Example Record

```json
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
  "justification": "Over the past 60 days, 47 citizen reports from Lucknow Rural District have flagged a complete water supply failure. Average urgency score is 9.2/10, with 89% expressing very negative sentiment. The region's SDG 6.1 (Safe Water Access) index is 42.3, which is 31% below the national average of 61.2. Cross-referencing with historical infrastructure data shows the main pipeline in this district was last maintained in 2019. Immediate restoration is recommended to prevent a public health crisis, particularly among children under 5 who account for 23% of the district population.",
  "location": {
    "country_code": "IN",
    "region_name": "Uttar Pradesh, Lucknow Rural",
    "center_coords": { "lat": 26.8467, "lng": 80.9462 }
  },
  "supporting_feedback_count": 47,
  "supporting_feedback_ids": [
    "a3f1e8b2-7c4d-4e9a-b6f5-2d1c8a9e3b7f",
    "b4f2e9c3-8d5e-4f0b-c7g6-3e2d9b0f4c8g"
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
```

---

## 3. `InfrastructureIndex` — Reference Data Schema

Seeded reference data representing regional infrastructure scores used by the correlator.

### 3.1 Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://nagarikbrics.org/schemas/infrastructure-index.json",
  "title": "InfrastructureIndex",
  "description": "Regional infrastructure index data point used for gap analysis.",
  "type": "object",
  "required": ["index_id", "country_code", "region_name", "index_name", "value", "year"],
  "properties": {
    "index_id": {
      "type": "string",
      "format": "uuid"
    },
    "country_code": {
      "type": "string",
      "enum": ["BR", "RU", "IN", "CN", "ZA"]
    },
    "region_name": {
      "type": "string",
      "description": "State/province/district name."
    },
    "index_name": {
      "type": "string",
      "enum": [
        "HDI",
        "SDG 6.1 - Safe Water Access",
        "SDG 7.1 - Electricity Access",
        "SDG 9.1 - Infrastructure Quality",
        "SDG 11.1 - Adequate Housing",
        "SDG 3.8 - Healthcare Coverage",
        "SDG 4.1 - Education Quality",
        "Digital Connectivity Index",
        "Road Quality Index",
        "Waste Management Index"
      ],
      "description": "Name of the infrastructure/development index."
    },
    "value": {
      "type": "number",
      "minimum": 0,
      "maximum": 100,
      "description": "Normalized index value (0–100 scale)."
    },
    "national_average": {
      "type": "number",
      "minimum": 0,
      "maximum": 100,
      "description": "National average for this index."
    },
    "year": {
      "type": "integer",
      "minimum": 2020,
      "maximum": 2030,
      "description": "Year of the data point."
    },
    "source": {
      "type": "string",
      "description": "Data source (e.g., 'UNDP HDR 2025', 'World Bank WDI', 'National Statistics Bureau')."
    }
  },
  "additionalProperties": false
}
```

---

## 4. API Response Envelopes

All API responses from both Java and Python services MUST use this standard envelope.

### 4.1 Success Envelope

```json
{
  "status": "success",
  "data": { },
  "meta": {
    "request_id": "uuid-v4",
    "timestamp": "2026-08-19T14:30:00Z",
    "processing_time_ms": 142
  }
}
```

### 4.2 Error Envelope

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Human-readable error description.",
    "details": [
      {
        "field": "raw_text",
        "issue": "Must be at least 10 characters."
      }
    ]
  },
  "meta": {
    "request_id": "uuid-v4",
    "timestamp": "2026-08-19T14:30:00Z"
  }
}
```

### 4.3 Standard Error Codes

| Code | HTTP Status | Meaning |
|---|---|---|
| `VALIDATION_FAILED` | 400 | Request payload failed schema validation |
| `UNSUPPORTED_LANGUAGE` | 400 | Language code not in supported set |
| `COORDS_OUT_OF_RANGE` | 400 | Coordinates outside BRICS nation boundaries |
| `PROCESSING_FAILED` | 500 | Gemini API or internal processing error |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests from this source |
| `NOT_FOUND` | 404 | Resource not found |

---

## 5. Schema Versioning

All schemas follow [Semantic Versioning](https://semver.org/):

- **Current Version**: `1.0.0-mvp`
- Breaking changes increment the MAJOR version
- New optional fields increment the MINOR version
- Bug fixes increment the PATCH version

Schema version is tracked in the `$id` URL and in the API response `meta` object.

---

*These schemas are the contracts between all NagarikBRICS services. Any deviation must be discussed and versioned.*
