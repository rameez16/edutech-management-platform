from django.shortcuts import render ,redirect
from .models import Student, Lead, Course, Batch
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from datetime import datetime
from django.contrib import messages

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
    active_students = Student.objects.filter(
        is_active=True,
        course_completion_status__in=[
            Student.CourseStatus.PHASE1,
            Student.CourseStatus.PHASE2,
            Student.CourseStatus.PHASE3
        ]
    ).count()
    
    # Trainer Statistics
    trainer_count = Trainer.objects.count()
    active_trainers = Trainer.objects.filter(is_active=True).count()
    
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
    certificate_requests = Student.objects.filter(
        certificate_eligible=True,
        course_completion_status=Student.CourseStatus.COMPLETED
    ).count()
    
    # Pending payments (students who haven't paid booking fee)
    pending_payments = Student.objects.filter(
        booking_fee_received=False,
        is_active=True
    ).count()
    
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
        'certificate_requests': certificate_requests,
        'pending_payments': pending_payments,
        'classes_today': classes_today,
        
        # Analytics
        'lead_status_breakdown': lead_status_breakdown,
        
        # Notifications (placeholder - implement as needed)
        'notification_count': 0,
        'notifications': [],
    }
    
    return render(request, 'bdm/dashboard/dashboard.html', context)



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
            # Add one day to include the entire end date
            date_to_obj = date_to_obj + timedelta(days=1)
            leads = leads.filter(enquiry_date__lt=date_to_obj)
        except ValueError:
            pass
    
    # Apply search filter (search in name, email, phone)
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
    
    # Get statistics for the stat cards
    total_leads = Lead.objects.count()
    new_leads = Lead.objects.filter(status=Lead.LeadStatus.NEW).count()
    
    # Calculate follow-up leads (assigned or idle)
    followup_leads = Lead.objects.filter(
        status__in=[Lead.LeadStatus.ASSIGNED, Lead.LeadStatus.IDLE]
    ).count()
    
    converted_leads = Lead.objects.filter(status=Lead.LeadStatus.CONVERTED).count()
    
    # Get all courses for the filter dropdown
    courses = Course.objects.all().order_by('name')
    
    # Get choices for filters
    status_choices = Lead.LeadStatus.choices
    mode_choices = Lead.ModeChoice.choices
    
    context = {
        'leads': leads,
        "all_leads": all_leads,               # FULL LIST
        "leads": all_leads,                   # for All Leads table (unchanged)
        "filtered_leads": filtered_leads,     # FILTER RESULT TABLE
        "filtered_count": filtered_leads.count(),
        'courses': courses,
        'status_choices': status_choices,
        'mode_choices': mode_choices,
        'new_leads_count': new_leads,
        'followup_leads_count': followup_leads,
        'converted_leads_count': converted_leads,
        'total_leads': total_leads,
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
            # later: create admission record here

        elif action == "lost":
            lead.status = "dropped"
            lead.save()

        return redirect("lead_details", lead_id=lead.id)

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
            return redirect("bulk_leads")

        leads = Lead.objects.filter(id__in=lead_ids)
        count = leads.count()

        if action == "assign":
            telecaller_id = request.POST.get("telecaller")
            if not telecaller_id:
                messages.error(request, "Please select a telecaller.")
                return redirect("bulk_leads")

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

        return redirect("leads")

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
    return redirect('leads')

def assign_lead(request):
    if request.method == "POST":
        lead = get_object_or_404(Lead, id=request.POST.get('lead_id'))
        lead.assigned_to_id = request.POST.get('assigned_to')
        lead.status = Lead.LeadStatus.ASSIGNED  # 🔥 auto status change
        lead.save()

    return redirect('bdm:leads')
