app_name = "vendor"
app_label = "Vendor"
menu_label = (app_name, f"/{app_name}", app_label)


from .views import bp
from .models import Vendor
