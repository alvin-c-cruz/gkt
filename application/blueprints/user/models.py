import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, current_app

from application.extensions import db


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String())
    
    def __str__(self):
        return self.role_name
    

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String())
    pass_word = db.Column(db.String())
    first_name = db.Column(db.String())
    middle_name = db.Column(db.String())
    last_name = db.Column(db.String())
    email = db.Column(db.String())
    admin = db.Column(db.Boolean(), default=False)
    staff = db.Column(db.Boolean(), default=False)
    active = db.Column(db.Boolean(), default=False)
    salt = db.Column(db.String())
    
    def __str__(self):
        return self.first_name + " " + self.last_name
    
    def set_pass_word(self, pass_word):
        salt = os.urandom(16)
        salted_password = f"{salt}{pass_word}"
        self.salt = salt
        self.pass_word = generate_password_hash(salted_password)
        
    def check_pass_word(self, pass_word):
        salted_pass_word = f"{self.salt}{pass_word}"
        return check_password_hash(self.pass_word, salted_pass_word)
    
    def is_active(self):
        return self.active
    
    def get_id(self):
        return self.id
    
    def is_authenticated(self):
        if 'user_id' in session: return True
        
    @property
    def user_roles(self):
        return [user_role.role.role_name for user_role in self.roles]
    
    @property
    def menus(self):
        return current_app.config['MENUS']


class UserRole(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    user = db.relationship('User', backref='roles', lazy=True)
    
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), primary_key=True)
    role = db.relationship('Role', backref='users', lazy=True)
