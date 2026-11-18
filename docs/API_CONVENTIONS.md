# REST API Conventions & Error-Handling Standards

**Document Version:** 1.0.0  
**Phase:** Phase 0 (Planning & Architecture)  
**Standard:** OpenAPI 3.1 & RFC 7807 (Problem Details for HTTP APIs)  

---

## 1. Core Principles

1. **RESTful Resource Orientation**: URLs represent nouns (`/students`, `/faculty`, `/recommendations`), and HTTP verbs define operations (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`).
2. **Predictable Versioning**: All production routes are prefixed with `/api/v1/`.
3. **Strict Serialization with Pydantic v2**: All request and response bodies are validated via Pydantic schemas with type enforcement.
4. **Consistent Envelopes for Collections**: List responses provide uniform pagination metadata (`total`, `page`, `page_size`, `items`).

---

## 2. Authentication & Authorization

All secure endpoints require a Bearer token in the `Authorization` header:
```http
Authorization: Bearer <jwt_access_token>
```

### Role-Based Access Control (RBAC)
- `STUDENT`: Can manage own profile (`/students/me`), generate recommendations (`/recommendations/generate`), view results, and submit feedback.
- `FACULTY`: Can manage own lab profile (`/faculty/me`), toggle `accepting_students` status, view student applicants.
- `ADMIN`: Full access to data import jobs (`/admin/import-jobs`), evaluation suites (`/admin/evaluation`), and user management.

---

## 3. Standard Response Format

### 3.1 Single Resource Response (200 OK / 201 Created)
```json
{
  "id": "7b0d2d2a-43c2-48f8-b3d6-444fbfca1b23",
  "first_name": "Alan",
  "last_name": "Turing",
  "department": "Computer Science",
  "created_at": "2026-10-22T08:30:00Z"
}
```

### 3.2 Paginated Collection Response (200 OK)
```json
{
  "items": [
    { "id": "uuid-1", "title": "Quantum Computing Fundamentals" },
    { "id": "uuid-2", "title": "Graph Neural Networks for Biology" }
  ],
  "total": 142,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

---

## 4. Error-Handling Standards (RFC 7807)

All non-2xx responses return a standard `application/problem+json` envelope:

```json
{
  "type": "https://api.collab-matcher.edu/errors/resource-not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "Faculty member with ID '7b0d2d2a-43c2-48f8-b3d6-444fbfca1b23' was not found.",
  "instance": "/api/v1/faculty/7b0d2d2a-43c2-48f8-b3d6-444fbfca1b23",
  "timestamp": "2026-10-22T14:15:00Z",
  "code": "FACULTY_NOT_FOUND",
  "invalid_params": []
}
```

### Validation Error Example (422 Unprocessable Entity)
When input payload validation fails:
```json
{
  "type": "https://api.collab-matcher.edu/errors/validation-error",
  "title": "Request Validation Failed",
  "status": 422,
  "detail": "One or more fields in the request body failed validation constraints.",
  "instance": "/api/v1/recommendations/generate",
  "timestamp": "2026-10-22T14:15:00Z",
  "code": "VALIDATION_ERROR",
  "invalid_params": [
    {
      "field": "top_k",
      "message": "Input should be greater than or equal to 1",
      "value": 0
    }
  ]
}
```

---

## 5. HTTP Status Code Guidelines

| Code | Meaning | When to Use |
| :--- | :--- | :--- |
| `200 OK` | Request succeeded | `GET`, `PUT`, `PATCH`, or idempotent `POST` returning immediate data. |
| `201 Created` | Resource created | `POST` creating an entity; includes created resource representation. |
| `202 Accepted` | Background task queued | `POST` initiating a long-running import job or offline embedding batch. |
| `204 No Content` | Success with empty body | `DELETE` operations or status updates without returning entity. |
| `400 Bad Request` | Malformed request | Semantic error or unparseable query parameter. |
| `401 Unauthorized` | Missing / invalid token | Missing Authorization header, expired JWT, or invalid signature. |
| `403 Forbidden` | Insufficient permissions | Authenticated user lacks required role for requested action. |
| `404 Not Found` | Resource does not exist | Specified UUID or route cannot be located. |
| `409 Conflict` | Duplicate state | Unique constraint conflict (e.g. duplicate email, DOI, or duplicate skill). |
| `422 Unprocessable Entity` | Schema validation error | Pydantic validation failure on request payload. |
| `429 Too Many Requests` | Rate limit exceeded | Client exceeded endpoint rate quota. |
| `500 Internal Error` | Unexpected server error | Uncaught backend exception (logged with internal trace ID). |

---

## 6. Key Endpoint Contract Previews

### 6.1 `POST /api/v1/recommendations/generate`
**Request Body:**
```json
{
  "student_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "top_k": 10,
  "filters": {
    "departments": ["Computer Science", "Electrical Engineering"],
    "only_accepting_students": true,
    "min_capacity": 1
  },
  "weights": {
    "semantic": 0.50,
    "skills": 0.30,
    "projects": 0.15,
    "capacity": 0.05
  }
}
```

**Response Body (200 OK):**
```json
{
  "run_id": "e8d3568c-02cf-48cb-aefd-1d6ebfa7be32",
  "student_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "algorithm_version": "v1.2-hybrid",
  "execution_time_ms": 32.4,
  "recommendations": [
    {
      "faculty_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "faculty_name": "Prof. Sophia Chen",
      "department": "Computer Science",
      "lab_name": "Intelligent Systems Lab",
      "rank_position": 1,
      "overall_score": 0.892,
      "score_breakdown": {
        "semantic_score": 0.924,
        "skill_score": 0.850,
        "project_score": 0.880,
        "capacity_factor": 1.000
      },
      "explanation": {
        "summary": "Prof. Sophia Chen conducts leading research in Graph Neural Networks and Explainable AI, directly matching your project on GNN protein folding and your Python/PyTorch skillset.",
        "top_matching_publications": [
          {
            "publication_id": "pub-uuid-1",
            "title": "Scalable Graph Neural Networks for Biological Structures",
            "year": 2024,
            "venue": "NeurIPS",
            "similarity_score": 0.941,
            "relevant_excerpt": "We propose a novel GNN message-passing formulation that accelerates protein topology analysis..."
          }
        ],
        "shared_skills": ["PyTorch", "Graph Neural Networks", "Bioinformatics"],
        "taxonomic_crossover": ["Machine Learning -> Deep Learning -> Graph Representation"]
      }
    }
  ]
}
```
