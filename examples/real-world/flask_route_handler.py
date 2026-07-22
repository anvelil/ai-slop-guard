# Excerpt adapted from pallets/flask, examples/tutorial/flaskr/blog.py
# (BSD-3-Clause). Reproduced here only as a minimal illustration of a
# real pattern the checker had to learn to handle -- see
# benchmarks/README.md for the full story.

from flask import Blueprint

bp = Blueprint("blog", __name__)


@bp.route("/")
def index():
    return "recent posts"
