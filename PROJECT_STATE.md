# Project State Tracker: AI-Powered Researcher–Student Collaboration System

**Project Name:** AI-Powered Researcher–Student Collaboration Recommendation System  
**Current Phase:** Phase 7 (Final Validation & Deployment Readiness) — COMPLETE  
**Last Updated:** 2026-10-23  

---

## 1. Executive Status Summary

| Phase | Description | Status |
| :---: | :--- | :---: |
| **Phase 0** | Planning, Architecture Design, Normalized Schema, API Standards | ✅ Completed |
| **Phase 1** | Backend Foundation, Database ORM Models, Alembic Migrations, Docker Environment, CRUD Endpoints & Tests | ✅ Completed |
| **Phase 2** | Ingestion & Validation Pipeline, Deduplication Engine, Provenance Logger, Synthetic Data Generator, Admin APIs & CLI | ✅ Completed |
| **Phase 3** | Text Preprocessing, Sentence Transformers Vector Pipeline, Hybrid Recommendation Engine & Offline Evaluation | ✅ Completed |
| **Phase 4** | Complete Frontend Application (React, Vite, Tailwind CSS 3.4) & Full Authentication / RBAC | ✅ Completed |
| **Phase 5** | Integration Testing, End-to-End Workflow Verification, Security Hardening, Rate Limiting & Documentation | ✅ Completed |
| **Phase 6** | Real Academic Data Connectors (OpenAlex & Crossref), Institutional CSV Roster, Faculty Verification & Diversity-Aware MMR | ✅ Completed |
| **Phase 7** | Final Validation, Deployment Readiness, Automated Workflow Tests & Production Packaging | ✅ Completed |

---

## 2. Phase 2 Deliverables Summary

### 2.1 Preprocessing & Normalization Services
- **`backend/app/ingestion/preprocessing.py`**:
  - `normalize_text()`: Unicode NFKC normalization, whitespace/tab/linebreak collapse, edge trimming.
  - `normalize_doi()`: Strips URL prefixes (`https://doi.org/`, `doi:`), converts to canonical lowercase.
  - `generate_title_hash()`: Deterministic SHA-256 hash ignoring punctuation and whitespace for bulletproof entity deduplication.
  - `slugify()`: URL-safe hyphen-delimited slugs for taxonomy nodes.

### 2.2 Ingestion Schemas (DTOs) & Deduplication Engine
- **`backend/app/ingestion/schemas.py`**: Strongly typed Pydantic Ingestion DTOs for `TopicSkillIngestDTO`, `StudentIngestDTO`, `FacultyIngestDTO`, `PublicationIngestDTO`, `ProjectIngestDTO`, and `RelevanceJudgmentIngestDTO`.
- **`backend/app/ingestion/deduplication.py`**: Fast entity resolution checking existing publications by DOI or title hash, topics by slug or canonical name, and users by email.
- **`backend/app/ingestion/pipeline.py`**:
  - Orchestrates batch validation, transactional entity insertion, relationship wiring, and provenance logging (`data_sources`, `import_jobs`, `entity_provenance`).
  - Implements safe, isolated synthetic data resets (`reset_synthetic_data()`) ensuring real research data is never deleted.

### 2.3 Synthetic Dataset Generator
- **`backend/app/synthetic/taxonomy_data.py`**: Curated hierarchical taxonomy spanning 8 research domains.
- **`backend/app/synthetic/templates.py`**: Realistic paper titles, abstracts, top venues (NeurIPS, ACL, CVPR, KDD, USENIX, IROS, CHI, SIGIR), faculty lab names, student SOPs, and project descriptions.
- **`backend/app/synthetic/generator.py`**: Deterministic pseudo-random generation with configurable seed (default: `42`).

---

## 3. Phase 3 Deliverables Summary

### 3.1 Academic Text Aggregator (`backend/app/embeddings/text_aggregator.py`)
- Profile compilation for students, faculty, publications, and projects.

### 3.2 Embedding Service (`backend/app/embeddings/service.py`)
- Sentence Transformers `all-MiniLM-L6-v2` with deterministic semantic hash fallback.

### 3.3 Hybrid Recommendation Engine (`backend/app/recommendations/`)
- 4-signal scoring: Research Intent (35%), Project Alignment (25%), Publication Relevance (25%), Skill Compatibility (15%).

### 3.4 Offline Evaluation Framework (`backend/app/evaluation/`)
- NDCG@K, Precision@K, Recall@K, and MRR offline evaluation metrics.

---

## 4. Phase 4 Deliverables Summary: Complete Frontend & UX

### 4.1 Frontend Architecture & Design System
- **Framework & Tooling:** React 19, TypeScript, Vite 8, Tailwind CSS 3.4 with PostCSS and Autoprefixer.
- **Design Aesthetic:** Dark mode primary theme with deep slate backdrop, tailored HSL brand indigo/violet gradients, Google Fonts (Inter + JetBrains Mono), glassmorphism frosted panels, subtle micro-animations, and accessible color-contrast indicators.
- **State Management & Routing:** `AuthContext` with JWT bearer persistence in `localStorage`, role-aware `ProtectedRoute` navigation guard, and centralized typed API client with Vite dev server proxy to backend `/api/v1`.

### 4.2 Required Pages Implemented
1. **Landing Page (`src/pages/LandingPage.tsx`)**:
   - Hero banner with headline, problem analysis vs solution breakdown, 4-signal architecture feature cards, system metrics, and quick demo switchers.
2. **Authentication Pages (`src/pages/LoginPage.tsx` & `src/pages/RegisterPage.tsx`)**:
   - Proper backend JWT authentication with bcrypt salted passwords (`POST /api/v1/auth/login`, `POST /api/v1/auth/register`, `GET /api/v1/auth/me`).
   - One-click demo autofills for instant student and administrator sessions.
3. **Student Dashboard (`src/pages/StudentDashboard.tsx`)**:
   - Dynamic profile completeness score calculation (0–100%) based on research statement, bio, skills, and projects.
   - Project showcase with repository links, skill levels visualization, and past recommendation run history.
4. **Student Profile Editor (`src/pages/StudentProfileEditor.tsx`)**:
   - Live editing of statement of purpose, bio, department, degree level, GPA, and availability.
   - Interactive modal to add/remove academic projects with role descriptions.
   - Interactive modal to select and add skills from the standardized taxonomy (`GET /api/v1/taxonomy/topics`).
5. **Researcher Directory (`src/pages/FacultyDirectory.tsx`)**:
   - Live search input for faculty name, lab, or bio keywords.
   - Department filter dropdown, "Accepting Students Only" toggle, and paginated grid layout.
   - Synthetic badge indicators for test benchmark records.
6. **Researcher Detail Page (`src/pages/FacultyDetailPage.tsx`)**:
   - Verified profile view with lab name, website URL, office location, and mentorship capacity progress indicator.
   - Full publication bibliography with venues, abstracts, publication years, citations, and external DOI links.
7. **Recommendation Results (`src/pages/RecommendationResults.tsx`)**:
   - Ranked faculty cards with overall match score percentage badge.
   - Visual multi-signal score breakdown (`ScoreBar` for Research Intent, Projects, Publications, Skills).
   - Extractive explanation summary and capacity warning caveats.
   - Interactive weight customization sliders allowing students to tune the algorithm in real-time.
   - Evidence inspection modal to examine why a specific professor was recommended.
   - Interactive 1–5 star rating feedback submission persisted to the backend audit log.
8. **Admin Dashboard (`src/pages/AdminDashboard.tsx`)**:
   - Live entity counts broken down by data mode (`synthetic` vs `real`).
   - Configurable synthetic data generator trigger and isolated synthetic reset trigger.
   - Embedding synchronization trigger and 384-d vector statistics.
   - Offline IR relevance benchmark runner displaying live NDCG@5, Precision@5, Recall@5, and MRR.
   - Future-ready connector architecture preview for OpenAlex and Semantic Scholar real data.
   - Provenance import jobs audit table.
9. **Error & Empty States (`src/pages/NotFoundPage.tsx`)**:
   - Informative empty and error states guiding users on incomplete profiles, zero search results, or connection issues.

### 4.3 Backend Endpoints Added in Phase 4
- `POST /api/v1/auth/login` — Authenticate user and issue signed JWT token.
- `POST /api/v1/auth/register` — Register user and initialize linked student/faculty profile.
- `GET /api/v1/auth/me` — Return current authenticated session with profile data.
- `GET /api/v1/taxonomy/topics` — List standardized taxonomy skills and research topics.
- `POST /api/v1/students/{id}/projects` & `DELETE /api/v1/students/{id}/projects/{pid}` — Manage student projects.
- `POST /api/v1/students/{id}/skills` & `DELETE /api/v1/students/{id}/skills/{sid}` — Manage student skills.

### 4.4 Automated Testing & Verification
- **Frontend Test Suite:** Vitest + React Testing Library (5 passed tests across components, score bars, badges, and landing page).
- **Frontend Production Build:** `tsc -b && vite build` built cleanly in 1.72s with zero TypeScript errors.
- **Backend Test Suite:** 94 passed tests in 3.43s covering auth, recommendations, embeddings, evaluation, scoring, CRUD, and data pipelines.

---

## 5. How to Run the Platform

### Running the Backend Server
```powershell
# 1. Activate python virtual environment
.venv\Scripts\Activate.ps1

# 2. Start the FastAPI development server
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Documentation (Swagger UI): `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/v1/health`

### Running the Frontend Application
```powershell
# In a separate terminal:
cd frontend
npm run dev
```
- Frontend application URL: `http://localhost:5173`
- Pre-configured Vite proxy forwards all `/api/*` calls directly to `http://127.0.0.1:8000`.

### Running Tests
```powershell
# Run backend tests (101 tests passing)
.venv\Scripts\python -m pytest backend/tests/ -v

# Run frontend tests (11 tests passing)
cd frontend
npm run test

# Validate production build (clean bundle)
cd frontend
npm run build
```

---

## 6. Architecture Decision Records (ADRs)

- **ADR-001:** Normalized Single Schema for Both Synthetic and Real Academic Data.
- **ADR-002:** Vector Search with PostgreSQL `pgvector` and HNSW Indexing.
- **ADR-003:** Multi-Stage Hybrid Recommendation Pipeline.
- **ADR-004:** Extractive, Evidence-Based Explanations.
- **ADR-005:** Frontend Tech Stack Selection (React + Vite + Tailwind CSS 3.4 + PostCSS).
- **ADR-006:** Universal DB Engine Abstraction (Async PostgreSQL / psycopg3 in production, aiosqlite in memory tests).
- **ADR-007:** Strict Provenance & Synthetic Data Isolation.
- **ADR-008:** Dual-Engine Vectorization & Deterministic Semantic Fallback.
- **ADR-009:** JWT Bearer Authentication & Role-Based Access Control (RBAC): Enforces authentication at the FastAPI backend level with bcrypt hashing; frontend route guards provide UX routing while backend validates every request.

---

## 7. Phase 6 Deliverables Summary: Real Research Data Integration

### 7.1 OpenAlex API Connector & Polite Pool Compliance (`backend/app/connectors/openalex_client.py`)
- Modular async HTTP client for the official OpenAlex REST API with polite pool mailto identification.
- Exponential backoff with jitter on 429 rate limit responses.
- Accurate abstract inverted index reconstruction (`reconstruct_abstract`) restoring full paper abstracts.
- Dedicated methods: `search_works`, `get_work_by_doi`, `search_authors`, `search_institutions`.

### 7.2 Crossref Metadata Enrichment & Conflict Resolution (`backend/app/connectors/crossref_client.py`)
- Modular client querying `api.crossref.org/works/{doi}` with polite pool headers.
- Strips JATS XML markup (`<jats:p>`, `<jats:sec>`) from abstracts cleanly.
- Transparent conflict resolution with OpenAlex: merges authoritative DOI, publication year, journal venue, and abstract while preserving OpenAlex citation counts and concept tags.

### 7.3 Institutional CSV Faculty Roster Importer (`backend/app/connectors/csv_importer.py`)
- Parses institutional faculty rosters with validation against required columns: `first_name`, `last_name`, `email`, `department`, `title_rank`, `max_capacity`.
- Assigns `VERIFIED` verification status automatically to official institutional roster imports.

### 7.4 Ingestion Orchestrator & Provenance Pipeline (`backend/app/ingestion/real_data_service.py`)
- Orchestrates transactional import of genuine works, authors, and rosters.
- Enforces entity deduplication via normalized DOI and title hash (`SHA-256`).
- Automatic 384-dimensional vector embedding generation for newly imported entities.
- Full audit tracking in `import_jobs` and `entity_provenance`.

### 7.5 Scholarly REST API Endpoints (`backend/app/api/v1/endpoints/scholarly.py`)
- `GET /api/v1/scholarly/search/works`: Live OpenAlex works search with optional ROR and year filters.
- `GET /api/v1/scholarly/search/authors`: Live OpenAlex author search.
- `GET /api/v1/scholarly/search/institutions`: Institution lookup by name or ROR.
- `POST /api/v1/scholarly/import/works`: Batch works ingestion with Crossref enrichment option.
- `POST /api/v1/scholarly/import/authors`: Batch author ingestion with pending review status.
- `POST /api/v1/scholarly/import/csv`: Institutional CSV roster upload.
- `GET /api/v1/scholarly/summary`: Breakdown of real vs. synthetic entities and verification counts.
- `GET /api/v1/scholarly/verification/faculty`: Paginated faculty verification queue.
- `PUT /api/v1/scholarly/verification/faculty/{id}`: Administrative status updates with verification notes.
- `POST /api/v1/scholarly/verification/faculty/batch`: Batch verification/rejection.

### 7.6 Operating Mode Separation & Diversity-Aware MMR Reranking
- Recommendation engine supports explicit `data_mode` filters: `ALL`, `REAL_ONLY`, and `SYNTHETIC_ONLY`.
- Maximal Marginal Relevance (MMR) reranking prevents near-duplicate faculty from dominating top recommendations.
- UI badges explicitly tag entity origin: `<RealDataBadge />` (OpenAlex/CSV) vs `<SyntheticBadge />` and verification status: `<VerificationBadge />` (`VERIFIED`, `PENDING_REVIEW`, `UNVERIFIED`, `REJECTED_OUTDATED`).

### 7.7 Testing & Verification Metrics
- **Backend Tests:** 114 passing tests across database, ingestion, recommendation engine, real data connectors, and security.
- **Frontend Tests:** 11 passing Vitest unit tests verifying components, navigation, and landing workflows.
- **Production Build:** Clean TypeScript & Vite build producing optimized production bundle.

---

## 8. Phase 7 Deliverables Summary: Final Validation and Deployment Readiness

### 8.1 Automated End-to-End Workflow Tests (`backend/tests/test_phase7_validation_workflows.py`)
- **Workflow A (Synthetic Demonstration):**
  - Full automated lifecycle: admin dataset seeding (15 students, 10 faculty, 25 publications), dense vector embedding synchronization, student recommendation generation with `SYNTHETIC_ONLY` mode, multi-signal evidence and score decomposition assertion, and offline IR evaluation benchmark execution.
- **Workflow B (Real Research Data):**
  - Full automated lifecycle: OpenAlex work ingestion with inverted index abstract reconstruction, OpenAlex researcher ingestion tagged as `PENDING_REVIEW`, institutional CSV roster upload automatically tagged as `VERIFIED`, provenance verification in `import_jobs` and `entity_provenance`, non-destructive entity deduplication (updating citations rather than duplicating), vector synchronization, `REAL_ONLY` recommendation filtering, and strict `verified_only=True` exclusion verification.

### 8.2 Production Deployment Packaging & Infrastructure
- **Multi-Container Topology (`docker-compose.yml`):**
  - PostgreSQL 16 + pgvector container (`stu_postgres`) with isolated named volume `pgdata` and internal network `collab_network`.
  - FastAPI Backend container (`stu_backend`) with non-root user considerations, `PYTHONPATH` resolution, automatic Alembic migration on startup, and healthchecks on `/health`.
  - Frontend SPA container (`stu_frontend`) with multi-stage build (Node 20 build -> Nginx Alpine runtime) and reverse proxy routing for API traffic.
- **Nginx SPA Configuration (`frontend/nginx.conf`):**
  - Handles client-side HTML5 history routing (`try_files $uri $uri/ /index.html`), gzip compression, and proxies `/api/` and `/docs` directly to the backend.
- **Production Documentation (`docs/DEPLOYMENT_OPERATIONS.md`):**
  - Complete operations manual covering architecture topology, environment variables, Alembic versioning, automated `pg_dump`/`pg_restore` disaster recovery procedures, structured logging, health checks, and manual external configuration prerequisites.

