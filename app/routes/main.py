from flask import Blueprint, render_template

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/analysis")
def redirect_to_summary():
    from flask import redirect, url_for

    return redirect(url_for("time_summary.show_summary"))
