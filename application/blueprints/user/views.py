from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user
from functools import wraps
from werkzeug.security import generate_password_hash

from .models import User, Role, UserRole
from .forms import LoginForm, UserForm

from application.extensions import db


bp = Blueprint("user", __name__, template_folder="pages", url_prefix="/user")


def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('user.login'))
        
        if not current_user.is_active():
            return redirect(url_for("user.inactive"))
                
        return func(*args, **kwargs)
    return decorated_view


def roles_accepted(roles=[]):
    def decorator(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not any(role in roles for role in current_user.user_roles):
                flash("You are not allowed to access this area.", category="error")
                return redirect(url_for('main.home')) 
            return func(*args, **kwargs)
        return decorated_view
    return decorator  


@bp.route("/")
@login_required
def home():
    return "User profile"


@bp.route("/list")
@login_required
@roles_accepted(['user'])
def user_list():
    users = User.query.order_by('user_name').all()
    context = {
        "rows": users,
    }
    return render_template("user/user_list.html", **context)


@bp.route("/user_group/<int:record_id>")
@login_required
@roles_accepted(['user'])
def user_group(record_id):
    user = User.query.get(record_id)
    roles = Role.query.order_by('role_name').all()
    context = {
        "user": user,
        "roles": roles
    }
    return render_template("user/user_group.html", **context)


@bp.route("user_admin")
@login_required
@roles_accepted(['user'])
def user_admin():
    user_id = request.args.get('user_id')
    value = int(request.args.get("value"))
    
    user = User.query.get(user_id)
    if user.user_name != "admin":
        user.admin = value
        db.session.commit()
    else:
        flash("Cannot change super admin status", category="error")
    
    return redirect(url_for('user.user_group', record_id=user_id))


@bp.route("user/active")
@login_required
@roles_accepted(['user'])
def user_active():
    user_id = request.args.get('user_id')
    value = int(request.args.get("value"))
    
    user = User.query.get(user_id)
    if user.user_name != "admin":
        user.active = value   
        db.session.commit()
    else:
        flash("Cannot change super admin status", category="error")
    
    return redirect(url_for('user.user_group', record_id=user_id))


@bp.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect("/")
    
    if request.method == "POST":
        form = LoginForm()
        form.post(request.form)
        
        if form.validate():
            user = User.query.filter_by(user_name=form.user_name).first()
            if user:
                if user.check_pass_word(form.pass_word):
                    login_user(user)
                    flash(f"Welcome {user.user_name}.", category="success")
                    return redirect("/")
                
            flash("Invalid username / password.", category="error")
    else:
        form = LoginForm()
    
    check_roles()
    
    context = {
        "form": form,
    }
    return render_template("user/login.html", **context)


@bp.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        form = UserForm()
        form.post(request.form)
        if form.validate():
            user = User(
                user_name=form.user_name,
                first_name=form.first_name,
                middle_name=form.middle_name,
                last_name=form.last_name,
                email=form.email
            )
            
            if form.user_name == "admin":
                user.active = True
                user.admin = True                
                
            user.set_pass_word(form.pass_word)
            
            db.session.add(user)
            db.session.commit()
            
            if form.user_name == "admin":
                if not Role.query.all():
                    check_roles()
                
                role = Role.query.filter_by(role_name="user").first()
                                    
                user_role = UserRole(
                    user_id=user.id,
                    role_id=role.id
                )
                
                db.session.add(user_role)
                db.session.commit()               
            
            login_user(user)
            flash(f"Welcome {user.user_name}.", category="success")
            return redirect(url_for("user.inactive"))
        
    else:
        form = UserForm()
    
    context = {
        "form": form
    }
    return render_template("user/register.html", **context)


@bp.route("/change_password", methods=["POST", "GET"])
@login_required
def change_password():
    if not current_user.admin:
        flash("Admin rights required", category="error")
        return redirect(url_for('main.home'))
    

    if request.method == "POST":
        form = UserForm()
        form.post(request.form)

        user = User.query.filter_by(user_name=form.user_name).first()

        if not user:
            flash("User does not exists.", category="error")
        elif form.pass_word != form.confirm_pass_word:
            flash("Password is not identical.", category="error")
        else:              
            form.id = user.id
            user.set_pass_word(form.pass_word)
            db.session.commit()
            
            flash(f"Password has changed.", category="success")
            return redirect(url_for("main.home"))
        
    else:
        form = UserForm()
    
    context = {
        "form": form
    }
    return render_template("user/change_password.html", **context)


@bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("User logged out.", category="success")
        
    return redirect(url_for('user.login'))


@bp.route("/inactive")
def inactive():
    if current_user.is_active():
        return redirect("/")
    
    return render_template("user/inactive.html")


@bp.route("/add_role")
@login_required
@roles_accepted(['user'])
def add_role():
    user_id = int(request.args.get("user_id"))
    role_id = int(request.args.get("role_id"))
    
    user_role = UserRole(
        user_id=user_id,
        role_id=role_id
    )
    
    db.session.add(user_role)
    db.session.commit()
    
    return redirect(url_for('user.user_group', record_id=user_id))
    
@bp.route("/remove_role")
@login_required
@roles_accepted(['user'])
def remove_role():
    user_id = int(request.args.get("user_id"))
    role_id = int(request.args.get("role_id"))
    
    user = User.query.get(user_id)
    role = Role.query.get(role_id)
    
    if user.user_name == 'admin' and role.role_name == 'user':
        flash("Cannot remove user role for super admin", category='error')
    else:
        user_role = UserRole.query.filter_by(
            user_id=user_id,
            role_id=role_id
        ).first()
        
        db.session.delete(user_role)
        db.session.commit()
    
    return redirect(url_for('user.user_group', record_id=user_id))


def check_roles():
    from application import blueprints
    modules = [
        getattr(blueprints, module) 
        for module in dir(blueprints) if hasattr(getattr(blueprints, module),"bp")
        ]
    role_names = ['user']
    for module in modules:
        if hasattr(module,"menu_label"):
            role_names.append(getattr(module,"menu_label")[2])
    
    for role_name in role_names:
        role = Role.query.filter_by(role_name=role_name).first()
        if not role:
            role = Role(role_name=role_name)
            db.session.add(role)
            db.session.commit()
