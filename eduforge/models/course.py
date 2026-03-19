from eduforge.models import db


class Course(db.Model):
    """Represents an educational course."""

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    lessons = db.relationship("Lesson", backref="course", lazy=True)

    def __repr__(self):
        return f"<Course {self.title}>"
