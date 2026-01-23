
from django.shortcuts import render

# Create your views here.


def dashboard(request):
    """Simple dashboard"""
    
    return render(request, 'dashboard/dashboard.html')





