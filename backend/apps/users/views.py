from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_not_required

@login_not_required
def login_view(request):
    # لو المستخدم عامل تسجيل دخول أصلاً، وديه على الداشبورد فوراً
    if request.user.is_authenticated:
        return redirect('core:dashboard') # أو '/' لو الداشبورد ملهاش اسم
    
    # لو مش مسجل، اعرضله صفحة اللوجين اللي صممناها
    return render(request, 'users/login.html')