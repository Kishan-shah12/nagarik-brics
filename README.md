# NagarikBRICS — Digital Public Good Infrastructure Intelligence Platform

![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![Java 21](https://img.shields.io/badge/Java-21-007396?style=flat&logo=openjdk&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688?style=flat&logo=fastapi&logoColor=white)
![Google GenAI SDK](https://img.shields.io/badge/Google_GenAI-Gemini_2.5_Flash-4285F4?style=flat&logo=google&logoColor=white)
![WCAG 2.1 AA](https://img.shields.io/badge/Accessibility-WCAG_2.1_AA-06D6A0?style=flat)
![Docker Multi-Stage](https://img.shields.io/badge/Docker-Multi--Stage_Build-2496ED?style=flat&logo=docker&logoColor=white)
![Repo Size](https://img.shields.io/badge/Repo_Size-<300_KB-success?style=flat)

## Executive Summary & Problem Statement

**The Problem:** 
Fragmented citizen feedback systems across developing economies often lead to misaligned public infrastructure investments. Without a standardized, multilingual approach to aggregating ground-level reports, critical infrastructure gaps in water sanitation, transportation, and healthcare remain unaddressed, while public funds are deployed inefficiently.

**The Solution:** 
**NagarikBRICS** is a multilingual, privacy-preserving AI orchestration platform designed as a Digital Public Good (DPG). By synthesizing unstructured citizen feedback (voice/text) against national demographic indices and infrastructure indicators, the platform generates prioritized, budget-estimated infrastructure project recommendations for policymakers. It leverages Google Gemini for high-speed, zero-local-model reasoning to instantly identify geographic demand hotspots.

---

## Polyglot Microservice Architecture

The platform operates on a decoupled, zero-bloat microservice architecture optimized for speed, security, and low environmental overhead.

- **Java 21 Ingestion Service** (`services/java-ingestion`):
  - **Purpose**: High-throughput DTO parsing, aggressive input validation, and serialization.
  - **Details**: Built with native Spring Boot 3.3.2 (no ORM/Lombok bloat). Implements strict Jackson configurations and UUID v4 tracing.
- **Python AI Core** (`services/python-ai-core` & `api/index.py`):
  - **Purpose**: Google Gemini SDK integration, multilingual translation (Portuguese, Russian, Hindi, Mandarin, English), and hotspot analysis.
  - **Details**: Utilizes `FastAPI` and Pydantic v2 for strict schema enforcement. Computes a proprietary Priority Scoring Formula (Urgency 40% + Volume 25% + Index Gap 25% + Sentiment 10%). Also includes a Vercel-ready Serverless endpoint for secure frontend AI chat integration.
- **Frontend Dashboard** (`services/frontend-ui`):
  - **Purpose**: Multilingual Citizen Simulator and Policymaker Intelligence Canvas.
  - **Details**: 100% Vanilla HTML5, CSS3, and ES6 JavaScript. Zero heavy mapping libraries (custom interactive SVG canvas). Strictly adheres to the WCAG 2.1 AA accessibility standards (ARIA roles, keyboard focus navigation).
- **Docker Orchestration**:
  - **Security First**: All three containers execute as non-root users (`appuser` UID 1001 or Alpine `nginx`).
  - **Efficiency**: Multi-stage builds (`builder` -> `runtime`/`slim`) ensure minimal final image sizes, blocking source code and build tools from production runtimes.

---

## Metrics & Compliance

| Metric / Domain | Status | Description |
| :--- | :--- | :--- |
| **Repository Size** | **< 300 KB** | Strictly constrained source footprint (Currently ~271 KB, ~6.6% of a 4 MB absolute limit), ensuring extreme portability. |
| **Security Boundaries** | **Hardened** | Strict CSP meta tags, XSS Entity Mapping, frozen JS objects (`Object.freeze()`), and dangerous URI protocol filtering. |
| **Code Quality** | **Grade A** | 100% Python type hints, comprehensive Java Javadocs, fully JSDoc-annotated JavaScript, and Pydantic field regex validators. |
| **Automated Testing** | **8 / 8 Passed** | E2E Security and API Contract Test Runner explicitly validates XSS blocks, schema limits, and cross-service payload structures. |

---

## Getting Started & Deployment Guide

NagarikBRICS supports both local containerized execution and modern serverless deployment topologies.

### 1. Local Execution (Docker Compose)
To run the full decoupled microservice topology locally:

```bash
# 1. Export your Gemini API Key
export GEMINI_API_KEY="your_google_gemini_key_here"

# 2. Build and start the cluster in detached mode
docker compose up --build -d

# 3. Access the Policymaker Dashboard
# Navigate to http://localhost in your browser
```

### 2. Vercel Serverless Deployment
For zero-config deployment, the repository is configured natively for Vercel.

1. Connect the repository to your Vercel account.
2. In the Vercel Project Settings, add the Environment Variable:
   - `GEMINI_API_KEY` = `your_google_gemini_key_here`
3. Vercel automatically uses `vercel.json` to:
   - Route `/api/(.*)` to the secure Python serverless endpoint (`api/index.py`).
   - Serve static assets and UI directly from the Edge network.

### 3. Running the Test Suite
To manually execute the security and API contract test suite:

```bash
# Ensure Node.js is installed, then run:
node services/frontend-ui/tests/test_runner.js
```
*(Expected Output: `TEST SUMMARY: 8 Passed, 0 Failed`)*
