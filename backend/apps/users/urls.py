from django.urls import path, include
from .views import login_view

app_name = 'users'

urlpatterns = [
    # 1. مسار صفحة الـ HTML (اللي اليوزر بيكتبها في المتصفح)
    path('login/', login_view, name='login'), 

    # 2. تضمين مسارات الـ API (عشان الكود يكلمها)
    path('api/', include('apps.users.api.urls')), 
]