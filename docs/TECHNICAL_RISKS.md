# Technical Risks, Dependencies & Mitigation Strategies

**Document Version:** 1.0.0  
**Phase:** Phase 0 (Planning & Architecture)  

---

## 1. Risk Analysis Matrix

| # | Risk Category | Risk Description | Severity | Likelihood | Mitigation Strategy |
| :- | :--- | :--- | :---: | :---: | :--- |
| **R1** | **Cold Start** | New students or faculty with sparse publication records or empty research statements cannot be matched accurately via pure dense embeddings. | **High** | **High** | **Hybrid Fallback Hierarchy**: Fall back from dense publication embeddings to explicit skill/coursework taxonomic overlap, degree level, and department filtering. Provide wizard prompt tips guiding students to enter project summaries. |
| **R2** | **External API Limits** | OpenAlex / Semantic Scholar rate limits, network outages, or API schema changes interrupt live data harvesting. | **High** | **Medium** | **Asynchronous Batch Harvest with Local Caching**: Real data connectors run exclusively via background jobs with exponential backoff and polite pools (`mailto` headers). All harvested data is normalized and stored locally; recommender queries local PostgreSQL only. |
| **R3** | **Vector Latency at Scale** | Computing high-dimensional cosine similarity over thousands of faculty publications on every user query creates CPU/memory bottlenecks. | **High** | **Low** | **HNSW Indexing + Profile Level Aggregations**: Pre-compute and index both holistic faculty profile vectors and individual publication vectors. In Stage 1 candidate retrieval, query top 50 faculty via HNSW index in pgvector (<10ms), restricting intensive re-ranking only to candidates. |
| **R4** | **Entity Resolution & Deduplication** | Co-authored papers from multiple faculty or different sources (OpenAlex vs manual CSV) duplicate publications, skewing citation counts and vector stores. | **Medium** | **High** | **Strict Deduplication Keying**: Normalize DOIs (lowercase, trimmed). Fallback to composite hashing: SHA-256 of lowercase alphanumeric title + publication year. Maintain strict unique constraints in `publications` table. |
| **R5** | **Embedding Drift & Version Incompatibility** | Changing embedding models (e.g. from MiniLM to SPECTER2) causes vector distance mismatch if stale vectors remain in database. | **High** | **Low** | **Version-Tagged Embeddings**: The `embeddings` table explicitly stores `model_name` and `model_version` with a composite unique constraint `(entity_type, entity_id, embedding_type, model_version)`. Recommender enforces query vector model matching candidate vector model. |
| **R6** | **Explanation Hallucination** | LLM-generated explanations might invent non-existent faculty publications or misrepresent student alignment. | **High** | **Low** | **Extractive, Evidence-Based Explanations**: Do NOT use generative black-box text without grounding. The explanation engine uses deterministic extraction: exact publication titles, direct cosine contribution, and matched taxonomy nodes with direct links. |
| **R7** | **Memory Footprint of ML Models** | Loading Sentence Transformers (PyTorch) in multiple web workers exhausts container RAM. | **Medium** | **Medium** | **Singleton Model Loader with CPU Quantization**: Shared singleton model instance in FastAPI lifespan, running quantized ONNX or Torch CPU inference with restricted worker count (1-2 Uvicorn workers per container). |

---

## 2. Critical Dependency Breakdown

### 2.1 External Libraries & Toolchains
- **`pgvector` (PostgreSQL Extension)**:
  - *Dependency*: PostgreSQL server must have `vector.so` compiled and loaded.
  - *Mitigation*: Base Docker Compose image pinned to `pgvector/pgvector:pg16`, ensuring pre-compiled vector binaries and HNSW support.
- **`sentence-transformers` & `torch`**:
  - *Dependency*: Model weights downloaded from Hugging Face Hub.
  - *Mitigation*: Cache model weights during Docker build or mount a persistent volume (`/root/.cache/huggingface`) to prevent re-downloading across container restarts. Support offline pre-downloaded weights.
- **`alembic` & `SQLAlchemy 2.x`**:
  - *Dependency*: Database schema migrations.
  - *Mitigation*: Strict migration scripts in version control; CI runs `alembic upgrade head` against a test database on every pull request.

---

## 3. Graceful Degradation & Failure Modes

```mermaid
graph TD
    Query[Student Requests Recommendations] --> CheckVectors{Vector Engine Available?}
    
    CheckVectors -- Yes --> Hybrid[Run Full Hybrid Pipeline:<br/>Semantic + Skill + Capacity + Projects]
    CheckVectors -- No / Timeout --> Fallback1[Fallback: Taxonomic Skill & Lexical Match]
    
    Hybrid --> CheckPubs{Faculty Has Publications?}
    CheckPubs -- Yes --> PubEvidence[Generate Publication-Based Evidence & Explanations]
    CheckPubs -- No --> BioEvidence[Generate Bio & Keyword Match Explanations]

    Fallback1 --> DegradedNotice[Return Recommendations with<br/>'Degraded Mode (Lexical Only)' Notice]
```
