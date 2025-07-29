from dataclasses import dataclass
import re
from sqlalchemy import func

from .models import User


@dataclass
class UserForm:
    id: int = 0
    user_name: str = ""
    pass_word: str = ""
    confirm_pass_word: str = ""
    first_name: str = ""
    middle_name: str = ""
    last_name: str = ""
    email: str = ""
    
    errors = {}
    
    def post(self, request_form):
        self.user_name = request_form.get("user_name")
        self.pass_word = request_form.get("pass_word")
        self.confirm_pass_word = request_form.get("confirm_pass_word")
        self.first_name = request_form.get("first_name")
        self.middle_name = request_form.get("middle_name")
        self.last_name = request_form.get("last_name")
        self.email = request_form.get("email")
        
    def validate(self):
        self.errors = {}
        
        if not self.user_name: 
            self.errors["user_name"] = "Please type username."
        elif not self.is_valid_char(self.user_name):
            self.errors["user_name"] = "User alpha-numeric and underscore for username."
        else:
            user = User.query.filter(
                func.upper(User.user_name) == func.upper(self.user_name),
                User.id != self.id).first()
            if user:
                self.errors["user_name"] = "Username is already taken. Please choose another one."

            
        if not self.pass_word:
            self.errors["pass_word"] = "Please type password."
        elif len(self.pass_word) < 6:
            self.errors["pass_word"] = "Password should be at least six (6) characters."
        
        if not self.confirm_pass_word:
            self.errors["confirm_pass_word"] = "Please re-type password."
        elif self.pass_word != self.confirm_pass_word:
            self.errors["confirm_pass_word"] = "Passwords does not match."
            
        if not self.first_name: self.errors["first_name"] = "Please type first name."
        if not self.last_name: self.errors["last_name"] = "Please type last name."
        
        if not self.errors:
            return True
        
    def is_valid_char(self, value):
        # Regular expression pattern to match valid Excel sheet names
        pattern = re.compile(r'^[a-zA-Z0-9_.]*([a-zA-Z0-9_.]+$)')
        return pattern.match(value) is not None


@dataclass
class LoginForm:
    user_name: str = ""
    pass_word: str = ""
    
    errors = {}
    
    def post(self, request_form):
        self.user_name = request_form.get("user_name") if request_form.get("user_name") else ""
        self.pass_word = request_form.get("pass_word") if request_form.get("pass_word") else ""

    def validate(self):
        self.errors = {}
        if not self.user_name: 
            self.errors["user_name"] = "Please type username."
        if not self.pass_word: self.errors["pass_word"] = "Please type password."
        if not self.errors: return True
        