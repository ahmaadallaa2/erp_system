from django.contrib import admin
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_not_required
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from apps.core.views import landing_view


@login_not_required
def health_view(request):
    return JsonResponse({"status": "ok"})


@login_not_required
def admin_logout_view(request):
    logout(request)
    return redirect("admin:login")


urlpatterns = [
    path("", landing_view, name="landing"),
    path("health/", health_view, name="health"),
    path("admin/logout/", admin_logout_view, name="admin-logout"),
    path("admin/", admin.site.urls),

    path("api/", include("apps.core.api.urls")),
    path("api/auth/", include("apps.users.api.urls")),
    path("api/partners/", include("apps.partners.api.urls")),
    path("api/inventory/", include("apps.inventory.api.urls")),
    path("api/sales/", include("apps.sales.api.urls")),
    path("api/purchases/", include("apps.purchases.api.urls")),
    path("api/accounting/", include("apps.accounting.api.urls")),
    path("api/ai-assistant/", include("apps.ai_assistant.api.urls")),
]

# Access is governed by SPECTACULAR_SETTINGS["SERVE_PERMISSIONS"]: open in DEBUG,
# staff-only otherwise. API_DOCS_ENABLED=False removes the routes entirely.
if settings.API_DOCS_ENABLED:
    schema_view = SpectacularAPIView.as_view()
    swagger_view = SpectacularSwaggerView.as_view(url_name="schema")
    redoc_view = SpectacularRedocView.as_view(url_name="schema")

    if settings.DEBUG:
        schema_view = login_not_required(schema_view)
        swagger_view = login_not_required(swagger_view)
        redoc_view = login_not_required(redoc_view)

    urlpatterns += [
        path("api/schema/", schema_view, name="schema"),
        path("api/docs/", swagger_view, name="swagger-ui"),
        path("api/redoc/", redoc_view, name="redoc"),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
