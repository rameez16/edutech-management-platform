from django.shortcuts import get_object_or_404,render,redirect
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
            return redirect("bdm:user_list")

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
    
    
def create_admin_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # ----------------------------
    # ROUTING BASED ON ROLE
    # ----------------------------
    if user.role == "trainer":
        return create_trainer_admin_profile(request, user)

    elif user.role == "student":
        return create_student_admin_profile(request, user)

    else:
        messages.error(request, "Admin profile not supported for this role.")
        return redirect("bdm:user_list")
    
    
    
    
def create_trainer_admin_profile(request, user):
    trainer = getattr(user, "trainer", None)

    if not trainer:
        messages.error(request, "Trainer profile not found.")
        return redirect("user_list")

    if request.method == "POST":
        form = TrainerAdminProfileForm(request.POST)

        if form.is_valid():
            admin_profile = form.save(commit=False)
            admin_profile.trainer = trainer
            admin_profile.save()

            messages.success(
                request,
                f"Trainer admin profile created for {trainer}"
            )
            return redirect("bdm:user_list")

    else:
        form = TrainerAdminProfileForm()

    return render(
        request,
        "bdm/trainer/trainer_profile.html",
        {
            "form": form,
            "user": user,
            "role": "trainer"
        }
    )   
    
def create_student_admin_profile(request, user):
    student = getattr(user, "student", None)

    if not student:
        messages.error(request, "Student profile not found.")
        return redirect("bdm:user_list")

    if request.method == "POST":
        form = StudentAdminProfileForm(request.POST)

        if form.is_valid():
            admin_profile = form.save(commit=False)
            admin_profile.student = student
            admin_profile.save()

            messages.success(
                request,
                f"Student admin profile created for {student}"
            )
            return redirect("user_list")

    else:
        form = StudentAdminProfileForm()

    return render(
        request,
        "bdm/student/student_profile.html",
        {
            "form": form,
            "user": user,
            "role": "student"
        }
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
    
    
    
    

# Leads management aleena

def leads(request):
    leads = Lead.objects.select_related(
        'preferred_course',
        'assigned_to'
    )

    # Get filter parameters from request
    status_filter = request.GET.get('status', '')
    course_filter = request.GET.get('course', '')
    mode_filter = request.GET.get('mode', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search_query = request.GET.get('search', '')

    # Apply status filter
    if status_filter:
        leads = leads.filter(status=status_filter)

    # Apply course filter
    if course_filter:
        leads = leads.filter(preferred_course_id=course_filter)

    # Apply mode filter
    if mode_filter:
        leads = leads.filter(mode=mode_filter)

    # Apply date range filter
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            leads = leads.filter(enquiry_date__gte=date_from_obj)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_obj = date_to_obj + timedelta(days=1)
            leads = leads.filter(enquiry_date__lt=date_to_obj)
        except ValueError:
            pass

    # Apply search filter
    all_leads = Lead.objects.all()
    filtered_leads = all_leads

    search = request.GET.get("search")
    status = request.GET.get("status")
    course = request.GET.get("course")
    mode = request.GET.get("mode")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")

    if search:
        filtered_leads = filtered_leads.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )

    if status:
        filtered_leads = filtered_leads.filter(status=status)

    if course:
        filtered_leads = filtered_leads.filter(preferred_course_id=course)

    if mode:
        filtered_leads = filtered_leads.filter(mode=mode)

    if date_from:
        filtered_leads = filtered_leads.filter(enquiry_date__gte=date_from)

    if date_to:
        filtered_leads = filtered_leads.filter(enquiry_date__lte=date_to)

    # Stats
    total_leads = Lead.objects.count()
    new_leads = Lead.objects.filter(status=Lead.LeadStatus.NEW).count()
    followup_leads = Lead.objects.filter(
        status__in=[Lead.LeadStatus.ASSIGNED, Lead.LeadStatus.IDLE]
    ).count()
    converted_leads = Lead.objects.filter(
        status=Lead.LeadStatus.CONVERTED
    ).count()

    courses = Course.objects.all().order_by('name')
    status_choices = Lead.LeadStatus.choices
    mode_choices = Lead.ModeChoice.choices

    context = {
        "all_leads": all_leads,
        "filtered_leads": filtered_leads,
        "filtered_count": filtered_leads.count(),
        "courses": courses,
        "status_choices": status_choices,
        "mode_choices": mode_choices,
        "new_leads_count": new_leads,
        "followup_leads_count": followup_leads,
        "converted_leads_count": converted_leads,
        "total_leads": total_leads,
    }

    return render(request, 'bdm/leads/leads.html', context)



def lead_details(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    counsellors = User.objects.filter(is_staff=True)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "assign":
            lead.assigned_to_id = request.POST.get("assigned_to")
            lead.status = "assigned"
            lead.save()

        elif action == "status":
            lead.status = request.POST.get("status")
            lead.save()

        elif action == "convert":
            lead.status = "converted"
            lead.save()

        elif action == "lost":
            lead.status = "dropped"
            lead.save()

        return redirect("bdm:lead_details", lead_id=lead.id)

    return render(request, "bdm/leads/lead_details.html", {
        "lead": lead,
        "counsellors": counsellors
    })


def bulk_leads(request):
    leads = Lead.objects.all()
    return render(request, "bdm/leads/bulk_leads.html", {
        "leads": leads
    })


@login_required
def bulk_action(request):
    if request.method == "POST":
        lead_ids = request.POST.getlist("lead_ids")
        action = request.POST.get("bulk_action")

        if not lead_ids or not action:
            messages.warning(request, "No leads or action selected.")
            return redirect("bdm:bulk_leads")

        leads = Lead.objects.filter(id__in=lead_ids)
        count = leads.count()

        if action == "assign":
            telecaller_id = request.POST.get("telecaller")
            if not telecaller_id:
                messages.error(request, "Please select a telecaller.")
                return redirect("bdm:bulk_leads")

            leads.update(
                assigned_to_id=telecaller_id,
                status=Lead.LeadStatus.ASSIGNED
            )
            messages.success(request, f"{count} leads assigned successfully.")

        elif action == "converted":
            leads.update(status=Lead.LeadStatus.CONVERTED)
            messages.success(request, f"{count} leads marked as converted.")

        elif action == "lost":
            leads.update(status=Lead.LeadStatus.DROPPED)
            messages.success(request, f"{count} leads marked as lost.")

        return redirect("bdm:leads")


def create_lead(request):
    if request.method == "POST":
        Lead.objects.create(
            name=request.POST.get('name'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
            preferred_course_id=request.POST.get('preferred_course') or None,
            mode=request.POST.get('mode'),
            notes=request.POST.get('notes', '')
        )
    return redirect('bdm:leads')


def assign_lead(request):
    if request.method == "POST":
        lead = get_object_or_404(Lead, id=request.POST.get('lead_id'))
        lead.assigned_to_id = request.POST.get('assigned_to')
        lead.status = Lead.LeadStatus.ASSIGNED
        lead.save()

    return redirect('bdm:leads')