from django.urls import path, include  # 👈 لازم include هنا

urlpatterns = [
    path("auth/", include("apps.users.api.urls")),
]