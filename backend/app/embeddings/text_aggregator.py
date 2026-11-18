"""Academic Text Aggregator: Composes rich profile documents for embedding generation.

Produces structured text concatenations that capture the full semantic footprint
of student research interests and faculty expertise, ensuring vector embeddings
reflect the complete academic profile rather than isolated fields.
"""

from typing import List, Optional
from backend.app.ingestion.preprocessing import normalize_text
from backend.app.models.faculty import Faculty
from backend.app.models.project import AcademicProject
from backend.app.models.publication import Publication
from backend.app.models.student import Student
from backend.app.models.taxonomy import FacultySkillExpertise, StudentSkillInterest


def compose_student_profile_text(
    student: Student,
    skills: Optional[List[StudentSkillInterest]] = None,
    projects: Optional[List[AcademicProject]] = None,
) -> str:
    """Composes a comprehensive student profile document for embedding.

    Structure:
      1. Statement of purpose (primary research intent signal)
      2. Bio (supplementary context)
      3. Academic projects (titles + descriptions — practical experience signal)
      4. Skills and interests (taxonomy keywords — lexical anchor signal)
      5. Department and degree level (institutional context)
    """
    parts: List[str] = []

    # Primary intent signal
    if student.statement_of_purpose:
        parts.append(f"Research Statement: {student.statement_of_purpose}")

    if student.bio:
        parts.append(f"Background: {student.bio}")

    # Projects provide concrete evidence of applied research
    actual_projects = projects if projects is not None else getattr(student, "academic_projects", [])
    for proj in (actual_projects or []):
        proj_text = f"Project - {proj.title}: {proj.description}"
        if proj.role:
            proj_text += f" (Role: {proj.role})"
        parts.append(proj_text)

    # Skills provide taxonomic anchor tokens
    actual_skills = skills if skills is not None else getattr(student, "skills_interests", [])
    skill_names = []
    for si in (actual_skills or []):
        name = si.topic_skill.name if hasattr(si, "topic_skill") and si.topic_skill else None
        if name:
            skill_names.append(name)
    if skill_names:
        parts.append(f"Skills and Interests: {', '.join(skill_names)}")

    # Institutional context
    if student.department:
        parts.append(f"Department: {student.department}")
    if student.degree_level:
        parts.append(f"Degree Level: {student.degree_level}")

    combined = " ".join(parts)
    return normalize_text(combined) or ""


def compose_faculty_profile_text(
    faculty: Faculty,
    expertise: Optional[List[FacultySkillExpertise]] = None,
    publications: Optional[List[Publication]] = None,
) -> str:
    """Composes a comprehensive faculty profile document for embedding.

    Structure:
      1. Bio / research narrative (primary research identity signal)
      2. Lab name (specialized unit identity)
      3. Publication titles and abstracts (evidence of active research)
      4. Expertise keywords (taxonomic anchors)
      5. Department and rank (institutional context)
    """
    parts: List[str] = []

    # Primary research identity
    if faculty.bio:
        parts.append(f"Research Profile: {faculty.bio}")

    if faculty.lab_name:
        parts.append(f"Laboratory: {faculty.lab_name}")

    # Publications provide the strongest evidence of active research direction
    actual_pubs = publications or []
    for pub in actual_pubs[:8]:  # Cap at 8 to avoid overly long documents
        pub_text = f"Publication - {pub.title}"
        if pub.abstract:
            # Truncate very long abstracts to prevent any single publication from dominating
            abstract_excerpt = pub.abstract[:300]
            pub_text += f": {abstract_excerpt}"
        parts.append(pub_text)

    # Expertise keywords
    actual_expertise = expertise if expertise is not None else getattr(faculty, "skills_expertise", [])
    expertise_names = []
    for fe in (actual_expertise or []):
        name = fe.topic_skill.name if hasattr(fe, "topic_skill") and fe.topic_skill else None
        if name:
            expertise_names.append(name)
    if expertise_names:
        parts.append(f"Research Expertise: {', '.join(expertise_names)}")

    # Institutional context
    if faculty.department:
        parts.append(f"Department: {faculty.department}")
    if faculty.title_rank:
        parts.append(f"Academic Rank: {faculty.title_rank}")

    combined = " ".join(parts)
    return normalize_text(combined) or ""


def compose_publication_text(publication: Publication) -> str:
    """Composes searchable publication text for individual publication embedding."""
    parts: List[str] = []

    if publication.title:
        parts.append(publication.title)
    if publication.abstract:
        parts.append(publication.abstract)
    if publication.venue:
        parts.append(f"Venue: {publication.venue}")

    combined = ". ".join(parts)
    return normalize_text(combined) or ""


def compose_project_text(project: AcademicProject) -> str:
    """Composes text for an individual student project embedding."""
    parts: List[str] = []

    if project.title:
        parts.append(project.title)
    if project.description:
        parts.append(project.description)
    if project.role:
        parts.append(f"Role: {project.role}")

    # Include project skill names if loaded
    project_skills = getattr(project, "skills", [])
    if project_skills:
        skill_names = [s.name for s in project_skills if hasattr(s, "name")]
        if skill_names:
            parts.append(f"Technologies: {', '.join(skill_names)}")

    combined = ". ".join(parts)
    return normalize_text(combined) or ""
