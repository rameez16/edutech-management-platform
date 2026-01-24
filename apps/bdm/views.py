from django.shortcuts import render
from .models import Student, Lead, Course, Batch

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