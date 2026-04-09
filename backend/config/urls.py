from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.users.api.urls")),
    path("api/partners/", include("apps.partners.api.urls")),
    path("api/inventory/", include("apps.inventory.api.urls")),
    path("api/sales/", include("apps.sales.api.urls")),
]