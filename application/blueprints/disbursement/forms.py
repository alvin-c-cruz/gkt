from dataclasses import dataclass
from sqlalchemy import func
from application.extensions import db
from .models import Disbursement as Obj
from .models import DisbursementDetail as ObjDetail
from .admin_models import UserDisbursement as Preparer
from datetime import datetime
from . import app_name

from .. account import Account
from .. vendor import Vendor


DETAIL_ROWS = 20


def get_attributes(object):
    attributes = [x for x in dir(object) if (not x.startswith("_"))]
    exceptions = (
        "user_prepare_id", 
        "user_prepare", 
        "errors", 
        "active", 
        "details",
        "locked", 
        app_name,
        )
    for i in exceptions:
        try:
            attributes.remove(i)
        except ValueError:
            pass
    return attributes


def get_attributes_as_dict(object):
    attributes = get_attributes(object)
    return {
        attribute: getattr(object, attribute)
        for attribute in attributes
    }


@dataclass
class SubForm:
    id: int = 0
    disbursement_id:int = 0
    account_id: int = 0
    debit: float = 0
    credit: float = 0
    side_note: str = ""

    account_name: str = ""

    errors = {}

    def _populate(self, row):
        for attribute in get_attributes(self):
            if attribute in ["errors", "amount", "account_name"]:
                continue
            elif attribute in ["account_id"]:
                account = Account.query.get(getattr(row, "account_id"))
                setattr(self, attribute, account.id)
                self.account_name = account.account_name
            elif attribute in ["debit", "credit"]:
                setattr(self, attribute, float(getattr(row, attribute)))
            else:
                setattr(self, attribute, getattr(row, attribute))

    def _validate(self):
        self.errors = {}

        if self._is_dirty():            
            if self.debit < 0:
                self.errors["debit"] = "Debit cannot be less than zero (0)."

            if self.credit < 0:
                self.errors["credit"] = "Credit cannot be less than zero (0)."

            if not self.account_name:
                self.errors["account_name"] = "Please select account title."
            else:
                account_number, account_title = self.account_name.split(": ")
                account = Account.query.filter(Account.account_number==account_number).first()
                if not account:
                    self.errors["account_name"] = f"{self.account_name} does not exists."
                else:
                    self.account_id = account.id

        if not self.errors:
            return True
        else:
            return False    

    def _is_dirty(self):
        return any([
            self.account_name, 
            self.debit, 
            self.credit, 
            self.side_note
            ])    
        

@dataclass
class Form:
    id: int = None
    record_date: str = ""
    record_number: str = ""
    vendor_id: int = 0
    ap_number: str = ""
    po_number: str = ""
    prepared_by: str = ""
    checked_by: str = ""
    approved_by: str = ""
    description: str = ""

    submitted: str = ""
    cancelled: str = ""
    locked: bool = False

    user_prepare_id: int = None
    
    vendor_name: str = ""

    details = []
    errors = {}

    def __post_init__(self):
        self.details = []
        for i in range(DETAIL_ROWS):
            self.details.append((i, SubForm()))

    def _save(self):
        if self.id is None:
            # Add a new record
            _dict = get_attributes_as_dict(self)
            if "locked" in _dict: _dict.pop("locked")
            _dict.pop("vendor_name")
            
            new_record = Obj(
                **_dict
                )
            db.session.add(new_record)
            db.session.commit()

            self.id = new_record.id

            for _, detail in self.details:
                if detail._is_dirty():
                    _dict = get_attributes_as_dict(detail)
                    _dict.pop("id")
                    _dict.pop("account_name")
                    _dict[f"{app_name}_id"] = new_record.id
                    new_detail = ObjDetail(**_dict)
                    db.session.add(new_detail)
                    db.session.commit()
            
            data = {
                f"{app_name}_id": new_record.id,
                "user_id": self.user_prepare_id
            }
            
            preparer = Preparer(**data)

            db.session.add(preparer)
            db.session.commit()

        else:
            # Update an existing record
            record = Obj.query.get(self.id)
            if record:
                data = {
                    f"{app_name}_id": self.id
                }
                preparer = Preparer.query.filter_by(**data).first()
                preparer.user_id = self.user_prepare_id

                for attribute in get_attributes(self):
                    if attribute == "id": continue
                    setattr(record, attribute, getattr(self, attribute))
                                    
                details = ObjDetail.query.filter(
                    getattr(ObjDetail, f"{app_name}_id")==self.id
                    )
                
                for detail in details:
                    db.session.delete(detail)

                for _, detail in self.details:
                    if detail._is_dirty():
                        _dict = get_attributes_as_dict(detail)
                        _dict.pop("id")
                        _dict.pop("account_name")
                        _dict[f"{app_name}_id"] = record.id
                        row_detail = ObjDetail(**_dict)
                        db.session.add(row_detail)
                
        db.session.commit()
   
    def _populate(self, obj):
        for attribute in get_attributes(self):
            if attribute in ["vendor_id"]:
                setattr(self, attribute, int(getattr(obj, attribute)))
                vendor = Vendor.query.get(getattr(obj, attribute))
                self.vendor_name = vendor.vendor_name
            elif attribute == "vendor_name":
                pass
            elif attribute in ("debit", "credit"):
                setattr(self, attribute, float(getattr(obj, attribute)))
            else:
                setattr(self, attribute, getattr(obj, attribute))

        for i, row in enumerate(getattr(obj, f"{app_name}_details")):
            subform = SubForm()
            subform._populate(row)
            self.details[i] = (i, subform)

    def _post(self, request_form):
        for attribute in get_attributes(self):
            if attribute == "id":
                value = getattr(request_form, "get")("record_id")
                if value:
                    setattr(self, "id", int(value))
            elif attribute in ["vendor_id"]:
                vendor_name = request_form.get('vendor_name')
                vendor = Vendor.query.filter_by(
                    vendor_name=vendor_name
                    ).first()
                if vendor:
                    setattr(self, attribute, vendor.id)
                self.vendor_name = vendor_name

            elif attribute in ("submitted", "cancelled"):
                continue
            else:
                setattr(self, attribute, getattr(request_form, "get")(attribute))

        for i in range(DETAIL_ROWS):
            for attribute in ["account_name"] + get_attributes(ObjDetail):
                if attribute in ("debit", "credit"):
                    if type(request_form.get(f'{attribute}-{i}')) == str:
                        _value = request_form.get(f'{attribute}-{i}')
                        if _value.isnumeric() or (_value.replace('.', '', 1).isdigit() and _value.count('.') <= 1):
                            setattr(self.details[i][1], attribute, float(_value))
                        else:
                            setattr(getattr(self.details[i][1], attribute), 0)
                    else: 
                        setattr(getattr(self.details[i][1], attribute), float(request_form.get(f'{attribute}-{i}')))
                elif attribute in ["account_name"]:
                    account_name = request_form.get(f'account_name-{i}')
                    setattr(self.details[i][1], attribute, account_name)
                    if account_name:
                        account = Account.query.filter_by(account_name=account_name).first()
                        if account:
                            setattr(self.details[i][1], "account_id", account.id)
                elif attribute in ["side_note"]:
                    setattr(self.details[i][1], attribute, request_form.get(f'{attribute}-{i}'))
                else:
                    continue

    def _validate_on_submit(self):
        self.errors = {}
        detail_validation = True

        if not self.record_date:
            self.errors["record_date"] = "Please type date."

        if not self.record_number:
            self.errors["record_number"] = "Please type disbursement number."
        else:
            duplicate = Obj.query.filter(
                func.lower(
                    Obj.record_number
                    ) == func.lower(self.record_number), 
                    Obj.id != self.id
                    ).first()
            if duplicate:
                self.errors["record_number"] = "Disbursment number is already used, please verify."        

        if not self.vendor_name:
            self.errors["vendor_name"] = "Please type vendor."
        else:
            vendor = Vendor.query.filter(Vendor.vendor_name==self.vendor_name).first()
            if not vendor:
                self.errors["vendor_name"] = f"{self.vendor_name} does not exists."


        for i in range(DETAIL_ROWS):
            if not self.details[i][1]._validate():
                detail_validation = False

        all_not_dirty = True
        for _, detail in self.details:
            if detail._is_dirty():
                all_not_dirty = False

        if all_not_dirty:
            self.errors["entry"] = "There should be at least one entry."       

        if not self.errors and detail_validation:
            return True        
    
    def _submit(self):
        self.submitted = str(datetime.today())[:10]

    @property
    def _locked_(self):
        if self.submitted or self.cancelled:
            return True
        else:
            return False
    