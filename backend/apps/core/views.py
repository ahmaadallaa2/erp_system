from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render


@login_not_required
def landing_view(request):
    return render(request, "core/landing.html")
