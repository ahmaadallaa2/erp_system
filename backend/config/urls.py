from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/", include("apps.core.api.urls")),
    path("api/auth/", include("apps.users.api.urls")),
    path("api/partners/", include("apps.partners.api.urls")),
    path("api/inventory/", include("apps.inventory.api.urls")),
    path("api/sales/", include("apps.sales.api.urls")),
    path("api/purchases/", include("apps.purchases.api.urls")),
    path("api/accounting/", include("apps.accounting.api.urls")),
    path("api/ai-assistant/", include("apps.ai_assistant.api.urls")),

    # OpenAPI schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    # Swagger UI
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    # ReDoc
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
