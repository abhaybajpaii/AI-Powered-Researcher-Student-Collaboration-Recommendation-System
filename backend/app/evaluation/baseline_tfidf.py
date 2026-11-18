from typing import Dict, List, Optional, Tuple
from uuid import UUID
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.app.ingestion.preprocessing import normalize_text
from backend.app.models.faculty import Faculty
from backend.app.models.student import Student


class TfidfBaseline:
    """Baseline lexical retrieval model using Scikit-Learn's TfidfVectorizer and cosine similarity.
    Serves as an empirical baseline against the dense hybrid embedding recommendation engine.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=5000,
        )

    def rank_candidates(
        self,
        student: Student,
        candidates: List[Faculty],
    ) -> List[Tuple[UUID, float]]:
        """Ranks candidate faculty for a given student using pure TF-IDF cosine similarity."""
        if not candidates:
            return []

        student_text = normalize_text(f"{student.statement_of_purpose} {student.bio or ''}")
        if not student_text:
            return [(fac.id, 0.0) for fac in candidates]

        corpus = [student_text]
        for fac in candidates:
            fac_text = normalize_text(f"{fac.bio or ''} {fac.lab_name or ''} {fac.department}")
            corpus.append(fac_text or "empty")

        tfidf_matrix = self.vectorizer.fit_transform(corpus)
        query_vec = tfidf_matrix[0]
        doc_matrix = tfidf_matrix[1:]

        sims = cosine_similarity(query_vec, doc_matrix).flatten()

        ranked = [
            (candidates[idx].id, round(float(sims[idx]), 4))
            for idx in range(len(candidates))
        ]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked
