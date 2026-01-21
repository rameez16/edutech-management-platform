
from django.shortcuts import render

# Create your views here.


def dashboard(request):
    """Simple dashboard"""
    
    return render(request, 'dashboard/dashboard.html')

def index(request):
    """index page"""
    
    return render(request, 'dashboard/index.html')



