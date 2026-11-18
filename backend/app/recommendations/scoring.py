from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from backend.app.models.faculty import Faculty
from backend.app.models.project import AcademicProject
from backend.app.models.publication import Publication
from backend.app.models.student import Student
from backend.app.recommendations.schemas import (
    PublicationEvidence,
    RecommendationWeights,
    ScoreBreakdown,
)


def compute_cosine_similarity(vec1: Optional[List[float]], vec2: Optional[List[float]]) -> float:
    """Computes bounded cosine similarity [0.0, 1.0] between two vectors."""
    if not vec1 or not vec2:
        return 0.0
    u = np.array(vec1, dtype=np.float32)
    v = np.array(vec2, dtype=np.float32)
    norm_u = np.linalg.norm(u)
    norm_v = np.linalg.norm(v)
    if norm_u < 1e-12 or norm_v < 1e-12:
        return 0.0
    sim = float(np.dot(u, v) / (norm_u * norm_v))
    return max(0.0, min(1.0, sim))


def compute_skill_compatibility(
    student_skills: List[Any], faculty_skills: List[Any]
) -> Tuple[float, List[str]]:
    """Computes taxonomic skill overlap between student interests and faculty expertise.
    Returns (normalized_score, shared_skill_names).
    """
    if not student_skills or not faculty_skills:
        return 0.0, []

    stu_topic_map = {}
    for ss in student_skills:
        # ss can be StudentSkillInterest OR dict
        t_id = getattr(ss, "topic_skill_id", None)
        if isinstance(ss, dict):
            t_id = ss.get("topic_skill_id", t_id)
        if not t_id:
            continue
        topic_skill = (
            ss.get("topic_skill") if isinstance(ss, dict) else getattr(ss, "topic_skill", None)
        )
        topic_name = ss.get("topic_name") if isinstance(ss, dict) else None
        t_name = topic_name or (
            topic_skill.get("name")
            if isinstance(topic_skill, dict)
            else getattr(topic_skill, "name", None)
        ) or str(t_id)
        interest = (
            ss.get("interest_level", 3)
            if isinstance(ss, dict)
            else getattr(ss, "interest_level", 3)
        )
        stu_topic_map[t_id] = (t_name, interest)

    fac_topic_map = {}
    for fs in faculty_skills:
        t_id = getattr(fs, "topic_skill_id", None)
        if isinstance(fs, dict):
            t_id = fs.get("topic_skill_id", t_id)
        if not t_id:
            continue
        topic_skill = (
            fs.get("topic_skill") if isinstance(fs, dict) else getattr(fs, "topic_skill", None)
        )
        topic_name = fs.get("topic_name") if isinstance(fs, dict) else None
        t_name = topic_name or (
            topic_skill.get("name")
            if isinstance(topic_skill, dict)
            else getattr(topic_skill, "name", None)
        ) or str(t_id)
        expertise = (
            fs.get("expertise_level", 5)
            if isinstance(fs, dict)
            else getattr(fs, "expertise_level", 5)
        )
        fac_topic_map[t_id] = (t_name, expertise)

    shared_ids = set(stu_topic_map.keys()) & set(fac_topic_map.keys())
    all_ids = set(stu_topic_map.keys()) | set(fac_topic_map.keys())

    if not all_ids:
        return 0.0, []

    # Jaccard index weighted by expertise and interest
    jaccard = len(shared_ids) / len(all_ids)

    # Calculate weighted compatibility on shared skills
    weight_sum = 0.0
    for s_id in shared_ids:
        _, interest = stu_topic_map[s_id]
        _, expertise = fac_topic_map[s_id]
        weight_sum += (interest / 5.0) * (expertise / 5.0)

    score = 0.5 * jaccard + 0.5 * (weight_sum / max(1, len(shared_ids)))
    shared_names = [stu_topic_map[s_id][0] for s_id in shared_ids]

    return round(float(min(1.0, score)), 4), shared_names


def aggregate_top_k_publications(
    query_vector: Optional[List[float]],
    publications: List[Tuple[Publication, Optional[List[float]]]],
    top_k: int = 3,
) -> Tuple[float, List[PublicationEvidence]]:
    """Evaluates individual publications separately and aggregates top-K relevance.
    Does NOT lump all publications into one string.
    Returns (aggregate_score, top_publication_evidences).
    """
    if not query_vector or not publications:
        return 0.0, []

    scored_pubs: List[Tuple[float, Publication]] = []
    for pub, p_vec in publications:
        if p_vec:
            sim = compute_cosine_similarity(query_vector, p_vec)
            scored_pubs.append((sim, pub))

    if not scored_pubs:
        return 0.0, []

    # Sort descending by similarity
    scored_pubs.sort(key=lambda x: x[0], reverse=True)
    top_subset = scored_pubs[:top_k]

    weights = [0.60, 0.30, 0.10][: len(top_subset)]
    total_w = sum(weights)
    weighted_score = sum(score * w for (score, _), w in zip(top_subset, weights)) / total_w

    evidences = [
        PublicationEvidence(
            publication_id=pub.id,
            title=pub.title,
            year=pub.publication_year,
            venue=pub.venue,
            similarity_score=round(score, 4),
            relevant_excerpt=pub.abstract[:200] + ("..." if len(pub.abstract) > 200 else ""),
        )
        for score, pub in top_subset
    ]

    return round(float(weighted_score), 4), evidences


def compute_project_similarity(
    student_projects: List[Tuple[AcademicProject, Optional[List[float]]]] ,
    faculty_publications: List[Tuple[Publication, Optional[List[float]]]] ,
) -> float:
    """Computes relevance between student past projects and faculty publications."""
    if not student_projects or not faculty_publications:
        return 0.0

    scores = []
    for _, proj_vec in student_projects:
        if not proj_vec:
            continue
        for _, pub_vec in faculty_publications:
            if not pub_vec:
                continue
            scores.append(compute_cosine_similarity(proj_vec, pub_vec))

    if not scores:
        return 0.0

    # Max pool top project-publication alignment with soft mean
    scores.sort(reverse=True)
    top_scores = scores[:3]
    return round(float(0.7 * top_scores[0] + 0.3 * (sum(top_scores) / len(top_scores))), 4)


def generate_explanation_summary(
    faculty_name: str,
    lab_name: Optional[str],
    research_score: float,
    skill_score: float,
    shared_skills: List[str],
    top_pubs: List[PublicationEvidence],
    caveats: List[str],
    research_data_available: bool = True,
) -> str:
    """Produces a deterministic, evidence-based textual rationale."""
    sentences = []
    # Lab / Research domain alignment
    if not research_data_available:
        sentences.append(
            "Research-profile similarity could not be calculated from the available information."
        )
    elif research_score >= 0.70:
        sentences.append(
            f"Prof. {faculty_name} has strong conceptual research alignment ({int(research_score * 100)}% thematic match)"
            + (f" within the {lab_name}." if lab_name else ".")
        )
    elif research_score >= 0.50:
        sentences.append(
            f"Prof. {faculty_name} shares complementary research interests ({int(research_score * 100)}% thematic match)."
        )
    else:
        sentences.append(f"Prof. {faculty_name} presents an exploratory cross-disciplinary alignment.")

    # Top publication citation
    if top_pubs:
        best_pub = top_pubs[0]
        publication_details = ", ".join(
            value
            for value in (
                str(best_pub.year) if best_pub.year else None,
                best_pub.venue,
            )
            if value
        )
        publication_details = f" ({publication_details})" if publication_details else ""
        sentences.append(
            f"Key matching publication: \"{best_pub.title}\"{publication_details} with {int(best_pub.similarity_score * 100)}% relevance."
        )

    # Shared skills
    if shared_skills:
        skills_str = ", ".join(shared_skills[:3])
        sentences.append(f"Shared methodological overlap in: {skills_str}.")

    # Caveats
    if caveats:
        sentences.append(f"Note: {caveats[0]}.")

    return " ".join(sentences)
