# AI-Powered Researcher–Student Collaboration Recommendation System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.135+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19+-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9+-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+pgvector-336791?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Pytest](https://img.shields.io/badge/Tests-101%20Backend%20Passed-4CAF50?logo=pytest&logoColor=white)](https://docs.pytest.org)
[![Vitest](https://img.shields.io/badge/Tests-11%20Frontend%20Passed-4CAF50?logo=vitest&logoColor=white)](https://vitest.dev)

A modern, full-stack, enterprise-grade research collaboration and matchmaking platform. The system matches university students with faculty researchers by synthesizing research interests, technical skills, academic projects, faculty biographies, and publication histories into ranked, evidence-grounded recommendations.

---

## Table of Contents

1. [Architectural Overview](#architectural-overview)
2. [Recommendation & Explanation Pipeline](#recommendation--explanation-pipeline)
3. [Evaluation Methodology & Benchmarking](#evaluation-methodology--benchmarking)
4. [Prerequisites & Quickstart](#prerequisites--quickstart)
5. [End-to-End Synthetic Data Workflow](#end-to-end-synthetic-data-workflow)
6. [API Documentation Summary](#api-documentation-summary)
7. [Security & Rate Limiting](#security--rate-limiting)
8. [Testing & Quality Assurance](#testing--quality-assurance)
9. [Known Limitations & Planned Next Steps](#known-limitations--planned-next-steps)

---

## Architectural Overview

The application follows a clean layered architecture with decoupled frontend, asynchronous backend, relational database with vector similarity indexing, and offline evaluation harnesses.

```
┌─────────────────────────────────────────────────────────────┐
│               Frontend (React 19 + TypeScript + Vite)       │
│  - Tailwind CSS + Glassmorphism UI                          │
│  - Role-aware Auth Context (Student & Admin sessions)       │
│  - Interactive Profile Editor, Recommendation Explorer       │
│  - Offline Benchmark Comparison & Analytics Dashboard       │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST / JSON (RFC 7807)
┌──────────────────────────────▼──────────────────────────────┐
│                  Backend (FastAPI + Async Python)           │
│  - Sliding-window Rate Limiting & JWT/API-Key Security      │
│  - Pydantic v2 validation & error formatters                │
│  - SQLAlchemy 2.0 Async ORM + Repository Pattern            │
│  - Sentence Transformers (`all-MiniLM-L6-v2`) Embedding Hub │
│  - Hybrid Multi-Signal Recommendation Engine                │
│  - Offline Evaluation Benchmark Engine (vs TF-IDF baseline) │
└──────────────────────────────┬──────────────────────────────┘
                               │ asyncpg / pgvector
┌──────────────────────────────▼──────────────────────────────┐
│          PostgreSQL 16 + pgvector (or SQLite for tests)     │
│  - Students, Faculty, Publications, Taxonomy tables         │
│  - 384-dimension vector embeddings with cosine indexing     │
│  - Benchmarks, Relevance Judgments, Recommendation Runs     │
└─────────────────────────────────────────────────────────────┘
```

---

## Recommendation & Explanation Pipeline

Matches are calculated using a **hybrid multi-signal scoring algorithm** normalized dynamically based on profile completeness:

$$S_{\text{total}} = w_1 \cdot S_{\text{interest}} + w_2 \cdot S_{\text{project}} + w_3 \cdot S_{\text{pub}} + w_4 \cdot S_{\text{skill}}$$

| Signal | Feature Inputs | Method |
|---|---|---|
| **$S_{\text{interest}}$ (Research Intent)** | Student statement of purpose vs Faculty biography & lab profile | Cosine similarity between 384-dim normalized sentence transformer vectors. |
| **$S_{\text{project}}$ (Project Experience)** | Student academic project descriptions vs Faculty publication abstracts | Pairwise cosine similarity aggregated via $\text{score} = \alpha \max(s) + (1-\alpha) \text{avg}_{\text{top3}}(s)$. |
| **$S_{\text{pub}}$ (Publication Relevance)** | Student research statements vs Faculty publication corpus | Aggregated cosine match highlighting top cited/recent publications. |
| **$S_{\text{skill}}$ (Taxonomy & Skills)** | Overlap of shared topics, technical skills, and proficiency levels | Jaccard-weighted overlap penalized by mismatch in proficiency vs expertise. |

### Grounded Explanations
Every recommendation includes:
- **Interactive Score Breakdown**: Transparent contribution percentage of each signal.
- **Evidence-Based Publications**: Relevant publications with cosine similarity scores and exact excerpts.
- **Shared Skills**: Overlapping taxonomy concepts.
- **Caveats**: Warnings when student projects or statements are missing, avoiding synthetic hallucinations.

---

## Evaluation Methodology & Benchmarking

The system incorporates an offline evaluation framework benchmarked against an information retrieval baseline (**TF-IDF + Cosine Similarity**) across curated ground-truth relevance judgments ($0 = \text{Irrelevant}$ to $3 = \text{Highly Relevant}$):

- **Precision@K**: Fraction of top-K recommendations that are relevant.
- **Recall@K**: Fraction of known relevant faculty captured within top-K.
- **NDCG@K**: Normalized Discounted Cumulative Gain accounting for graded rank order.
- **MRR**: Mean Reciprocal Rank of the first relevant faculty member.

> **Data Leakage Safeguard**: Relevance judgments are stored in separate evaluation tables and are strictly prohibited from entering embedding generation or runtime recommendation weights. Synthetic benchmark judgments cover a student's complete candidate-faculty set so unjudged candidates are not counted as irrelevant.

---

## Prerequisites & Quickstart

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Docker & Docker Compose (optional, for PostgreSQL + pgvector)

### Backend Setup

1. **Clone & Virtual Environment**:
   ```bash
   cd backend
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Environment Configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your PostgreSQL credentials or use default SQLite for testing
   ```

3. **Database Migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Run Backend**:
   ```bash
   uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

### Frontend Setup

1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Run Vite Dev Server**:
   ```bash
   npm run dev
   ```
   Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## End-to-End Synthetic Data Workflow

Run the pipeline using the backend CLI. Point the application at a dedicated, disposable database before seeding; do not use a development or production database for benchmark data. The generator is deterministic for a given seed and creates complete candidate sets for its selected evaluation students.

### Using CLI
```bash
# Run from the repository root after initializing the isolated database schema.
# Small (100 students, 50 faculty, 200 publications, 5,000 judgments)
python -m backend.app.cli seed-synthetic --seed 42 --students 100 --faculty 50 --publications 200 --judgments 5000

# Medium (500 students, 100 faculty, 1,000 publications, 10,000 judgments)
python -m backend.app.cli seed-synthetic --seed 42 --students 500 --faculty 100 --publications 1000 --judgments 10000

# Large (1,000 students, 250 faculty, 3,000 publications, 10,000 judgments)
python -m backend.app.cli seed-synthetic --seed 42 --students 1000 --faculty 250 --publications 3000 --judgments 10000

# Build embeddings and compare the hybrid engine with the TF-IDF baseline
python -m backend.app.cli generate-embeddings
python -m backend.app.cli run-evaluation --suite standard_eval_v1 --k-values 5,10
```

The judgment target is rounded up to whole student candidate sets. For example, 10,000 judgments with 250 faculty evaluates 40 students against all 250 faculty. Evaluation output includes overall, research-domain, and profile-completeness metric groups.

---

## API Documentation Summary

The backend serves interactive OpenAPI docs at `http://localhost:8000/docs`.

| Endpoint | Method | Role | Description |
|---|---|---|---|
| `/api/v1/auth/login` | `POST` | Public | Authenticates user; returns JWT token (Rate limited: 10/min) |
| `/api/v1/auth/register` | `POST` | Public | Registers student profile (Rate limited: 10/min) |
| `/api/v1/students/{id}` | `GET/PUT` | Student/Admin | Fetches or updates complete student profile details |
| `/api/v1/students/{id}/skills` | `POST` | Student | Adds or updates student skills & taxonomy interests |
| `/api/v1/students/{id}/projects` | `POST` | Student | Adds academic project with title, description, skills |
| `/api/v1/faculty` | `GET` | Public | Paginated faculty directory with department & capacity filters |
| `/api/v1/recommendations/generate` | `POST` | Student | Generates multi-signal ranked faculty recommendations |
| `/api/v1/recommendations/runs/{id}/results/{fac_id}/feedback` | `POST` | Student | Submits 1-5 user rating on recommendation accuracy |
| `/api/v1/embeddings/sync` | `POST` | Admin | Syncs vector embeddings across all students, faculty, publications |
| `/api/v1/evaluation/benchmark` | `POST` | Admin | Runs offline comparative evaluation against relevance judgments |
| `/api/v1/admin/reseed` | `POST` | Admin | Wipes and reseeds synthetic dataset idempotently |

---

## Security & Rate Limiting

- **Input Validation**: Strict Pydantic v2 schemas across all payloads with RFC 7807 Problem Details error formatting.
- **Authentication**: Stateless HS256 JWT tokens with role claims (`STUDENT`, `FACULTY`, `ADMIN`).
- **Authorization**: Role-aware endpoint dependencies rejecting unauthorized student access to admin operations.
- **Sliding-Window Rate Limiting**: In-memory rate limiting applied to sensitive auth endpoints preventing brute-force attacks.
- **CORS Protection**: Configurable origins with restricted methods and headers.
- **Credential Hygiene**: Zero hardcoded secrets; `.env.example` template provided; `.env` excluded from version control.

---

## Testing & Quality Assurance

### Backend Tests (101 Passed)
```bash
pytest backend/tests/ -v
```
- `test_end_to_end_workflow.py`: Comprehensive 9-step full workflow lifecycle test.
- `test_recommendations.py`: Multi-signal scoring and ranking accuracy tests.
- `test_evaluation_metrics.py`: Unit tests for Precision@K, Recall@K, NDCG@K, MRR.
- `test_validation.py`: RFC 7807 error format and schema boundary validation.
- `test_students_api.py` & `test_faculty_api.py`: CRUD lifecycle tests.
- `test_synthetic_generator.py`: Seed reproducibility tests.

### Frontend Tests (11 Passed)
```bash
cd frontend
npm run test
```
- Component tests for Button, ScoreBar, Badge, Card, Modal, EmptyState, LoadingSpinner, and Navbar.
- Production bundle verification (`npm run build`).

---

## Known Limitations & Planned Next Steps

1. **External Publication Ingestion**: The current system uses high-fidelity synthetic profiles and publications. The ingestion service architecture is designed to integrate with live **OpenAlex** or **Semantic Scholar** APIs via rate-limited worker queues (Celery/Redis).
2. **Dynamic Cross-Encoders**: Initial candidate retrieval utilizes bi-encoder cosine similarity (`all-MiniLM-L6-v2`). Future releases will add a re-ranking cross-encoder step for the top-20 candidates to boost NDCG@5.
3. **Faculty Feedback Loop**: While students can submit ratings on recommendations, faculty can be given reciprocal intake dashboards to express interest in candidate student profiles.
