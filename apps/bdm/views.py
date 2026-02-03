from django.shortcuts import render,redirect
from .models import Student, Lead, Course, Batch

from .form import  TrainerAdminProfileForm

from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils import timezone
from datetime import datetime

# Create your views here.



from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Lead, Student, Trainer, Course, Batch, TeleCallerProfile


@login_required
def dashboard(request):
    """
    Dashboard view with comprehensive statistics and latest data
    """
    # Get current date for time-based filtering
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # Lead Statistics
    total_leads = Lead.objects.count()
    new_leads_count = Lead.objects.filter(
        enquiry_date__gte=week_ago
    ).count()
    pending_leads = Lead.objects.filter(
        status=Lead.LeadStatus.NEW
    ).count()
    
    # Get latest 10 leads ordered by enquiry date
    latest_leads = Lead.objects.select_related(
        'preferred_course', 'assigned_to'
    ).order_by('-enquiry_date')[:10]
    
    # Student Statistics
    total_students = Student.objects.count()
    active_students = Student.objects.count()
    
    # Trainer Statistics
    trainer_count = Trainer.objects.count()
    active_trainers = Trainer.objects.filter(admin_profile__is_active=True).count()
    
    # Course Statistics
    course_count = Course.objects.filter(is_active=True).count()
    
    # Batch Statistics
    batch_count = Batch.objects.filter(is_active=True).count()
    
    # Get upcoming batches (starting in the next 30 days)
    upcoming_batches = Batch.objects.filter(
        is_active=True,
        start_date__gte=today,
        start_date__lte=today + timedelta(days=30)
    ).select_related('course').prefetch_related('students')[:5]
    
    # Certificate requests (students who are eligible)
  
    
    # Pending payments (students who haven't paid booking fee)
    # pending_payments = Student.objects.filter(
    #     booking_fee_received=False,
    #     is_active=True
    # ).count()
    
    # Classes today (batches that are currently active)
    classes_today = Batch.objects.filter(
        is_active=True,
        start_date__lte=today,
        expected_finish_date__gte=today
    ).count()
    
    # Lead status breakdown for analytics
    lead_status_breakdown = Lead.objects.values('status').annotate(
        count=Count('id')
    )
    
    # Conversion rate calculation
    converted_leads = Lead.objects.filter(
        status=Lead.LeadStatus.CONVERTED
    ).count()
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
    
    context = {
        # Lead Data
        'total_leads': total_leads,
        'new_leads_count': new_leads_count,
        'pending_leads': pending_leads,
        'latest_leads': latest_leads,
        'conversion_rate': round(conversion_rate, 1),
        
        # Student Data
        'total_students': total_students,
        'active_students': active_students,
        
        # Trainer Data
        'trainer_count': trainer_count,
        'active_trainers': active_trainers,
        
        # Course & Batch Data
        'course_count': course_count,
        'batch_count': batch_count,
        'upcoming_batches': upcoming_batches,
        
        # Pending Actions
        # 'certificate_requests': certificate_requests,
        # 'pending_payments': pending_payments,
        'classes_today': classes_today,
        
        # Analytics
        'lead_status_breakdown': lead_status_breakdown,
        
        # Notifications (placeholder - implement as needed)
        'notification_count': 0,
        'notifications': [],
    }
    
    return render(request, 'bdm/dashboard/dashboard.html', context)


# Optional: View for lead detail/management
@login_required
def lead_detail(request, lead_id):
    """
    View for individual lead details
    """
    lead = Lead.objects.select_related(
        'preferred_course', 'assigned_to'
    ).get(id=lead_id)
    
    context = {
        'lead': lead,
    }
    
    return render(request, 'bdm/lead_detail.html', context)


# Optional: View for assigning leads
@login_required
def assign_lead(request, lead_id):
    """
    View for assigning leads to tele-callers
    """
    if request.method == 'POST':
        lead = Lead.objects.get(id=lead_id)
        tele_caller_id = request.POST.get('tele_caller')
        
        if tele_caller_id:
            from django.contrib.auth.models import User
            tele_caller = User.objects.get(id=tele_caller_id)
            lead.assigned_to = tele_caller
            lead.status = Lead.LeadStatus.ASSIGNED
            lead.save()
            
            # Update tele-caller profile stats
            profile, created = TeleCallerProfile.objects.get_or_create(
                user=tele_caller
            )
            profile.total_leads += 1
            profile.save()
            
            # Redirect or return success
            from django.shortcuts import redirect
            return redirect('dashboard')
    
    # GET request - show assignment form
    from django.contrib.auth.models import User, Group
    tele_callers = User.objects.filter(
        groups__name='TELE-CALLER',
        is_active=True
    )
    lead = Lead.objects.get(id=lead_id)
    
    context = {
        'lead': lead,
        'tele_callers': tele_callers,
    }
    
    return render(request, 'bdm/assign_lead.html', context)



User = get_user_model()



from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import Group
from .form import CreateUserForm

def create_user(request):
    if request.method == "POST":
        form = CreateUserForm(request.POST)

        if form.is_valid():
            user = form.save()

            # Assign role using Django Groups
            role = form.cleaned_data["role"]
            try:
                group = Group.objects.get(name__iexact=role)
                user.groups.add(group)
            except Group.DoesNotExist:
                pass

            messages.success(request, f"User '{user.username}' created successfully")
            return redirect("user_list")

        messages.error(request, "Please correct the errors below")

    else:
        form = CreateUserForm()

    return render(request, "bdm/user/create_user.html", {"form": form})


@login_required
def user_list(request):
    users = User.objects.all().order_by("-date_joined")

    return render(request, "bdm/user/user_list.html", {
        "users": users
    })
    
    
def create_trainer_admin_profile(request):
    if request.method == "POST":
        form = TrainerAdminProfileForm(request.POST)

        if form.is_valid():
            admin_profile = form.save()
            messages.success(
                request,
                f"Admin profile created for {admin_profile.trainer}"
            )
            return redirect("user_list")  # 👈 your target URL

    else:
        form = TrainerAdminProfileForm()

    return render(
        request,
        "bdm/trainer/trainer_profile.html",
        {"form": form}
    )    
    
    

# def create_user(request):
#     if request.method == "POST":
#         # Get form data
#         username = request.POST.get("username", "").strip()
#         email = request.POST.get("email", "").strip()
#         password = request.POST.get("password")
#         first_name = request.POST.get("first_name", "").strip()
#         last_name = request.POST.get("last_name", "").strip()
#         role = request.POST.get("role")
        
#         # Get checkbox values
#         is_active = request.POST.get("is_active") == "on"
#         is_staff = request.POST.get("is_staff") == "on"
#         is_superuser = request.POST.get("is_superuser") == "on"
        
#         # Get date joined (optional - defaults to now)
#         date_joined_str = request.POST.get("date_joined")
        
#         # Validation
#         errors = []
        
#         if not username:
#             errors.append("Username is required")
#         elif len(username) > 150:
#             errors.append("Username must be 150 characters or fewer")
#         elif User.objects.filter(username=username).exists():
#             errors.append("Username already exists")
        
#         if not email:
#             errors.append("Email address is required")
#         elif User.objects.filter(email=email).exists():
#             errors.append("Email address already exists")
        
#         if not password:
#             errors.append("Password is required")
#         elif len(password) < 8:
#             errors.append("Password must be at least 8 characters")
        
#         if not role:
#             errors.append("User role is required")
        
#         # If there are validation errors, show them and return
#         if errors:
#             for error in errors:
#                 messages.error(request, error)
#             return render(request, "bdm/user/create_user.html", {
#                 "form_data": request.POST  # Preserve form data
#             })
        
#         try:
#             # Create the user
#             user = User.objects.create_user(
#                 username=username,
#                 email=email,
#                 password=password,
#                 first_name=first_name,
#                 last_name=last_name
#             )
            
#             # Set additional fields
#             user.is_active = is_active
#             user.is_staff = is_staff
#             user.is_superuser = is_superuser
            
#             # Set date joined if provided
#             if date_joined_str:
#                 try:
#                     # Parse the datetime-local input format
#                     date_joined = datetime.strptime(date_joined_str, "%Y-%m-%dT%H:%M")
#                     user.date_joined = timezone.make_aware(date_joined)
#                 except ValueError:
#                     pass  # Use default if parsing fails
            
#             # Save the user
#             user.save()
            
#             # Handle role assignment (assuming you have a role field or group)
#             # Option 1: If role is a field on your User model or profile
#             if hasattr(user, 'role'):
#                 user.role = role
#                 user.save()
            
#             # Option 2: If using Django groups for roles
#             from django.contrib.auth.models import Group
#             try:
#                 group = Group.objects.get(name__iexact=role)
#                 user.groups.add(group)
#             except Group.DoesNotExist:
#                 pass  # Handle missing group
            
#             messages.success(request, f"User '{username}' created successfully")
#             return redirect("/")  # or wherever you want to redirect
            
#         except Exception as e:
#             messages.error(request, f"Error creating user: {str(e)}")
#             return render(request, "bdm/user/create_user.html", {
#                 "form_data": request.POST
#             })
    
#     # GET request - show the form
#     return render(request, "bdm/user/create_user.html")


def onboarding_view(request):
    
    return render(request,"bdm/student_onboarding/tab_view.html")

def students_tab(request):
    students = Student.objects.all()
    return render(request, "bdm/student_onboarding/students_tab.html", {
        "students": students
    })
    
def trainers_tab(request):
    trainers = Trainer.objects.all()
    return render(request, "bdm/student_onboarding/trainer_tab.html", {
        "trainers": trainers
    })   