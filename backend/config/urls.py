from django.contrib import admin
from django.urls import path
from django.shortcuts import render # 1. ضيف السطر ده عشان نقدر نعرض الصفحة

# 2. اكتب الدالة دي قبل الـ urlpatterns
def custom_permission_denied_view(request, exception=None):
    # الدالة دي بتاخد الريكويست، وتروح تجيب 403.html من فولدر templates، وبترجع كود 403 للمتصفح
    return render(request, '403.html', status=403)

# 3. السطر السحري اللي بيربط جانجو بالدالة بتاعتك (لازم يتكتب بره المصفوفة خالص)
handler403 = custom_permission_denied_view

urlpatterns = [
    path('admin/', admin.site.urls),
    # ... باقي مساراتك
]