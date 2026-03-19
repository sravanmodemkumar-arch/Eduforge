from eduforge.models import db


class Lesson(db.Model):
    """Represents a lesson within a course."""

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)

    def __repr__(self):
        return f"<Lesson {self.title}>"
