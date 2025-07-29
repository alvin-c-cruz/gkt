app_name = "disbursement"
app_label = "Disbursement"
menu_label = (app_name, f"/{app_name}", app_label)


from .views import bp
from .models import Disbursement, DisbursementDetail
