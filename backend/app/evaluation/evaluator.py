import re
from collections import defaultdict
from typing import Any, Dict, List, Set
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.evaluation.baseline_tfidf import TfidfBaseline
from backend.app.evaluation.metrics import (
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from backend.app.models.evaluation import RelevanceJudgment
from backend.app.models.faculty import Faculty
from backend.app.models.student import Student
from backend.app.recommendations.engine import recommendation_engine
from backend.app.recommendations.schemas import RecommendationRequest
from backend.app.synthetic.templates import DOMAIN_RESEARCH_TEMPLATES


class BenchmarkEvaluator:
    def __init__(self):
        self.tfidf_baseline = TfidfBaseline()

    async def run_evaluation(
        self,
        db: AsyncSession,
        benchmark_suite: str = "standard_eval_v1",
        k_values: List[int] = [5, 10],
    ) -> Dict[str, Any]:
        """Executes comparative offline evaluation comparing the Hybrid Embedding Recommender
        with the TF-IDF lexical baseline across benchmark relevance judgments.
        Prevents relevance judgments from leaking into feature representations.
        """
        # 1. Fetch Relevance Judgments
        stmt = (
            select(RelevanceJudgment)
            .where(RelevanceJudgment.benchmark_suite == benchmark_suite)
            .order_by(RelevanceJudgment.student_id)
        )
        judgments = list((await db.execute(stmt)).scalars().all())

        if not judgments:
            return {
                "benchmark_suite": benchmark_suite,
                "status": "NO_JUDGMENTS_FOUND",
                "message": f"No relevance judgments found for suite '{benchmark_suite}'.",
            }

        # Group judgments by student
        student_judgments_map: Dict[UUID, Dict[UUID, int]] = defaultdict(dict)
        for rj in judgments:
            student_judgments_map[rj.student_id][rj.faculty_id] = rj.relevance_grade

        # Fetch all candidate faculty for baseline
        candidate_faculty = list(
            (
                await db.execute(
                    select(Faculty).options(
                        selectinload(Faculty.skills_expertise),
                        selectinload(Faculty.authorship_links),
                    )
                )
            )
            .scalars()
            .all()
        )

        embedding_metrics: Dict[str, List[float]] = defaultdict(list)
        baseline_metrics: Dict[str, List[float]] = defaultdict(list)
        per_student_metrics: List[Dict[str, Any]] = []

        evaluated_students_count = 0

        for student_id, grades_dict in student_judgments_map.items():
            # Fetch student
            stu_stmt = (
                select(Student)
                .where(Student.id == student_id)
                .options(
                    selectinload(Student.skills_interests),
                    selectinload(Student.academic_projects),
                )
            )
            student = (await db.execute(stu_stmt)).scalars().first()
            if not student:
                continue

            # Ground truth: grade >= 2 is considered relevant
            relevant_ids: Set[UUID] = {fac_id for fac_id, grade in grades_dict.items() if grade >= 2}

            evaluated_students_count += 1
            max_k = max(k_values)

            # --- 1. Evaluate Hybrid Embedding Engine ---
            req = RecommendationRequest(student_id=student_id, top_k=max_k)
            rec_res = await recommendation_engine.generate_recommendations(db, req)
            emb_ranked_ids = [item.faculty_id for item in rec_res.recommendations]

            # Compute embedding metrics
            student_embedding_metrics: Dict[str, float] = {}
            student_baseline_metrics: Dict[str, float] = {}
            for k in k_values:
                student_embedding_metrics[f"precision@{k}"] = precision_at_k(
                    emb_ranked_ids, relevant_ids, k
                )
                student_embedding_metrics[f"recall@{k}"] = recall_at_k(
                    emb_ranked_ids, relevant_ids, k
                )
                student_embedding_metrics[f"ndcg@{k}"] = ndcg_at_k(
                    emb_ranked_ids, grades_dict, k
                )
            student_embedding_metrics["mrr"] = reciprocal_rank(
                emb_ranked_ids, relevant_ids
            )
            for metric, value in student_embedding_metrics.items():
                embedding_metrics[metric].append(value)

            # --- 2. Evaluate TF-IDF Baseline ---
            tfidf_ranked = self.tfidf_baseline.rank_candidates(student, candidate_faculty)
            tfidf_ranked_ids = [fac_id for fac_id, _ in tfidf_ranked[:max_k]]

            for k in k_values:
                student_baseline_metrics[f"precision@{k}"] = precision_at_k(
                    tfidf_ranked_ids, relevant_ids, k
                )
                student_baseline_metrics[f"recall@{k}"] = recall_at_k(
                    tfidf_ranked_ids, relevant_ids, k
                )
                student_baseline_metrics[f"ndcg@{k}"] = ndcg_at_k(
                    tfidf_ranked_ids, grades_dict, k
                )
            student_baseline_metrics["mrr"] = reciprocal_rank(
                tfidf_ranked_ids, relevant_ids
            )
            for metric, value in student_baseline_metrics.items():
                baseline_metrics[metric].append(value)

            statement = (student.statement_of_purpose or "").lower()
            primary_area = re.search(
                r"primary research area:\s*([^.]+)", statement
            )
            area_text = primary_area.group(1).strip() if primary_area else statement
            domain = next(
                (
                    name.replace("-", " ").title()
                    for name in DOMAIN_RESEARCH_TEMPLATES
                    if area_text.startswith(name.replace("-", " "))
                ),
                next(
                    (
                        name.replace("-", " ").title()
                        for name in DOMAIN_RESEARCH_TEMPLATES
                        if name.replace("-", " ") in statement
                    ),
                    "Unknown",
                ),
            )
            profile_type = (
                "complete"
                if student.bio and student.skills_interests and student.academic_projects
                else "incomplete"
            )
            per_student_metrics.append(
                {
                    "domain": domain,
                    "profile_type": profile_type,
                    "hybrid": student_embedding_metrics,
                    "tfidf": student_baseline_metrics,
                }
            )

        if evaluated_students_count == 0:
            return {
                "benchmark_suite": benchmark_suite,
                "status": "NO_VALID_QUERIES",
                "message": "Judgments exist but none reference an existing student.",
            }

        # Calculate macro averages
        def _macro_avg(metric_list: List[float]) -> float:
            return round(float(sum(metric_list) / len(metric_list)), 4) if metric_list else 0.0

        summary_embedding = {m: _macro_avg(vals) for m, vals in embedding_metrics.items()}
        summary_baseline = {m: _macro_avg(vals) for m, vals in baseline_metrics.items()}

        def summarize_groups(group_field: str) -> Dict[str, Any]:
            grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
            for result in per_student_metrics:
                grouped[result[group_field]].append(result)
            return {
                group: {
                    "queries_evaluated": len(results),
                    "hybrid_embedding_scores": {
                        metric: _macro_avg(
                            [result["hybrid"][metric] for result in results]
                        )
                        for metric in summary_embedding
                    },
                    "tfidf_baseline_scores": {
                        metric: _macro_avg(
                            [result["tfidf"][metric] for result in results]
                        )
                        for metric in summary_baseline
                    },
                }
                for group, results in sorted(grouped.items())
            }

        comparison = {}
        for m in summary_embedding.keys():
            emb_val = summary_embedding[m]
            base_val = summary_baseline.get(m, 0.0)
            lift = round(((emb_val - base_val) / max(base_val, 1e-6)) * 100.0, 2)
            comparison[m] = {
                "hybrid_embedding": emb_val,
                "tfidf_baseline": base_val,
                "relative_lift_percent": f"{lift:+.2f}%",
            }

        return {
            "benchmark_suite": benchmark_suite,
            "queries_evaluated": evaluated_students_count,
            "total_judgments": len(judgments),
            "comparison": comparison,
            "hybrid_embedding_scores": summary_embedding,
            "tfidf_baseline_scores": summary_baseline,
            "by_research_domain": summarize_groups("domain"),
            "by_profile_completeness": summarize_groups("profile_type"),
            "limitations_and_caveats": [
                "Synthetic evaluation judgments are generated from topic and expertise relationships rather than verified advisor outcomes.",
                "Real academic matching quality will be further validated upon real OpenAlex publication and institutional student intake.",
                "Relevance judgments were strictly excluded from model feature extraction and used solely at scoring comparison time.",
            ],
        }


benchmark_evaluator = BenchmarkEvaluator()
