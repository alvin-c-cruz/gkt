from flask import Blueprint, render_template, current_app, g
from .. user import login_required


bp = Blueprint('main', __name__, template_folder="pages")


@bp.route("/")
@login_required
def home():
    context = {}

    return render_template("main/home.html", **context)


@bp.before_app_request
def set_g():
    g.company_name = current_app.config["COMPANY_NAME"]
    # g.user_nav = current_app.config["NAVIGATIONS"]