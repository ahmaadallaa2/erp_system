from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render 
from apps.users.views import login_view # استدعاء دالة اللوجين
# 2. اكتب الدالة دي قبل الـ urlpatterns
def custom_permission_denied_view(request, exception=None):
    # الدالة دي بتاخد الريكويست، وتروح تجيب 403.html من فولدر templates، وبترجع كود 403 للمتصفح
    return render(request, '403.html', status=403)

# 3. السطر السحري اللي بيربط جانجو بالدالة بتاعتك (لازم يتكتب بره المصفوفة خالص)
handler403 = custom_permission_denied_view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', login_view, name='login'), # صفحة اللوجين هي الرئيسية
    
    # ضيف السطر ده عشان يقرأ مسارات تطبيق الـ core
    path('core/', include('apps.core.urls')), 
    
    path('users/', include('apps.users.urls')),
]