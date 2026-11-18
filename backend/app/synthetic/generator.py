import random
from math import ceil
from datetime import date
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from backend.app.ingestion.preprocessing import slugify
from backend.app.ingestion.schemas import (
    BatchIngestPayload,
    FacultyIngestDTO,
    FacultySkillIngestDTO,
    ProjectIngestDTO,
    PublicationIngestDTO,
    RelevanceJudgmentIngestDTO,
    StudentIngestDTO,
    StudentSkillIngestDTO,
)
from backend.app.synthetic.taxonomy_data import (
    ACADEMIC_TAXONOMY_TREE,
    flatten_taxonomy_tree,
)
from backend.app.synthetic.templates import (
    DEPARTMENTS,
    DOMAIN_RESEARCH_TEMPLATES,
    FIRST_NAMES,
    LAST_NAMES,
)


class SyntheticConfig(BaseModel):
    seed: int = Field(default=42, description="Random seed for reproducibility")
    num_students: int = Field(default=30, ge=1, le=5000, description="Number of synthetic students to generate")
    num_faculty: int = Field(default=25, ge=1, le=1000, description="Number of synthetic faculty to generate")
    num_publications: int = Field(default=60, ge=1, le=10000, description="Number of synthetic publications to generate")
    num_relevance_judgments: int = Field(
        default=40,
        ge=0,
        le=1000000,
        description="Target judgments; generated judgments cover complete faculty candidate sets",
    )
    label_prefix: str = Field(default="[SYNTHETIC]", description="Mandatory synthetic labeling prefix")
    email_domain: str = Field(default="synthetic.university.edu", description="Synthetic email domain")


class SyntheticDataGenerator:
    def __init__(self, config: Optional[SyntheticConfig] = None):
        self.config = config or SyntheticConfig()
        self.rng = random.Random(self.config.seed)
        self.topics = flatten_taxonomy_tree()
        self.topic_slugs_by_domain: Dict[str, List[str]] = self._map_topics_to_domains()

    def _map_topics_to_domains(self) -> Dict[str, List[str]]:
        mapping: Dict[str, List[str]] = {}
        for root in ACADEMIC_TAXONOMY_TREE:
            domain_slug = slugify(root["name"])
            slugs: List[str] = []

            def _collect(children):
                for ch in children:
                    slugs.append(slugify(ch["name"]))
                    _collect(ch.get("children", []))

            slugs.append(domain_slug)
            _collect(root.get("children", []))
            mapping[domain_slug] = slugs
        return mapping

    def generate(self) -> BatchIngestPayload:
        self.rng = random.Random(self.config.seed)
        prefix = self.config.label_prefix
        domain_keys = list(DOMAIN_RESEARCH_TEMPLATES.keys())

        # 1. Faculty Generation
        faculty_list: List[FacultyIngestDTO] = []
        faculty_domains: List[List[str]] = []
        for i in range(1, self.config.num_faculty + 1):
            fname = self.rng.choice(FIRST_NAMES)
            lname = self.rng.choice(LAST_NAMES)
            domain_key = domain_keys[(i - 1) % len(domain_keys)]
            faculty_research_domains = [domain_key]
            if self.rng.random() < 0.25:
                secondary_domain = self.rng.choice(
                    [domain for domain in domain_keys if domain != domain_key]
                )
                faculty_research_domains.append(secondary_domain)
            faculty_domains.append(faculty_research_domains)
            domain_meta = DOMAIN_RESEARCH_TEMPLATES[domain_key]
            dept = self.rng.choice(DEPARTMENTS)
            rank = self.rng.choice(["ASSISTANT_PROFESSOR", "ASSOCIATE_PROFESSOR", "FULL_PROFESSOR"])
            lab = f"{prefix} {self.rng.choice(domain_meta['lab_names'])}"
            email = f"prof.{fname.lower()}.{lname.lower()}_{i}@{self.config.email_domain}"

            related_topics = [
                topic
                for research_domain in faculty_research_domains
                for topic in self.topics
                if topic.slug in self.topic_slugs_by_domain[research_domain]
            ]

            selected_skills = self.rng.sample(
                related_topics,
                min(len(related_topics), self.rng.randint(2, 4)),
            )
            if self.rng.random() < 0.08:
                selected_skills = []
            fac_skills = [
                FacultySkillIngestDTO(
                    topic_slug=s.slug,
                    expertise_level=self.rng.randint(2, 5),
                    is_primary_focus=(idx == 0),
                )
                for idx, s in enumerate(selected_skills)
            ]

            research_areas = " and ".join(
                domain.replace("-", " ").title()
                for domain in faculty_research_domains
            )
            bio = (
                f"{prefix} Dr. {fname} {lname} is a {rank.replace('_', ' ').title()} in {dept} "
                f"directing the {lab}. Research focuses on {research_areas}."
            )
            if self.rng.random() < 0.08:
                bio = None

            faculty_list.append(
                FacultyIngestDTO(
                    email=email,
                    first_name=f"{prefix} {fname}",
                    last_name=lname,
                    department=dept,
                    title_rank=rank,
                    office_location=f"Synthetic Hall {self.rng.randint(100, 500)}",
                    website_url=f"https://{self.config.email_domain}/~{fname.lower()}{i}",
                    lab_name=lab,
                    accepting_students=self.rng.random() > 0.15,
                    max_capacity=self.rng.randint(3, 8),
                    current_student_count=self.rng.randint(0, 3),
                    bio=bio,
                    skills=fac_skills,
                )
            )

        # 2. Student Generation
        student_list: List[StudentIngestDTO] = []
        student_domains: List[List[str]] = []
        student_profiles_complete: List[bool] = []
        for i in range(1, self.config.num_students + 1):
            fname = self.rng.choice(FIRST_NAMES)
            lname = self.rng.choice(LAST_NAMES)
            domain_key = domain_keys[(i - 1) % len(domain_keys)]
            student_research_domains = [domain_key]
            if self.rng.random() < 0.25:
                secondary_domain = self.rng.choice(
                    [domain for domain in domain_keys if domain != domain_key]
                )
                student_research_domains.append(secondary_domain)
            student_domains.append(student_research_domains)
            domain_meta = DOMAIN_RESEARCH_TEMPLATES[domain_key]
            dept = self.rng.choice(DEPARTMENTS)
            degree = self.rng.choice(["UNDERGRADUATE", "MASTERS", "PHD"])
            email = f"student.{fname.lower()}.{lname.lower()}_{i}@{self.config.email_domain}"
            research_areas = " and ".join(
                domain.replace("-", " ").title()
                for domain in student_research_domains
            )
            sop = (
                f"{prefix} {self.rng.choice(domain_meta['student_sop'])} "
                f"Primary research area: {research_areas}."
            )

            related_topics = [
                topic
                for research_domain in student_research_domains
                for topic in self.topics
                if topic.slug in self.topic_slugs_by_domain[research_domain]
            ]

            selected_skills = self.rng.sample(
                related_topics,
                min(len(related_topics), self.rng.randint(2, 4)),
            )
            profile_variant = self.rng.random()
            if profile_variant < 0.08:
                selected_skills = []
            stu_skills = [
                StudentSkillIngestDTO(
                    topic_slug=s.slug,
                    proficiency_level=self.rng.randint(1, 5),
                    interest_level=self.rng.randint(1, 5),
                    years_experience=round(self.rng.uniform(0.5, 4.0), 1),
                )
                for s in selected_skills
            ]

            # Generate 1-2 academic projects
            projects: List[ProjectIngestDTO] = []
            proj_templates = domain_meta["project_templates"]
            num_projects = self.rng.randint(1, min(2, len(proj_templates)))
            if profile_variant < 0.08 or 0.08 <= profile_variant < 0.16:
                num_projects = 0
            for p_idx in range(num_projects):
                p_title, p_desc = proj_templates[p_idx % len(proj_templates)]
                projects.append(
                    ProjectIngestDTO(
                        title=f"{prefix} {p_title} #{i}",
                        description=f"{prefix} {p_desc}",
                        role="Lead Student Researcher",
                        start_date=date(2025, 1, 15),
                        end_date=date(2025, 5, 20),
                        github_url=f"https://github.com/synthetic-student-{i}/project-{p_idx + 1}",
                        skill_slugs=[s.topic_slug for s in stu_skills[:2]],
                    )
                )

            student_bio = (
                f"{prefix} {degree.title()} student focusing on {research_areas}."
            )
            if profile_variant >= 0.90:
                student_bio = None
            student_profiles_complete.append(
                bool(student_bio and stu_skills and projects)
            )
            student_list.append(
                StudentIngestDTO(
                    email=email,
                    first_name=f"{prefix} {fname}",
                    last_name=lname,
                    department=dept,
                    degree_level=degree,
                    gpa_or_standing=round(self.rng.uniform(3.2, 4.0), 2),
                    graduation_year=self.rng.choice([2026, 2027, 2028]),
                    bio=student_bio,
                    statement_of_purpose=sop,
                    availability_status="SEEKING_ADVISOR",
                    skills=stu_skills,
                    projects=projects,
                )
            )

        # 3. Publication Generation with Co-authorship
        publication_list: List[PublicationIngestDTO] = []
        for i in range(1, self.config.num_publications + 1):
            domain_key = domain_keys[(i - 1) % len(domain_keys)]
            domain_meta = DOMAIN_RESEARCH_TEMPLATES[domain_key]
            titles = domain_meta["paper_titles"]
            abstracts = domain_meta["abstracts"]
            base_title = self.rng.choice(titles)
            base_abstract = self.rng.choice(abstracts)

            title = f"{prefix} {base_title} (Vol. {i})"
            abstract = f"{prefix} {base_abstract}"
            venue = self.rng.choice(domain_meta["venues"])
            year = self.rng.randint(2021, 2026)
            doi = f"10.synthetic/{domain_key}/2026.{i:04d}"

            # Associate authors using the assigned research domains, not formatted prose.
            domain_faculty = [
                faculty_list[idx]
                for idx, research_domains in enumerate(faculty_domains)
                if domain_key in research_domains
            ]
            if not domain_faculty:
                domain_faculty = faculty_list

            chosen_faculty = self.rng.sample(domain_faculty, min(len(domain_faculty), self.rng.randint(1, 2)))
            author_names = [f.first_name + " " + f.last_name for f in chosen_faculty]
            # Add synthetic external collaborator
            if self.rng.random() > 0.5:
                author_names.append(f"{prefix} Dr. External Collaborator")

            author_emails = [f.email for f in chosen_faculty]

            publication_list.append(
                PublicationIngestDTO(
                    title=title,
                    abstract=abstract,
                    venue=venue,
                    publication_year=year,
                    doi=doi,
                    pmid=f"SYNTH-PMID-{i:06d}",
                    arxiv_id=f"2601.{i:05d}",
                    citation_count=self.rng.randint(5, 120),
                    url=f"https://synthetic-archive.org/abs/2601.{i:05d}",
                    author_names=author_names,
                    author_faculty_emails=author_emails,
                    topic_slugs=[domain_key],
                )
            )

        # 4. Relevance Judgments Generation (Evaluation Ground Truth)
        relevance_judgments: List[RelevanceJudgmentIngestDTO] = []
        if self.config.num_relevance_judgments and faculty_list:
            target_students = min(
                len(student_list),
                ceil(self.config.num_relevance_judgments / len(faculty_list)),
            )
            grouped_students: Dict[Tuple[str, bool], List[int]] = {}
            for idx, research_domains in enumerate(student_domains):
                group = (research_domains[0], student_profiles_complete[idx])
                grouped_students.setdefault(group, []).append(idx)
            for indices in grouped_students.values():
                self.rng.shuffle(indices)

            selected_student_indices: List[int] = []
            while len(selected_student_indices) < target_students:
                added_in_round = False
                for domain in domain_keys:
                    for is_complete in (True, False):
                        group = grouped_students.get((domain, is_complete), [])
                        if group and len(selected_student_indices) < target_students:
                            selected_student_indices.append(group.pop())
                            added_in_round = True
                if not added_in_round:
                    break

            for student_idx in selected_student_indices:
                stu = student_list[student_idx]
                student_domains_set = set(student_domains[student_idx])
                student_skills = {
                    skill.topic_slug: skill.interest_level for skill in stu.skills
                }
                for faculty_idx, fac in enumerate(faculty_list):
                    faculty_domains_set = set(faculty_domains[faculty_idx])
                    faculty_skills = {
                        skill.topic_slug: skill.expertise_level for skill in fac.skills
                    }
                    shared_skill_slugs = student_skills.keys() & faculty_skills.keys()
                    strong_shared_skills = sum(
                        student_skills[slug] >= 4 and faculty_skills[slug] >= 4
                        for slug in shared_skill_slugs
                    )
                    primary_domain_match = (
                        student_domains[student_idx][0] in faculty_domains_set
                    )
                    secondary_domain_match = bool(
                        (student_domains_set & faculty_domains_set)
                        - {student_domains[student_idx][0]}
                    )

                    if primary_domain_match and strong_shared_skills >= 1:
                        grade = 3
                        reason = "shared primary domain and a high-level shared skill"
                    elif (primary_domain_match and shared_skill_slugs) or (
                        secondary_domain_match and strong_shared_skills
                    ):
                        grade = 2
                        reason = "shared research domain and technical expertise"
                    elif primary_domain_match or secondary_domain_match or shared_skill_slugs:
                        grade = 1
                        reason = "limited topical or methodological overlap"
                    else:
                        grade = 0
                        reason = "no shared research domain or taxonomy skill"

                    relevance_judgments.append(
                        RelevanceJudgmentIngestDTO(
                            student_email=stu.email,
                            faculty_email=fac.email,
                            relevance_grade=grade,
                            benchmark_suite="standard_eval_v1",
                            annotator_id="synthetic_topic_oracle",
                            notes=f"{prefix} Ground truth: {reason}.",
                        )
                    )

        return BatchIngestPayload(
            topics=self.topics,
            faculty=faculty_list,
            students=student_list,
            publications=publication_list,
            relevance_judgments=relevance_judgments,
        )
