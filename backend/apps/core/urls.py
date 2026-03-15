from django.urls import path
from django.views.generic import TemplateView

app_name = 'core'  # <--- السطر ده هو الـ namespace اللي جانجو كان بيدور عليه

urlpatterns = [
    # مؤقتاً هنخليها تفتح الـ base.html لحد ما نعملها صفحة مخصصة
    path('dashboard/', TemplateView.as_view(template_name="base.html"), name='dashboard'), 
]