from flask import Blueprint, jsonify, request
from eduforge.models import db
from eduforge.models.course import Course

bp = Blueprint("courses", __name__, url_prefix="/courses")


@bp.route("/", methods=["GET"])
def list_courses():
    courses = Course.query.all()
    return jsonify([{"id": c.id, "title": c.title, "description": c.description} for c in courses])


@bp.route("/", methods=["POST"])
def create_course():
    data = request.get_json()
    course = Course(title=data["title"], description=data.get("description", ""))
    db.session.add(course)
    db.session.commit()
    return jsonify({"id": course.id, "title": course.title}), 201


@bp.route("/<int:course_id>", methods=["GET"])
def get_course(course_id):
    course = db.get_or_404(Course, course_id)
    return jsonify({
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "lessons": [{"id": l.id, "title": l.title, "order": l.order} for l in course.lessons],
    })
