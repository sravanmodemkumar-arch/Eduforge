from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from eduforge.models.course import Course
from eduforge.models.lesson import Lesson

__all__ = ["db", "Course", "Lesson"]
