from application.extensions import db
from .admin_models import AdminAccount as ObjAdmin
from .admin_models import UserAccount as ObjUser
from . import app_name

class Account(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    account_number = db.Column(db.String(255))
    account_title = db.Column(db.String(255))
    account_description = db.Column(db.String(255))

    def __str__(self):
        return f"{self.account_number}: {self.account_title}"
    
    @property
    def preparer(self):
        obj = ObjUser.query.filter(getattr(ObjUser,f"{app_name}_id")==self.id).first()
        return obj
    
    @property
    def approved(self):
        obj = ObjAdmin.query.filter(getattr(ObjAdmin,f"{app_name}_id")==self.id).first()
        return obj
    
    @property
    def account_name(self):
        return f"{self.account_number}: {self.account_title}"

