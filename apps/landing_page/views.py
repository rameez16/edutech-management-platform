from django.shortcuts import render, get_object_or_404,redirect
from apps.bdm.models import Course,Lead
from django.contrib import messages

# Create your views here.


def landing(request):
    courses = Course.objects.filter(is_active=True)
    
    if request.method == "POST":
        Lead.objects.create(
            name=request.POST.get('name'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
            preferred_course_id=request.POST.get('preferred_course'),
            mode=request.POST.get('mode'),
        )
        messages.success(request, "Thank you! Your enquiry has been submitted successfully.")
    
    
    return render(request, 'landing_page/content/landing.html', {
        'courses': courses
    })
    

def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'landing_page/content/course_detail.html', {
        'course': course
    })
