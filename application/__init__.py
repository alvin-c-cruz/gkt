from flask import Flask, request, redirect, url_for, abort, g

from pathlib import Path
from http import HTTPStatus

from . extensions import db, bcrypt, mail, migrate, login_manager
from . blueprints.user import User
from . import blueprints


def navigations():
    user_nav = {}

    options = "main/option_menu.html"

    plastic_product_component = "plastic_product_component/dropdown_menu.html"
    plastic_label = "plastic_label/dropdown_menu.html"
    product = "product/dropdown_menu.html"

    lithography = "lithography/dropdown_menu.html"

    user_nav["admin"] = user_nav["Salve"] = [
        product,
        plastic_product_component,
        plastic_label,
        lithography,
        options,
        ]
    
    # user_nav["alvin"] = [
    #     product,
    #     options,
    #     ]
    
    user_nav["Sofia"] = [
        product,
        options,
        ]
    
    user_nav["WARLITOFUENTES"] = [
        product,
        options,
        ]
    
    # user_nav["Arvie"] = [
    #     plastic_label,
    #     options,
    #     ]
    
    user_nav["chaynamey"] = [
        lithography,
        options,
        ]
    
    user_nav["pat"] = [
        plastic_product_component,
        lithography,
        options,
        ]
    
    return user_nav

def create_app(test=False):
    app = Flask(__name__, instance_relative_config=True)
    if test:
        app.config.from_pyfile('test_config.py')
    else:
        app.config.from_pyfile('config.py')

    app.config['NAVIGATIONS'] = navigations()

    instance_path = Path(app.instance_path)
    parent_directory = Path(instance_path.parent)
    if not parent_directory.is_dir():
        parent_directory.mkdir()
    
    if not instance_path.is_dir():
        instance_path.mkdir()
    
    
    
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.blueprint == 'api':
            abort(HTTPStatus.UNAUTHORIZED)
        return redirect(url_for('user.login'))
    
    
    # Register Blueprints
    modules = [
        getattr(blueprints, module) 
        for module in dir(blueprints) if hasattr(getattr(blueprints, module),"bp")
        ]

    menu_list = []
    for module in modules:
        app.register_blueprint(getattr(module, "bp"))
        if hasattr(module, "menu_label"):
            menu_list.append(getattr(module, "menu_label"))
        

    app.config['MENUS'] = menu_list

    # Initialize the database
    bcrypt.init_app(app)
    mail.init_app(app)
    db.init_app(app)
    migrate.init_app(app=app, db=db)
    
    return app
