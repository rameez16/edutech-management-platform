
from django.shortcuts import render

# Create your views here.


def dashboard(request):
    """Simple dashboard"""
    
    return render(request, 'dashboard/dashboard.html')


def onboard(request):
    
    return render(request, 'dashboard/onboarding.html')

def upload(request):
    
    return render(request, 'dashboard/uploaddoc.html')
