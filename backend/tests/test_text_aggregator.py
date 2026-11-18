"""Tests for the text aggregator: profile composition for students, faculty,
publications, and projects.
"""

import uuid
from unittest.mock import MagicMock
import pytest
from backend.app.embeddings.text_aggregator import (
    compose_faculty_profile_text,
    compose_project_text,
    compose_publication_text,
    compose_student_profile_text,
)


class TestStudentProfileText:
    def _make_student(self, **kwargs):
        student = MagicMock()
        student.statement_of_purpose = kwargs.get(
            "sop", "I want to research reinforcement learning for autonomous systems."
        )
        student.bio = kwargs.get("bio", "Third-year PhD student with experience in robotics.")
        student.department = kwargs.get("department", "Computer Science")
        student.degree_level = kwargs.get("degree_level", "PHD")
        student.skills_interests = kwargs.get("skills", [])
        student.academic_projects = kwargs.get("projects", [])
        return student

    def _make_skill(self, name):
        skill = MagicMock()
        skill.topic_skill = MagicMock()
        skill.topic_skill.name = name
        return skill

    def _make_project(self, title, desc, role=None):
        proj = MagicMock()
        proj.title = title
        proj.description = desc
        proj.role = role
        return proj

    def test_basic_composition(self):
        student = self._make_student()
        text = compose_student_profile_text(student)
        assert "reinforcement learning" in text.lower()
        assert "robotics" in text.lower()
        assert "computer science" in text.lower()

    def test_includes_skills(self):
        skills = [self._make_skill("Machine Learning"), self._make_skill("PyTorch")]
        student = self._make_student(skills=skills)
        text = compose_student_profile_text(student)
        assert "machine learning" in text.lower()
        assert "pytorch" in text.lower()

    def test_includes_projects(self):
        projects = [self._make_project("RL Navigator", "Built an RL-based path planner", "Lead")]
        student = self._make_student(projects=projects)
        text = compose_student_profile_text(student)
        assert "rl navigator" in text.lower()
        assert "path planner" in text.lower()

    def test_empty_student(self):
        student = self._make_student(sop="", bio="", department="", degree_level="")
        text = compose_student_profile_text(student)
        # Should return empty string for minimal data
        assert isinstance(text, str)


class TestFacultyProfileText:
    def _make_faculty(self, **kwargs):
        fac = MagicMock()
        fac.bio = kwargs.get("bio", "Expert in deep learning and neural architecture search.")
        fac.lab_name = kwargs.get("lab", "Neural Architecture Lab")
        fac.department = kwargs.get("department", "Computer Science")
        fac.title_rank = kwargs.get("rank", "FULL_PROFESSOR")
        fac.skills_expertise = kwargs.get("expertise", [])
        return fac

    def _make_pub(self, title, abstract):
        pub = MagicMock()
        pub.title = title
        pub.abstract = abstract
        return pub

    def _make_expertise(self, name):
        exp = MagicMock()
        exp.topic_skill = MagicMock()
        exp.topic_skill.name = name
        return exp

    def test_basic_composition(self):
        fac = self._make_faculty()
        text = compose_faculty_profile_text(fac)
        assert "deep learning" in text.lower()
        assert "neural architecture lab" in text.lower()

    def test_includes_publications(self):
        pubs = [self._make_pub("NAS via Efficient Search", "We propose a fast NAS algorithm.")]
        fac = self._make_faculty()
        text = compose_faculty_profile_text(fac, publications=pubs)
        assert "nas" in text.lower()

    def test_includes_expertise(self):
        expertise = [self._make_expertise("Deep Learning"), self._make_expertise("AutoML")]
        fac = self._make_faculty(expertise=expertise)
        text = compose_faculty_profile_text(fac)
        assert "automl" in text.lower()

    def test_publication_cap(self):
        """Should not include more than 8 publications to avoid overly long documents."""
        pubs = [self._make_pub(f"Paper {i}", f"Abstract {i}") for i in range(15)]
        fac = self._make_faculty()
        text = compose_faculty_profile_text(fac, publications=pubs)
        # Count how many "Publication -" markers appear
        count = text.lower().count("publication -")
        assert count <= 8


class TestPublicationText:
    def test_basic_composition(self):
        pub = MagicMock()
        pub.title = "Attention Is All You Need"
        pub.abstract = "We propose the Transformer architecture."
        pub.venue = "NeurIPS"
        text = compose_publication_text(pub)
        assert "attention" in text.lower()
        assert "transformer" in text.lower()
        assert "neurips" in text.lower()

    def test_missing_venue(self):
        pub = MagicMock()
        pub.title = "Test Paper"
        pub.abstract = "Abstract content."
        pub.venue = None
        text = compose_publication_text(pub)
        assert "test paper" in text.lower()
        assert "venue" not in text.lower()


class TestProjectText:
    def test_basic_composition(self):
        proj = MagicMock()
        proj.title = "Autonomous Drone Navigation"
        proj.description = "Built a drone navigation system using SLAM."
        proj.role = "Lead Developer"
        proj.skills = []
        text = compose_project_text(proj)
        assert "autonomous drone" in text.lower()
        assert "slam" in text.lower()
        assert "lead developer" in text.lower()

    def test_with_skills(self):
        proj = MagicMock()
        proj.title = "Test Project"
        proj.description = "Description"
        proj.role = None
        skill = MagicMock()
        skill.name = "ROS2"
        proj.skills = [skill]
        text = compose_project_text(proj)
        assert "ros2" in text.lower()
