from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import current_user
from dataclasses import dataclass
import datetime
from sqlalchemy.exc import IntegrityError
from .models import Disbursement as Obj
from .models import DisbursementDetail as ObjDetail
from .forms import Form
from .. account import Account
from .. vendor import Vendor
from application.extensions import db, month_first_day, month_last_day, next_control_number 
from .extensions import create_journal
from .. user import login_required, roles_accepted
from . import app_name, app_label


bp = Blueprint(app_name, __name__, template_folder="pages", url_prefix=f"/{app_name}")
ROLES_ACCEPTED = app_label


@bp.route("/journal", methods=["POST", "GET"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def journal():
    if request.method == "POST":
        date_from = request.form.get("date_from")
        date_to = request.form.get("date_to")
    else:
        date_from = month_first_day()
        date_to = month_last_day()

    records = Obj.query.filter(
        Obj.record_date.between(date_from, date_to)).order_by(
        Obj.record_date.desc(), Obj.id.desc()
        ).all()
           
    rows = create_journal(records)

    context = {
        "rows": rows,
        "date_from": date_from,
        "date_to": date_to,
    }

    return render_template(f"{app_name}/journal.html", **context)


@bp.route("/", methods=["POST", "GET"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def home():
    if request.method == "POST":
        date_from = request.form.get("date_from")
        date_to = request.form.get("date_to")
    else:
        date_from = month_first_day()
        date_to = month_last_day()

    rows = Obj.query.filter(
        Obj.record_date.between(date_from, date_to)).order_by(
        Obj.record_date.desc(), Obj.id.desc()
        ).all()
        

    context = {
        "rows": rows,
        "date_from": date_from,
        "date_to": date_to,
    }

    return render_template(f"{app_name}/home.html", **context)


@bp.route("/add", methods=["POST", "GET"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def add():
    vendor_dropdown = [{"id": vendor.id, "vendor_name": vendor.vendor_name} for vendor in Vendor.query.order_by('vendor_name').all()]
    account_dropdown = [{"id": account.id, "account_name": account.account_name} for account in Account.query.order_by('account_number').all()]
    
    if request.method == "POST":
        form = Form()
        form._post(request.form)

        if form._validate_on_submit():
            form.user_prepare_id = current_user.id
            form._save()
            flash(f"{getattr(form, f'record_number')} has been added.", category="success")
            return redirect(url_for(f'{app_name}.edit', record_id=form.id))

    else:
        form = Form()
        today = str(datetime.date.today())[:10]
        form.record_date = today

        form.record_number = next_control_number(
            obj=Obj, 
            control_number_field="record_number"
            )
        
        last_entry = Obj.query.order_by(Obj.id.desc()).first()

        if last_entry:
            form.prepared_by = last_entry.prepared_by
            form.checked_by = last_entry.checked_by
            form.approved_by = last_entry.approved_by

    context = {
        "form": form,
        "vendor_dropdown": vendor_dropdown,
        "account_dropdown": account_dropdown,

    }

    return render_template(f"{app_name}/form.html", **context)


@bp.route("/edit/<int:record_id>", methods=["POST", "GET"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def edit(record_id):     
    record = Obj.query.get_or_404(record_id)

    if request.method == "POST":
        form = Form()
        form._post(request.form)

        if form._validate_on_submit():
            cmd_button = request.form.get("cmd_button")
            if cmd_button == "Submit for Printing":
                form._submit()

            form.user_prepare_id = current_user.id
            form._save()

            if cmd_button == "Submit for Printing":
                flash(f"{getattr(form, f'record_number')} has been submitted for printing.", category="success")
                return redirect(url_for(f'{app_name}.edit', record_id=form.id))
            elif cmd_button == "Save Draft":
                flash(f"{getattr(form, f'record_number')} has been updated.", category="success")
                return  redirect(url_for(f'{app_name}.edit', record_id=form.id))

    else:
        form = Form()
        form._populate(record)

    context = {
        "form": form,
    }

    return render_template(f"{app_name}/form.html", **context)


@bp.route("/view/<int:record_id>", methods=["POST", "GET"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def view(record_id):   
    vendor_dropdown = [{"id": vendor.id, "vendor_name": vendor.vendor_name} for vendor in Vendor.query.order_by('vendor_name').all()]
    account_dropdown = [{"id": account.id, "account_name": account.account_name} for account in Account.query.order_by('account_number').all()]

    record = Obj.query.get_or_404(record_id)

    if request.method == "POST":
        flash("Record is locked for editting. Contact your administrator.", category="error")

    form = Form()
    form._populate(record)

    context = {
        "form": form,
        "vendor_dropdown": vendor_dropdown,
        "account_dropdown": account_dropdown,
    }

    return render_template(f"{app_name}/form.html", **context)


@bp.route("/delete/<int:record_id>", methods=["POST", "GET"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def delete(record_id):
    if not current_user.admin:
        flash("Administrator rights is required to conduct this activity.", category="error")
        return redirect(url_for(f"{app_name}.home"))

    obj = Obj.query.get_or_404(record_id)
    details = ObjDetail.query.filter(getattr(ObjDetail, f"{app_name}_id")==record_id).all()
    preparer = obj.preparer

    try:
        db.session.delete(preparer)
        for detail in details:
            db.session.delete(detail)
        db.session.delete(obj)
        db.session.commit()
        flash(f"{getattr(obj, f'record_number')} has been deleted.", category="success")
    except IntegrityError:
        db.session.rollback()
        flash(f"Cannot delete {obj} because it has related records.", category="error")

    return redirect(url_for(f'{app_name}.home'))


@bp.route("/unlock/<int:record_id>", methods=["POST", "GET"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def unlock(record_id):
    if not current_user.admin:
        flash("Administrator rights is required to conduct this activity.", category="error")
        return redirect(url_for(f"{app_name}.home"))

    obj = Obj.query.get_or_404(record_id)
    obj.submitted = ""
    obj.cancelled = ""

    db.session.commit()
    flash(f"{getattr(obj, f'record_number')} has been unlocked.", category="success")

    return redirect(url_for(f'{app_name}.edit', record_id=record_id))


@bp.route("/cancel/<int:record_id>", methods=["POST", "GET"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def cancel(record_id):   
    obj = Obj.query.get_or_404(record_id)
    obj.cancelled = str(datetime.datetime.today())[:10]
    db.session.commit()
    flash(f"{getattr(obj, f'record_number')} has been cancelled.", category="success")

    return redirect(url_for(f'{app_name}.home'))


@bp.route("/print/<int:record_id>", methods=["GET"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def print(record_id):   
    obj = Obj.query.get_or_404(record_id)
    
    context = {
        "obj": obj,
    }

    # return render_template("in_progress.html")
    return render_template(f"{app_name}/print.html", **context)


