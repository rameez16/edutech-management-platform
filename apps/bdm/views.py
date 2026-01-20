from django.shortcuts import render
from .models import Student, Lead, Course, Batch

# Create your views here.


def dashboard(request):
    """Simple dashboard"""
    context = {
        'students': Student.objects.all(),
        'total_students': Student.objects.count(),
        'total_leads': Lead.objects.count(),
        'total_courses': Course.objects.count(),
    }
    return render(request, 'home.html', context)