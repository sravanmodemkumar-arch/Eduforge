from flask import Blueprint, jsonify

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return jsonify({"name": "Eduforge", "version": "0.1.0", "status": "running"})


@bp.route("/health")
def health():
    return jsonify({"status": "ok"})
