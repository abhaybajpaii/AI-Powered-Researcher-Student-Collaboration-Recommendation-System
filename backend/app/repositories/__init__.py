from backend.app.repositories.base import BaseRepository
from backend.app.repositories.student_repo import student_repo, StudentRepository
from backend.app.repositories.faculty_repo import faculty_repo, FacultyRepository

__all__ = [
    "BaseRepository",
    "student_repo",
    "StudentRepository",
    "faculty_repo",
    "FacultyRepository",
]
