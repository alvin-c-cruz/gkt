from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from datetime import datetime, timedelta
from flask_login import LoginManager

db = SQLAlchemy()
mail = Mail()
bcrypt = Bcrypt()
migrate = Migrate()
login_manager = LoginManager()


def year_first_day():
    date_today = datetime.today()
    year = date_today.year
    month = 1
    day = 1
    first_day = str(datetime(year, month, day))[:10]

    return first_day


def month_first_day():
    date_today = datetime.today()
    year = date_today.year
    month = date_today.month
    day = 1
    first_day = str(datetime(year, month, day))[:10]

    return first_day


def year_last_day():
    date_today = datetime.today()
    year = date_today.year
    month = 12
    day = 31
    first_day = str(datetime(year, month, day))[:10]

    return first_day


def month_last_day():
    date_today = datetime.today()
    year = date_today.year
    month = date_today.month
    if month == 12:
        year += 1
        month = 1
    else:
        month += 1
    day = 1

    first_day_of_next_month = datetime(year, month, day)
    last_day = first_day_of_next_month - timedelta(days=1)
    last_day = str(last_day)[:10]

    return last_day


def next_control_number(obj, control_number_field, record_date=None):
    record = obj.query.order_by(getattr(obj, control_number_field).desc()).first()
    
    if not record:
        return "00001"

    last_number = getattr(record, control_number_field)
    
    length = len(last_number)
    suffix = int(last_number) + 1
    string_format = '{:0' + str(length) + 'd}'
    suffix = string_format.format(suffix)

    return suffix


def long_date(str_date):
    dte_date = datetime.strptime(str_date, "%Y-%m-%d")
    dte_date = datetime.strftime(dte_date, "%B %d, %Y")
    return dte_date


def short_date(str_date):
    dte_date = datetime.strptime(str_date, "%Y-%m-%d")
    dte_date = datetime.strftime(dte_date, "%d-%b-%Y")
    return dte_date
