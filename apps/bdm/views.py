from django.shortcuts import get_object_or_404,render,redirect
from .models import Student, Lead, Course, Batch
from django.core.paginator import Paginator
from .form import  TrainerAdminProfileForm ,ModuleForm ,LessonPlanForm
from django.db import transaction
from decimal import Decimal
from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce
from django.db.models import Max
from django.db.models import Case, When, IntegerField


from django.db.models import Prefetch

from django.db import models

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .models import StudentAdminProfile, TrainerAdminProfile
from .form import StudentAdminProfileForm, TrainerAdminProfileForm

from django.db.models import Sum, Avg

from apps.student.models import FeePayment ,LeaveApplication ,StudentFeedback
from apps.bdm.models import Student ,PaymentDocument ,StudentIssue ,Announcement ,BatchSchedule

from apps.trainer.models import Module,TrainerLeave
from apps.trainer.models import Module


# Create your views here.

from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    View
)



from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Lead, Student, Trainer, Course, Batch, TeleCallerProfile,OnboardingChecklist

from apps.student.models import StudentDocument,EnrollmentAgreement,StudentIDCard

from apps.bdm.constants import REQUIRED_DOCUMENT_TYPES


from .utils import role_required,counselor_or_admin_required



# @login_required
# @role_required('admin')
# def dashboard(request):
#     """
#     Dashboard view with comprehensive statistics and latest data
#     """
#     # Get current date for time-based filtering
#     today = timezone.now().date()
#     week_ago = today - timedelta(days=7)
    
#     # Lead Statistics
#     total_leads = Lead.objects.count()
#     new_leads_count = Lead.objects.filter(
#         enquiry_date__gte=week_ago
#     ).count()
#     pending_leads = Lead.objects.filter(
#         status=Lead.LeadStatus.NEW
#     ).count()
    
#     # Get latest 10 leads ordered by enquiry date
#     latest_leads = Lead.objects.select_related(
#         'preferred_course', 'assigned_to'
#     ).order_by('-enquiry_date')[:10]
    
#     # Student Statistics
#     total_students = Student.objects.count()
#     active_students = Student.objects.count()
    
#     # Trainer Statistics
#     trainer_count = Trainer.objects.count()
#     active_trainers = Trainer.objects.filter(admin_profile__is_active=True).count()
    
#     # Course Statistics
#     course_count = Course.objects.filter(is_active=True).count()
    
#     # Batch Statistics
#     batch_count = Batch.objects.filter(is_active=True).count()
    
#     # Get upcoming batches (starting in the next 30 days)
#     upcoming_batches = Batch.objects.filter(
#         is_active=True,
#         start_date__gte=today,
#         start_date__lte=today + timedelta(days=30)
#     ).select_related('course').prefetch_related('students')[:5]
    
#     # Certificate requests (students who are eligible)
  
    
#     # Pending payments (students who haven't paid booking fee)
#     # pending_payments = Student.objects.filter(
#     #     booking_fee_received=False,
#     #     is_active=True
#     # ).count()
    
#     # Classes today (batches that are currently active)
#     classes_today = Batch.objects.filter(
#         is_active=True,
#         start_date__lte=today,
#         expected_finish_date__gte=today
#     ).count()
    
#     # Lead status breakdown for analytics
#     lead_status_breakdown = Lead.objects.values('status').annotate(
#         count=Count('id')
#     )
    
#     # Conversion rate calculation
#     converted_leads = Lead.objects.filter(
#         status=Lead.LeadStatus.CONVERTED
#     ).count()
#     conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
    
#     context = {
#         # Lead Data
#         'total_leads': total_leads,
#         'new_leads_count': new_leads_count,
#         'pending_leads': pending_leads,
#         'latest_leads': latest_leads,
#         'conversion_rate': round(conversion_rate, 1),
        
#         # Student Data
#         'total_students': total_students,
#         'active_students': active_students,
        
#         # Trainer Data
#         'trainer_count': trainer_count,
#         'active_trainers': active_trainers,
        
#         # Course & Batch Data
#         'course_count': course_count,
#         'batch_count': batch_count,
#         'upcoming_batches': upcoming_batches,
        
#         # Pending Actions
#         # 'certificate_requests': certificate_requests,
#         # 'pending_payments': pending_payments,
#         'classes_today': classes_today,
        
#         # Analytics
#         'lead_status_breakdown': lead_status_breakdown,
        
#         # Notifications (placeholder - implement as needed)
#         'notification_count': 0,
#         'notifications': [],
#     }
    
#     return render(request, 'bdm/dashboard/dashboard.html', context)


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

@role_required('admin')
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
@role_required('admin')
def user_list(request):
    users = User.objects.all().order_by("-date_joined")

    return render(request, "bdm/user/user_list.html", {
        "users": users
    })
    
@role_required('admin')    
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
    
    


# student-onboarding- Ramees

def onboarding_view(request):
    
    return render(request,"bdm/student_onboarding/tab_view.html")


def students_with_uploaded_documents(request):
   
    checklists = (
        OnboardingChecklist.objects
        .select_related("student")
        .filter(
            documents_uploaded=True,
            documents_verified=False
        )
    )

    return render(
        request,
        "bdm/student_onboarding/docs_verification/studentList.html",
        {"checklists": checklists}
    )
    
 
def student_document_review(request, student_id):
    
    student = get_object_or_404(Student, id=student_id)

    documents = student.documents.filter(
        document_type__in=REQUIRED_DOCUMENT_TYPES
    )

    return render(
        request,
        "bdm/student_onboarding/docs_verification/studentView.html",
        {
            "student": student,
            "documents": documents,
        }
    )    
    
    
    
def verify_document(request, doc_id):
    
    document = get_object_or_404(StudentDocument, id=doc_id)
    student = document.student
    checklist = student.onboarding_checklist

    document.verification_status = StudentDocument.VerificationStatus.VERIFIED
    document.verified_by = request.user
    document.verified_at = timezone.now()
    document.save()

    #final check
    check=student.all_required_documents_verified()
    print(check)
    if student.all_required_documents_verified():
        checklist.documents_verified = True
        checklist.enrollment_letter_generated = True
        checklist.save()
        messages.success(
            request,
            "All documents verified. Student ready for enrollment letter."
        )

    return redirect(
        "bdm:student_document_review",
        student_id=student.id
    ) 
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST    
    
@require_POST
@csrf_exempt
def reject_document(request, document_id):
    try:
        document = StudentDocument.objects.get(id=document_id)
        rejection_reason = request.POST.get('rejection_reason', '')
        notes = request.POST.get('notes', '')
        
        # Update document status
        document.verification_status = 'rejected'
        document.rejection_reason = rejection_reason
        document.verified_by = request.user
        document.verified_at = timezone.now()
        document.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Document rejected successfully'
        })
    except StudentDocument.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Document not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)      
    


@login_required
def enrollment_verification_list(request):
    agreements = EnrollmentAgreement.objects.filter(
        is_signed=True,
        approved_by__isnull=True
    ).select_related('student')
    
    print(agreements)

    return render(
        request,
        'bdm/student_onboarding/enrollment-letter/student_list_enrollment.html',
        {
            'agreements': agreements
        }
    )


from .utils import generate_card_number
import random
import string
from django.utils.crypto import get_random_string
from apps.student.models import LMSAccess

@login_required
def approve_enrollment_agreement(request, student_id):
    agreement = get_object_or_404(
        EnrollmentAgreement,
        student__id=student_id
    )

    checklist = agreement.student.onboarding_checklist

    if not agreement.is_signed:
        messages.error(request, "Agreement not signed.")
        return redirect('enrollment_verification_list')

    if request.method == "POST":
        # ✅ Approve agreement
        agreement.approved_by = request.user
        agreement.approval_date = timezone.now()
        agreement.save()

        # ✅ Update checklist
        checklist.enrollment_letter_signed = True
        checklist.enrollment_letter_generated = True
        checklist.save()

        # ✅ AUTO CREATE ID CARD (if not exists)
        StudentIDCard.objects.get_or_create(
            student=agreement.student,
            defaults={
                'card_number': generate_card_number(agreement.student),
                'issue_date': timezone.now().date(),
                'expiry_date': timezone.now().date() + timedelta(days=200),
            }
        )
        
        checklist.id_card_generated = True
        checklist.id_card_issued = True
        checklist.save() 
        
        # ✅ AUTO CREATE LMS ACCESS (if not exists)
        lms_access, created = LMSAccess.objects.get_or_create(
            student=agreement.student,
            defaults={
                'lms_username':agreement.student.user.username,
                'lms_user_id': f"LMS{random.randint(10000,99999)}",
                'activated_date': timezone.now().date(),
                'expiry_date': timezone.now().date() + timedelta(days=200),
            }
        )

        if created:
            messages.success(
                request,
                f"LMS Access created. Username: {lms_access.lms_username}"
                )

        messages.success(request, "Agreement approved & ID card generated.LMS access granted")
        return redirect('bdm:view_student_id_card', student_id=student_id)

    return render(
        request,
        "bdm/student_onboarding/enrollment-letter/enrollment-letter-verification.html",
        {"agreement": agreement}
    )



@login_required
def view_student_id_card(request, student_id):
    id_card = get_object_or_404(
        StudentIDCard,
        student__id=student_id
    )

    # ✅ ALWAYS define this first
    lms_access = LMSAccess.objects.filter(
        student=id_card.student
    ).first()

    if request.method == "POST":
        if "collect" in request.POST:
            id_card.is_collected = True
            id_card.collected_date = timezone.now().date()

        if "lost" in request.POST:
            id_card.is_lost = True
            id_card.lost_date = timezone.now().date()

        id_card.save()
        messages.success(request, "ID card status updated.")

        # Redirect after POST (Best Practice)
        return redirect('bdm:view_student_id_card', student_id=student_id)

    return render(
        request,
        "bdm/student_onboarding/student_id card/id_card.html",
        {
            "id_card": id_card,
            "lms_access": lms_access
        }
    )



def docsVerification_tab(request):
    students = Student.objects.all()
    return render(request, "bdm/student_onboarding/students_tab.html", {
        "students": students
    })
    
def enrollmentLetter_tab(request):
    trainers = Trainer.objects.all()
    return render(request, "bdm/student_onboarding/trainer_tab.html", {
        "trainers": trainers
    })   
    

def id_card_generation_tab(request):
    trainers = Trainer.objects.all()
    return render(request, "bdm/student_onboarding/trainer_tab.html", {
        "trainers": trainers
    })   
    
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils import timezone

from apps.bdm.utils import render_to_pdf    
    
    
def download_enrollment_letter(request):
    student = request.user.student
    checklist = student.onboarding_checklist

    # 🔒 SECURITY CHECK
    if not checklist.documents_verified:
        return HttpResponseForbidden("Documents not verified yet")

    # Auto-mark generated (first time only)
    if not checklist.enrollment_letter_generated:
        checklist.enrollment_letter_generated = True
        checklist.save()

    context = {
        "student": student,
        "date": timezone.now().date(),
    }

    return render_to_pdf(
        "bdm/student_onboarding/enrollment-letter/enrollment-letter.html",
        context,
        filename="Enrollment_Letter.pdf"
    )        
    
    

# Leads management aleena
@login_required
@counselor_or_admin_required
def leads(request):
    
    is_counselor = request.user.role == "counselor"
    counselor_profile = getattr(request.user, 'counselor', None)

    # ── Base queryset ──
    all_leads = Lead.objects.select_related(
        'preferred_course',
        'assigned_to'
    ).order_by('-enquiry_date')

    # ── Counselor sees ONLY their assigned leads ──
    if is_counselor:
        all_leads = all_leads.filter(assigned_to=request.user)

    # ── Filtered queryset (starts from all_leads) ──
    filtered_leads = all_leads

    # Get filter parameters
    status = request.GET.get('status')
    course = request.GET.get('course')
    mode = request.GET.get('mode')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')

    # Apply filters
    if status:
        filtered_leads = filtered_leads.filter(status=status)

    if course:
        filtered_leads = filtered_leads.filter(preferred_course_id=course)

    if mode:
        filtered_leads = filtered_leads.filter(mode=mode)

    if date_from:
        try:
            filtered_leads = filtered_leads.filter(
                enquiry_date__date__gte=date_from
            )
        except ValueError:
            pass

    if date_to:
        try:
            filtered_leads = filtered_leads.filter(
                enquiry_date__date__lte=date_to
            )
        except ValueError:
            pass

    if search:
        filtered_leads = filtered_leads.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )

    # ── Stats (always computed from role-scoped all_leads) ──
    total_leads         = all_leads.count()
    new_leads_count     = all_leads.filter(status=Lead.LeadStatus.NEW).count()
    converted_leads_count = all_leads.filter(status=Lead.LeadStatus.CONVERTED).count()

    if is_counselor:
        # Counselor-specific stats
        assigned_leads_count = all_leads.filter(
            status=Lead.LeadStatus.ASSIGNED
        ).count()
        conversion_rate = round(
            (converted_leads_count / total_leads * 100) if total_leads else 0, 1
        )
        followup_leads_count = 0  # not used in counselor view
    else:
        # Admin stats
        assigned_leads_count = all_leads.filter(
            status=Lead.LeadStatus.ASSIGNED
        ).count()
        followup_leads_count = all_leads.filter(
            status__in=[Lead.LeadStatus.ASSIGNED, Lead.LeadStatus.IDLE]
        ).count()
        conversion_rate = round(
            (converted_leads_count / total_leads * 100) if total_leads else 0, 1
        )

    context = {
        # Tables
        "leads": all_leads,
        "filtered_leads": filtered_leads,
        "filtered_count": filtered_leads.count(),

        # Dropdowns
        "courses": Course.objects.all().order_by('name'),
        "status_choices": Lead.LeadStatus.choices,
        "mode_choices": Lead.ModeChoice.choices,
        "counselors": User.objects.filter(
            role="counselor",
            counselor__is_active=True
        ).select_related('counselor'),

        # Stats
        "total_leads": total_leads,
        "new_leads_count": new_leads_count,
        "followup_leads_count": followup_leads_count,
        "converted_leads_count": converted_leads_count,
        "assigned_leads_count": assigned_leads_count,
        "conversion_rate": conversion_rate,

        # Role flags
        "is_counselor": is_counselor,
        "counselor_profile": counselor_profile,
    }

    return render(request, 'bdm/leads/leads.html', context)


@counselor_or_admin_required
def lead_details(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    counsellors = User.objects.filter(role="counselor")
    
    new_student_data = request.session.pop("new_student_data", None)

    is_admin = request.user.groups.filter(name="Admin").exists()
    
    courses=Course.objects.all()         # changes
    batches=Batch.objects.all()

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
        "counsellors": counsellors,
        "batches":batches,
        "courses":courses,
         "new_student_data": new_student_data,
        "is_admin": is_admin,
    })

#lead follow up Ramees.
@counselor_or_admin_required
def update_lead_followup(request, pk):
    lead = get_object_or_404(Lead, pk=pk)

    if request.method == "POST":
        lead.educational_qualification = request.POST.get("educational_qualification")
        lead.confirmed_course_id = request.POST.get("confirmed_course") or None
        lead.interested_batch_id = request.POST.get("interested_batch") or None
        lead.discussed_fee = request.POST.get("discussed_fee") or None
        lead.payment_plan = request.POST.get("payment_plan") or None
        lead.telecaller_notes = request.POST.get("telecaller_notes")
        lead.admission_fee_paid = request.POST.get("admission_fee_paid") == "on"
        lead.admission_fee_amount=request.POST.get("admission_fee")

        # lead.status = Lead.LeadStatus.FOLLOWED  # optional
        lead.save()

        messages.success(request, "Follow-up details updated successfully!")

    return redirect("bdm:leads")



from .models import Admission

User = get_user_model()

from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required


@login_required
@role_required('admin')
def convert_lead_to_admission(request, pk):

    # 🔒 Admin Only
    if not request.user.groups.filter(name="Admin").exists():
        messages.error(request, "You are not authorized.")
        return redirect("bdm:leads")

    lead = get_object_or_404(Lead, pk=pk)

    # ❌ Prevent double conversion
    if lead.status == Lead.LeadStatus.CONVERTED:
        messages.error(request, "This lead is already converted.")
        return redirect("bdm:lead_details", pk=pk)

    if request.method == "POST":

        # 🔎 Check if user already exists
        existing_user = User.objects.filter(email=lead.email).first()

        if existing_user:
            messages.error(request, "A user with this email already exists.")
            return redirect("bdm:lead_details", pk=pk)

        with transaction.atomic():

            # 1️⃣ Create User (safe username)
            username = f"{lead.phone}"
            password = f"{lead.name}@1234"

            user = User.objects.create_user(
                username=username,
                email=lead.email,
                password=password,
                first_name=lead.name,
                role="student"
            )

            student_group, _ = Group.objects.get_or_create(name="Student")
            user.groups.add(student_group)

            # 2️⃣ Create Student
            student = Student.objects.create(
                user=user,
                full_name=lead.name,
                email=lead.email,
                phone=lead.phone
            )

            if lead.interested_batch:
                student.batches.add(lead.interested_batch)

            # 🔎 Prevent duplicate admission
            if Admission.objects.filter(student=student, status="active").exists():
                messages.error(request, "Active admission already exists.")
                return redirect("bdm:lead_details", pk=pk)

            # 3️⃣ Create Admission
            admission = Admission.objects.create(
                user=user,
                student=student,
                course=lead.confirmed_course or lead.preferred_course,
                batch=lead.interested_batch,
                educational_qualification=lead.educational_qualification,
                payment_plan=lead.payment_plan,
                total_fee=lead.discussed_fee or Decimal("0.00"),
                admitted_by=request.user,
                admission_fee_paid=lead.admission_fee_paid,
                admission_fee_amount=lead.admission_fee_amount or Decimal("0.00"),
                status="active"
            )

            # 4️⃣ Create Admission Fee Payment
            feepayment = FeePayment.objects.create(
                student=student,
                payment_type=FeePayment.PaymentType.ADMISSION,
                amount=lead.discussed_fee or Decimal("0.00"),
                payment_method=FeePayment.PaymentMethod.UPI,
                payment_status=FeePayment.PaymentStatus.COMPLETED,
                transaction_id=f"TRN-{student.id}-{int(timezone.now().timestamp())}",
                receipt_number=f"REC-{student.id}",
                payment_date=timezone.now(),
                remarks="Admission fee collected during conversion",
                received_by=request.user
            )

            # 5️⃣ Update Lead
            lead.status = Lead.LeadStatus.CONVERTED
            lead.save(update_fields=["status"])

        messages.success(
            request,
            f"Admission created! Username: {username} | Password: {password}"
        )
        
        
        request.session["new_student_data"] = {
                "username": username,
                "password": password,
                "name": lead.name,
                "course": str(admission.course),
                "batch": str(admission.batch) if admission.batch else "",
                "payment_plan": admission.payment_plan,
                "fee": str(admission.total_fee),
                "admission_date": admission.admission_date.strftime("%d-%m-%Y"),
                "admission fee receipt no":feepayment.receipt_number
            }

        return redirect("bdm:student_dashboard", pk=student.pk)

    return redirect("bdm:lead_detail", pk=pk)






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
        messages.success(request, "Lead created successfully ✅")

    return redirect('bdm:leads')

@role_required('admin')
def assign_lead(request):
    if request.method == "POST":
        lead = get_object_or_404(Lead, id=request.POST.get('lead_id'))
        assigned_user_id = request.POST.get('assigned_to')
        
        if not assigned_user_id:
            messages.error(request, "Please select a counselor.")
            return redirect('bdm:leads')
        
        assigned_user = get_object_or_404(User, id=assigned_user_id)
        
        # Update lead
        lead.assigned_to = assigned_user
        lead.status = Lead.LeadStatus.ASSIGNED
        lead.save()
        
        # Update Counselor metrics if profile exists
        counselor = getattr(assigned_user, 'counselor', None)
        if counselor:
            counselor.total_leads_assigned += 1
            counselor.active_leads += 1
            counselor.save()
        
        messages.success(request, f"Lead assigned to {assigned_user.get_full_name() or assigned_user.username} 👤")
    
    return redirect('bdm:leads')



# user profile view
@role_required('admin')
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)

    trainer_profile = getattr(user, "trainer", None)
    student_profile = getattr(user, "student", None)

    return render(
        request,
        "bdm/user/user_profile.html",
        {
            "user_obj": user,
            "trainer_profile": trainer_profile,
            "student_profile": student_profile,
        }
    )

@login_required
@role_required('admin')
def student_admin_profile_form(request, user_id):
    student = get_object_or_404(Student, user__id=user_id)

    # ✅ DO NOT create on GET
    admin_profile = StudentAdminProfile.objects.filter(
        student=student
    ).first()

    is_edit = admin_profile is not None

    if request.method == "POST":
        form = StudentAdminProfileForm(request.POST, instance=admin_profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.student = student

            # ✅ Ensure student_code is set ONLY once
            if not profile.student_code:
                profile.student_code = f"STU{student.id:05d}"

            profile.save()

            messages.success(
                request,
                "Student admin profile updated successfully."
                if is_edit
                else "Student admin profile created successfully."
            )
            return redirect("bdm:user_profile", user_id)
    else:
        form = StudentAdminProfileForm(instance=admin_profile)

    return render(
        request,
        "bdm/student/st_admin_profile_form.html",
        {
            "form": form,
            "student": student,
            "user_obj": student.user,
            "is_edit": is_edit,
        }
    )
@login_required
@role_required('admin')
def trainer_admin_profile_form(request, user_id):
    trainer = get_object_or_404(Trainer, user__id=user_id)

    admin_profile, created = TrainerAdminProfile.objects.get_or_create(
        trainer=trainer
    )

    if request.method == "POST":
        form = TrainerAdminProfileForm(request.POST, instance=admin_profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.trainer = trainer   # ✅ IMPORTANT
            profile.save()

            messages.success(
                request,
                "Trainer admin profile created successfully."
                if created else
                "Trainer admin profile updated successfully."
            )
            return redirect("bdm:user_profile", user_id)
    else:
        form = TrainerAdminProfileForm(instance=admin_profile)

    return render(
        request,
        "bdm/trainer/tr_admin_profile_form.html",
        {
            "form": form,
            "trainer": trainer,
            "user_obj": trainer.user,
            "is_edit": not created,
        }
    )



#batch
@role_required('admin')
def batch_list(request):
    batch_qs = Batch.objects.select_related('course').order_by('-id')

    active_batches_count = batch_qs.filter(is_active=True).count()
    inactive_batches_count = batch_qs.filter(is_active=False).count()

    paginator = Paginator(batch_qs, 10)
    page_number = request.GET.get('page')
    batches = paginator.get_page(page_number)

    courses = Course.objects.all()
    
    # ✅ ADD THESE
    trainers = Trainer.objects.all()
    students = Student.objects.filter(batches__isnull=True).distinct()
    context = {
        'batches': batches,
        'courses': courses,
        'trainers': trainers,   
        'students': students,
        'active_batches_count': active_batches_count,
        'inactive_batches_count': inactive_batches_count,
    }
    return render(request, 'bdm/batch/batch_list.html', context)
def batch_detail(request, pk):
    batch = get_object_or_404(
        Batch.objects.select_related('course')
        .prefetch_related(
            'trainers__user',
            'students__user',
        ),
        pk=pk
    )

    # ✅ Custom weekday ordering
    schedules = batch.schedules.annotate(
        day_order=Case(
            When(day_of_week='monday', then=1),
            When(day_of_week='tuesday', then=2),
            When(day_of_week='wednesday', then=3),
            When(day_of_week='thursday', then=4),
            When(day_of_week='friday', then=5),
            When(day_of_week='saturday', then=6),
            When(day_of_week='sunday', then=7),
            output_field=IntegerField(),
        )
    ).order_by('day_order', 'start_time')

    return render(request, 'bdm/batch/batch_detail.html', {
        'batch': batch,
        'trainers': batch.trainers.all(),
        'schedules': schedules,  # ✅ pass ordered schedules
    })
     
    
def toggle_batch_extension(request, pk):
    if request.method == "POST":
        batch = get_object_or_404(Batch, pk=pk)
        batch.requested_extension = not batch.requested_extension
        batch.save()

    return redirect("bdm:batch_detail", pk=pk)

@login_required
@role_required('admin')
def batch_create(request):

    if request.method == "POST":
        try:
            with transaction.atomic():
                batch = Batch.objects.create(
                    name=request.POST.get("name"),
                    course_id=request.POST.get("course"),
                    start_date=request.POST.get("start_date"),
                    expected_finish_date=request.POST.get("expected_finish_date"),
                    duration_months=request.POST.get("duration_months"),
                    is_active=request.POST.get("is_active") == "on",
                    requested_extension=request.POST.get("requested_extension") == "on",
                )

                # Trainers
                trainer_ids = request.POST.getlist("trainers")
                if trainer_ids:
                    batch.trainers.add(*trainer_ids)

                # Students (only unassigned)
                student_ids = request.POST.getlist("students")
                if student_ids:
                    unassigned_students = Student.objects.filter(
                        id__in=student_ids,
                        batches__isnull=True
                    ).distinct()
                    batch.students.add(*unassigned_students)

            messages.success(request, "Batch created successfully!")
            return redirect("bdm:batch_list")

        except Exception as e:
            messages.error(request, f"Error creating batch: {e}")
            return redirect("bdm:batch_list")

    # 🔥 THIS PART WAS MISSING (GET request)
    trainers = Trainer.objects.all()
    students = Student.objects.filter(batches__isnull=True).distinct()
    courses = Course.objects.all()

    return render(request, "bdm/batch_create.html", {
        "trainers": trainers,
        "students": students,
        "courses": courses,
    })

def add_batch_schedule(request, pk):
    batch = get_object_or_404(Batch, pk=pk)

    if request.method == "POST":
        day = request.POST.get("day_of_week")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        trainer_id = request.POST.get("trainer")

        trainer = None
        if trainer_id:
            trainer = Trainer.objects.get(id=trainer_id)

        BatchSchedule.objects.create(
            batch=batch,
            day_of_week=day,
            start_time=start_time,
            end_time=end_time,
            trainer=trainer
        )

        messages.success(request, "Schedule added successfully!")

    return redirect(f"{reverse('bdm:batch_detail', args=[batch.id])}?open_schedule=1")



#payments

# ================================
# PAYMENT DASHBOARD
# ================================

@login_required
@role_required('admin')
def payments_dashboard(request):
    payments = FeePayment.objects.select_related("student")

    # ----------------------------
    # FILTERING
    # ----------------------------

    payment_type = request.GET.get("type")
    if payment_type:
        payments = payments.filter(payment_type=payment_type)

    status = request.GET.get("status")
    if status:
        payments = payments.filter(payment_status=status)

    # ----------------------------
    # SORTING
    # ----------------------------

    sort = request.GET.get("sort")
    if sort == "amount_asc":
        payments = payments.order_by("amount")
    elif sort == "amount_desc":
        payments = payments.order_by("-amount")
    else:
        payments = payments.order_by("-created_at")

    # ----------------------------
    # DASHBOARD CARDS DATA
    # ----------------------------

    all_payments = FeePayment.objects.all()

    completed_count = all_payments.filter(
        payment_status="completed"
    ).count()

    pending_count = all_payments.filter(
        payment_status="pending"
    ).count()

    installment_count = all_payments.filter(
        payment_type="installment"
    ).count()

    total_collected = all_payments.filter(
    payment_status="completed"
).aggregate(
    total=Coalesce(
        Sum("amount"),
        Decimal("0.00"),
        output_field=DecimalField()
    )
)["total"]


    # ----------------------------
    # CONTEXT
    # ----------------------------

    context = {
        "recent_payments": payments,
        "completed_count": completed_count,
        "pending_count": pending_count,
        "installment_count": installment_count,
        "total_collected": total_collected,
    }

    return render(request, "bdm/payments/payments_dashboard.html", context)




@login_required
@role_required('admin')
def payment_detail(request, pk):
    payment = get_object_or_404(
        FeePayment.objects
        .select_related("student", "received_by")
        .prefetch_related("documents", "student__batches__course"),
        pk=pk
    )

    student = payment.student
    batch = student.batches.first()
    course = batch.course if batch else None

    # ─────────────────────────────
    # HANDLE STATUS UPDATE FROM DROPDOWN
    # ─────────────────────────────
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(FeePayment.PaymentStatus.choices).keys():
            payment.payment_status = new_status
            payment.save()
        return redirect("bdm:payment_detail", pk=payment.pk)

    # ─────────────────────────────
    # GET TOTAL COURSE FEE
    # ─────────────────────────────
    total_fee = course.course_fee if course else Decimal("0.00")

    # ─────────────────────────────
    # CALCULATE TOTALS
    # ─────────────────────────────
    total_paid = (
        FeePayment.objects
        .filter(student=student, payment_status=FeePayment.PaymentStatus.COMPLETED)
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    total_pending = (
        FeePayment.objects
        .filter(student=student, payment_status=FeePayment.PaymentStatus.PENDING)
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    balance = total_fee - total_paid

    # ─────────────────────────────
    # EMI INSTALLMENTS
    # ─────────────────────────────
    all_installments = []
    if payment.payment_type == FeePayment.PaymentType.INSTALLMENT:
        all_installments = (
            FeePayment.objects
            .filter(student=student, payment_type=FeePayment.PaymentType.INSTALLMENT)
            .order_by("installment_number")
        )

    # ─────────────────────────────
    # ALL PAYMENTS OF STUDENT
    # ─────────────────────────────
    all_student_payments = FeePayment.objects.filter(student=student).order_by("-payment_date")

    context = {
        "payment": payment,
        "student": payment.student,
        "course": course,
        "batch": batch,
        "all_installments": all_installments,
        "all_student_payments": all_student_payments,
        "total_fee": total_fee,
        "total_paid": total_paid,
        "total_pending": total_pending,
        "balance": balance,
        "today": timezone.now().date(),
        # ✅ send payment status choices to template
        "payment_status_choices": FeePayment.PaymentStatus.choices,
    }

    return render(request, "bdm/payments/payment_detail.html", context)

@role_required('admin')
def course_fee(request):

    # ✅ Only students who have at least one payment
    students = (
        Student.objects
        .filter(fee_payments__isnull=False)
        .prefetch_related('fee_payments', 'batches__course')
        .distinct()
    )

    search = request.GET.get("search")
    status_filter = request.GET.get("status")

    if search:
        students = students.filter(full_name__icontains=search)

    student_data = []

    for student in students:

        batch = student.batches.first()
        course = batch.course if batch else None
        course_fee = course.course_fee if course else Decimal("0.00")

        payments = student.fee_payments.all()

        # =====================================================
        # 🔹 ADMISSION STATUS
        # =====================================================

        admission_payments = payments.filter(
            payment_type=FeePayment.PaymentType.ADMISSION
        )

        if not admission_payments.exists():
            admission_status = "UNPAID"

        elif admission_payments.filter(
            payment_status=FeePayment.PaymentStatus.COMPLETED
        ).exists():
            admission_status = "PAID"

        elif admission_payments.filter(
            payment_status=FeePayment.PaymentStatus.PENDING
        ).exists():
            admission_status = "PENDING"

        else:
            admission_status = "UNPAID"

        # =====================================================
        # 🔹 COURSE FEE STATUS
        # =====================================================

        # 1️⃣ FULL PAYMENT (Status Based)
        full_payment = payments.filter(
            payment_type=FeePayment.PaymentType.FULL_PAYMENT
        ).order_by('-payment_date').first()

        if full_payment:
            if full_payment.payment_status == FeePayment.PaymentStatus.COMPLETED:
                course_status = "COMPLETED"
            elif full_payment.payment_status == FeePayment.PaymentStatus.PENDING:
                course_status = "PENDING"
            else:
                course_status = "UNPAID"

        else:
            # 2️⃣ INSTALLMENT LOGIC (Installment-number Based)
            installments = payments.filter(
                payment_type=FeePayment.PaymentType.INSTALLMENT
            )

            if not installments.exists():
                course_status = "UNPAID"

            else:
                # If ANY installment is pending → PENDING
                if installments.filter(
                    payment_status=FeePayment.PaymentStatus.PENDING
                ).exists():
                    course_status = "PENDING"

                else:
                    # Get latest completed installment
                    latest_completed = installments.filter(
                        payment_status=FeePayment.PaymentStatus.COMPLETED
                    ).order_by('-installment_number').first()

                    if not latest_completed:
                        course_status = "UNPAID"

                    else:
                        latest_number = latest_completed.installment_number or 0
                        total_installments = latest_completed.total_installments or 0

                        if total_installments > 0 and latest_number == total_installments:
                            course_status = "COMPLETED"
                        else:
                            course_status = "IN PROGRESS"

        # =====================================================
        # 🔹 STATUS FILTER
        # =====================================================

        if status_filter and course_status != status_filter:
            continue

        student_data.append({
            "id": student.id,
            "name": student.full_name,
            "course": course.name if course else "—",
            "course_fee": course_fee,
            "admission_status": admission_status,
            "course_status": course_status,
        })

    return render(request, "bdm/payments/course_fee.html", {
        "students": student_data
    })
    
@role_required('admin')
def payment_history(request, student_id):
    # ================= GET STUDENT =================
    student = get_object_or_404(Student, id=student_id)

    # ================= HANDLE STATUS UPDATE =================
    if request.method == "POST":
        payment_id = request.POST.get("payment_id")
        new_status = request.POST.get("status")

        payment = get_object_or_404(FeePayment, id=payment_id, student=student)
        if new_status in dict(FeePayment.PaymentStatus.choices).keys():
            payment.payment_status = new_status
            payment.save()
            messages.success(request, f"Payment status updated to {payment.get_payment_status_display()}.")
        else:
            messages.error(request, "Invalid status selected.")

        return redirect("bdm:payment_history", student_id=student.id)

    # ================= GET BATCH & COURSE =================
    batch = student.batches.first()
    course = batch.course if batch else None
    course_fee = course.course_fee if course else Decimal("0.00")

    # ================= PREFETCH PAYMENTS =================
    payments = FeePayment.objects.filter(student=student).prefetch_related(
        Prefetch('documents', queryset=PaymentDocument.objects.all())
    )

    # ================= PAYMENT TYPES =================
    admission_payments = payments.filter(payment_type=FeePayment.PaymentType.ADMISSION)
    booking_payments = payments.filter(payment_type=FeePayment.PaymentType.BOOKING)
    installments = payments.filter(payment_type=FeePayment.PaymentType.INSTALLMENT)
    full_payment = payments.filter(payment_type=FeePayment.PaymentType.FULL_PAYMENT).first()
    late_fees = payments.filter(payment_type=FeePayment.PaymentType.LATE_FEE)
    other_payments = payments.filter(payment_type=FeePayment.PaymentType.OTHER)

    # ================= ADMISSION STATUS =================
    if not admission_payments.exists():
        admission_status = "UNPAID"
    elif admission_payments.filter(payment_status=FeePayment.PaymentStatus.COMPLETED).exists():
        admission_status = "PAID"
    elif admission_payments.filter(payment_status=FeePayment.PaymentStatus.PENDING).exists():
        admission_status = "PENDING"
    else:
        admission_status = "UNPAID"

    # ================= PAYMENT SUMMARY =================
    # Default summary values
    total_paid = Decimal("0.00")
    balance = course_fee
    progress = 0

    # Include ADMISSION + INSTALLMENT + FULL PAYMENT
    course_payments = payments.filter(
    payment_type__in=[
        FeePayment.PaymentType.ADMISSION,
        FeePayment.PaymentType.INSTALLMENT,
        FeePayment.PaymentType.FULL_PAYMENT,
    ]
    )

    # Sum only COMPLETED payments
    total_paid = sum(p.amount for p in course_payments if p.payment_status == FeePayment.PaymentStatus.COMPLETED)

    # Calculate balance and progress
    balance = course_fee - total_paid
    progress = int((total_paid / course_fee) * 100) if course_fee else 0

    # ================= COURSE FEE STATUS =================
    if full_payment:
        if full_payment.payment_status == FeePayment.PaymentStatus.COMPLETED:
            course_status = "COMPLETED"
        elif full_payment.payment_status == FeePayment.PaymentStatus.PENDING:
            course_status = "PENDING"
        else:
            course_status = "UNPAID"
    else:
        if not installments.exists():
            course_status = "UNPAID"
        elif installments.filter(payment_status=FeePayment.PaymentStatus.PENDING).exists():
            course_status = "PENDING"
        else:
            latest_completed = installments.filter(
                payment_status=FeePayment.PaymentStatus.COMPLETED
            ).order_by('-installment_number').first()
            if not latest_completed:
                course_status = "UNPAID"
            else:
                latest_number = latest_completed.installment_number or 0
                total_installments = latest_completed.total_installments or 0
                if total_installments > 0 and latest_number == total_installments:
                    course_status = "COMPLETED"
                else:
                    course_status = "IN PROGRESS"

    # ================= CONTEXT =================
    context = {
        "student": student,
        "course": course,
        "course_fee": course_fee,
        "total_paid": total_paid,
        "balance": balance,
        "admission_payments": admission_payments,
        "booking_payments": booking_payments,
        "installments": installments,
        "full_payment": full_payment,
        "late_fees": late_fees,
        "other_payments": other_payments,
        "admission_status": admission_status,
        "course_status": course_status,
        "progress": progress,
        "payment_status_choices": FeePayment.PaymentStatus.choices,
    }

    return render(request, "bdm/payments/payment_history.html", context)

#leave section-aleena
@role_required('admin')
def leave_view(request):
    status_filter = request.GET.get('status', 'all')
    student_name = request.GET.get('student')
    leave_type = request.GET.get('leave_type')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    leaves = LeaveApplication.objects.select_related(
        'student', 'batch', 'approved_by'
    ).all()

    # Status filter
    if status_filter != 'all':
        leaves = leaves.filter(status=status_filter)

    # Student name filter
    if student_name:
        leaves = leaves.filter(
            student__full_name__icontains=student_name
        )

    # Leave type filter
    if leave_type:
        leaves = leaves.filter(leave_type=leave_type)

    # Date range filter
    if from_date:
        leaves = leaves.filter(from_date__gte=from_date)

    if to_date:
        leaves = leaves.filter(to_date__lte=to_date)

    context = {
        'leaves': leaves,
        'total_count': LeaveApplication.objects.count(),
        'pending_count': LeaveApplication.objects.filter(status='pending').count(),
        'approved_count': LeaveApplication.objects.filter(status='approved').count(),
        'rejected_count': LeaveApplication.objects.filter(status='rejected').count(),
        'active_status': status_filter,
        'leave_types': LeaveApplication.LeaveType.choices,
    }

    return render(request, 'bdm/leave/leave.html', context)

@login_required
@role_required('admin')
def leave_detail(request, pk):
    leave = get_object_or_404(
        LeaveApplication.objects.select_related(
            'student', 'batch', 'approved_by'
        ),
        pk=pk
    )

    student = leave.student

    leave_stats = LeaveApplication.objects.filter(student=student).aggregate(
        total_count=Count('id'),
        approved_count=Count('id', filter=Q(status='approved')),
        pending_count=Count('id', filter=Q(status='pending')),
        rejected_count=Count('id', filter=Q(status='rejected')),

        # 👇 Rename this
        total_days_sum=Sum('total_days'),
        approved_days_sum=Sum('total_days', filter=Q(status='approved')),
        pending_days_sum=Sum('total_days', filter=Q(status='pending')),
        rejected_days_sum=Sum('total_days', filter=Q(status='rejected')),
    )

    return render(request, 'bdm/leave/leave_detail.html', {
        'leave': leave,
        'leave_stats': leave_stats
    })


#lesson-plan-Ramees


class BatchListView(ListView):
    model = Batch
    template_name = "bdm/academics/batchview.html"
    context_object_name = "batches"
    

class BatchAcademicDashboardView(DetailView):
    model = Batch
    template_name = "bdm/academics/batch_dashboard.html"
    context_object_name = "batch"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        batch = self.object
        context["modules"] = batch.course.modules.all()
        # context["progress"] = LessonSession.get_batch_progress(batch)
        return context    
    
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView
from .models import  Batch
from apps.trainer.models import Module

class ModuleDetailView(DetailView):
    model = Module
    template_name = "bdm/academics/module_detail.html"
    context_object_name = "module"

    def dispatch(self, request, *args, **kwargs):
        self.batch = get_object_or_404(Batch, id=kwargs["batch_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        lesson_plans = self.object.lessons.all()
        context["batch"] = self.batch

        sessions = LessonSession.objects.filter(
            batch=self.batch,
            lesson_plan__module=self.object
        ).select_related("trainer")

        session_map = {s.lesson_plan_id: s for s in sessions}

        # Attach session to each lesson plan
        for plan in lesson_plans:
            plan.assigned_session = session_map.get(plan.id)

        context["lesson_plans"] = lesson_plans

        return context
    
    
from django.views.generic import CreateView
from django.shortcuts import get_object_or_404
from django.urls import reverse
from .models import Batch
from apps.trainer.models import LessonPlan, LessonSession
from .form import LessonSessionForm


class AssignLessonSessionView(CreateView):
    model = LessonSession
    form_class = LessonSessionForm
    template_name = "bdm/academics/assign_lesson_session.html"

    def dispatch(self, request, *args, **kwargs):
        self.batch = get_object_or_404(Batch, id=kwargs["batch_id"])
        self.lesson_plan = get_object_or_404(LessonPlan, id=kwargs["plan_id"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.batch = self.batch
        form.instance.lesson_plan = self.lesson_plan
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "bdm:module_detail",
            kwargs={
                "batch_id": self.batch.id,
                "pk": self.lesson_plan.module.id
            }
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["batch"] = self.batch
        context["lesson_plan"] = self.lesson_plan
        return context      
    

    
class LessonSessionUpdateView(UpdateView):
    model = LessonSession
    form_class = LessonSessionForm
    template_name = "bdm/academics/assign_lesson_session.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["batch"] = self.object.batch
        context["lesson_plan"] = self.object.lesson_plan
        return context

    def get_success_url(self):
        return reverse(
            "bdm:module_detail",
            kwargs={
                "batch_id": self.object.batch.id,
                "pk": self.object.lesson_plan.module.id
            }
        )

class LessonSessionDeleteView(DeleteView):
    model = LessonSession
    template_name = "bdm/academics/session_confirm_delete.html"

    def get_success_url(self):
        return reverse(
            "bdm:module_detail",
            kwargs={
                "batch_id": self.object.batch.id,
                "pk": self.object.lesson_plan.module.id
            }
        )


#student_feedback section-aleena

@login_required
def student_feedback(request):
    feedback_type = request.GET.get('type', 'all')

    feedbacks = StudentFeedback.objects.select_related(
        'student', 'trainer', 'course', 'batch'
    )

    if feedback_type != 'all':
        feedbacks = feedbacks.filter(feedback_type=feedback_type)

    stats = StudentFeedback.objects.aggregate(
        total_feedback=Count('id'),
        avg_rating=Avg('overall_rating'),
        avg_content=Avg('content_quality'),
        avg_teaching=Avg('teaching_methodology'),
        avg_responsiveness=Avg('responsiveness'),
    )

    context = {
        'feedbacks': feedbacks,
        'stats': stats,
        'active_type': feedback_type,
    }

    return render(request, 'bdm/student_feedback/student_feedback.html', context)


#course section-aleena

@role_required('admin')
def course_list_view(request):
    courses = Course.objects.filter(is_active=True).order_by('-created_at')

    context = {
        'courses': courses
    }
    return render(request, 'bdm/course/course_list.html', context)

@role_required('admin')
def course_detail_view(request, pk):
    course = get_object_or_404(Course, pk=pk)
    modules = course.modules.all().order_by('module_number')

    if request.method == "POST":
        form = ModuleForm(request.POST)

        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.save()

            messages.success(request, "Module created successfully!")
            return redirect('bdm:course_detail', pk=course.pk)

    else:
        form = ModuleForm()

    context = {
        'course': course,
        'modules': modules,
        'form': form
    }

    return render(request, 'bdm/course/course_detail.html', context)

@role_required('admin')
def module_detail_view(request, pk):
    module = get_object_or_404(Module, pk=pk)
    lessons = module.lessons.all().order_by('session_number')

    if request.method == "POST":
        form = LessonPlanForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.module = module
            lesson.course = module.course
            lesson.save()

            messages.success(request, "Lesson Plan created successfully!")
            return redirect('bdm:module_detail', pk=module.pk)
    else:
        form = LessonPlanForm()

    context = {
        'module': module,
        'lessons': lessons,
        'form': form
    }

    return render(request, 'bdm/course/module_detail.html', context)


@login_required
@role_required('admin')
def course_create(request):
    if request.method == "POST":
        try:
            Course.objects.create(
                name=request.POST.get("name"),
                description=request.POST.get("description"),
                duration=request.POST.get("duration"),
                tech_stack=request.POST.get("tech_stack"),
                course_fee=request.POST.get("course_fee"),
                syllabus=request.POST.get("syllabus"),
                is_active=request.POST.get("is_active") == "on",
            )

            messages.success(request, "Course created successfully!")
            return redirect("bdm:course_list")

        except Exception as e:
            messages.error(request, f"Error creating course: {e}")
            return redirect("bdm:course_list")

    return redirect("bdm:course_list")





#trainer-page-aleena
@role_required('admin')
def trainer_list_view(request):
    trainers = Trainer.objects.all().select_related(
        "user", "admin_profile"
    ).prefetch_related("batches")

    # 🔎 Search
    search_query = request.GET.get("search")
    if search_query:
        trainers = trainers.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(primary_domain__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    # 🎯 Domain Filter
    domain = request.GET.get("domain")
    if domain:
        trainers = trainers.filter(primary_domain__icontains=domain)

    # 📦 Assignment Filter
    assignment = request.GET.get("assignment")

    if assignment == "assigned":
        trainers = trainers.filter(batches__isnull=False).distinct()

    elif assignment == "unassigned":
        trainers = trainers.filter(batches__isnull=True)

    # 🟢 Status Filter
    status = request.GET.get("status")

    if status == "active":
        trainers = trainers.filter(admin_profile__is_active=True)

    elif status == "inactive":
        trainers = trainers.filter(admin_profile__is_active=False)

    elif status == "pending":
        trainers = trainers.filter(admin_profile__profile_verified=False)

    context = {
        "trainers": trainers,
    }

    return render(request, "bdm/trainer/trainer_list.html", context)

def trainer_detail_view(request, pk):
    trainer = get_object_or_404(Trainer, pk=pk)

    if request.method == "POST":

        # 🔁 Toggle Active Status
        if "toggle_active" in request.POST:
            if hasattr(trainer, "admin_profile"):
                profile = trainer.admin_profile
                profile.is_active = not profile.is_active
                profile.save()
                messages.success(request, "Trainer active status updated.")

            return redirect("bdm:trainer_detail", pk=pk)

        # 📦 Assign Batch
        if "assign_batch" in request.POST:
            batch_id = request.POST.get("batch_id")

            if batch_id:
                batch = get_object_or_404(Batch, id=batch_id)

                if trainer in batch.trainers.all():
                    messages.warning(request, "Trainer is already assigned to this batch.")
                else:
                    batch.trainers.add(trainer)
                    messages.success(request, "Trainer successfully assigned to batch.")

            return redirect("bdm:trainer_detail", pk=pk)

    available_batches = Batch.objects.exclude(trainers=trainer)

    context = {
        "trainer": trainer,
        "available_batches": available_batches,
    }

    return render(request, "bdm/trainer/trainer_detail.html", context)



#studentissue -aleena

def student_issue_list(request):
    issues = StudentIssue.objects.select_related(
        'student', 'assigned_to'
    ).all()

    # Filters
    issue_type = request.GET.get('issue_type')
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    search = request.GET.get('search')

    if issue_type:
        issues = issues.filter(issue_type=issue_type)

    if status:
        issues = issues.filter(status=status)

    if priority:
        issues = issues.filter(priority=priority)

    if search:
        issues = issues.filter(
            Q(subject__icontains=search) |
            Q(description__icontains=search)
        )

    # Pagination
    paginator = Paginator(issues, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'issues': page_obj,
        'page_obj': page_obj,
        'issue_types': StudentIssue.IssueType.choices,
        'statuses': StudentIssue.Status.choices,
        'priorities': StudentIssue.Priority.choices,
    }

    return render(request, 'bdm/student_issue/student_issue_list.html', context)



def student_issue_detail(request, pk):
    issue = get_object_or_404(StudentIssue, pk=pk)

    # Get only trainers (adjust filter based on your role system)
    trainers = User.objects.filter(groups__name='Trainer')

    if request.method == "POST":
        trainer_id = request.POST.get('trainer')

        if trainer_id:
            trainer = get_object_or_404(User, pk=trainer_id)

            issue.assigned_to = trainer
            issue.status = StudentIssue.Status.IN_PROGRESS
            issue.save()

            messages.success(request, "Issue assigned successfully.")
            return redirect('bdm:student_issue_detail', pk=issue.pk)

    context = {
        'issue': issue,
        'trainers': trainers
    }

    return render(request, 'bdm/student_issue/student_issue_detail.html', context)




# Ramees-Student view


from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.db.models import Count
from apps.bdm.models import Student, Batch
from apps.student.models import FeePayment
from apps.student.models import LMSAccess
from apps.bdm.models import OnboardingChecklist



class StudentListView(ListView):
    model = Student
    template_name = "bdm/student/student_list.html"
    context_object_name = "students"
    paginate_by = 20

    def get_queryset(self):
        return Student.objects.select_related("user").prefetch_related("batches")

    
    
class StudentDashboardView(DetailView):
    model = Student
    template_name = "bdm/student/student_dashboard.html"
    context_object_name = "student"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object

        # Batch
        batch = student.batches.first()

        # Progress
        from apps.trainer.models import LessonSession
        progress = None
        if batch:
            progress = LessonSession.get_batch_progress(batch)

        # Attendance
        from apps.trainer.models import Attendance
        attendance = 0
        if batch:
            attendance = Attendance.calculate_attendance_percentage(student, batch)

        # Tasks
        from apps.trainer.models import TaskSubmission
        pending_tasks = TaskSubmission.get_student_pending_tasks(student)
        overdue_tasks = TaskSubmission.get_student_overdue_tasks(student)

        # Fees
        fee_summary = FeePayment.get_payment_summary(student)

        # Documents
        documents = student.documents.all()

        # Onboarding
        onboarding = getattr(student, "onboarding_checklist", None)

        # LMS
        lms = getattr(student, "lms_access", None)

        context.update({
            "batch": batch,
            "progress": progress,
            "attendance": attendance,
            "pending_tasks": pending_tasks,
            "overdue_tasks": overdue_tasks,
            "fee_summary": fee_summary,
            "documents": documents,
            "onboarding": onboarding,
            "lms": lms
        })

        return context    
    
from django.views import View
from django.shortcuts import redirect

class ToggleStudentStatusView(View):
    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        student.is_active = not student.is_active
        student.save()
        return redirect("student_dashboard", pk=pk)
    
    
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import timedelta

# Import all models from bdm
from apps.bdm.models import (
    Lead, Course, Trainer, Student, Batch,
    StudentAdminProfile, TeleCallerProfile,
    CallHistory, PaymentReminder, PDCCollection,
    OnboardingChecklist, StudentIssue, Notification,
    BatchSchedule,
)

# Import student app models
from apps.student.models import FeePayment, StudentDocument, EnrollmentAgreement







# New dashboard -ramees


@login_required
@role_required('admin')
def dashboard(request):
    today = timezone.now().date()
    now = timezone.now()
    month_start = today.replace(day=1)

    # ── STAT CARDS ──────────────────────────────────────────────
    total_students = Student.objects.count()
    active_students = StudentAdminProfile.objects.filter(is_active=True).count()

    active_batches = Batch.objects.filter(is_active=True).count()
    completing_soon = Batch.objects.filter(
        is_active=True,
        expected_finish_date__lte=today + timedelta(days=14)
    ).count()

    # Revenue this month
    revenue_this_month = FeePayment.objects.filter(
        payment_date__date__gte=month_start,
        payment_status=FeePayment.PaymentStatus.COMPLETED,
    ).aggregate(total=Sum('amount'))['total'] or 0

    revenue_last_month = FeePayment.objects.filter(
        payment_date__date__gte=(month_start - timedelta(days=30)).replace(day=1),
        payment_date__date__lt=month_start,
        payment_status=FeePayment.PaymentStatus.COMPLETED,
    ).aggregate(total=Sum('amount'))['total'] or 1  # avoid div-by-zero

    revenue_change_pct = round(
        ((revenue_this_month - revenue_last_month) / revenue_last_month) * 100, 1
    )

    # Leads
    total_leads = Lead.objects.count()
    new_leads = Lead.objects.filter(status=Lead.LeadStatus.NEW).count()
    assigned_leads = Lead.objects.filter(status=Lead.LeadStatus.ASSIGNED).count()
    converted_leads = Lead.objects.filter(status=Lead.LeadStatus.CONVERTED).count()
    idle_leads = Lead.objects.filter(status=Lead.LeadStatus.IDLE).count()
    dropped_leads = Lead.objects.filter(status=Lead.LeadStatus.DROPPED).count()

    conversion_rate = round(
        (converted_leads / total_leads * 100) if total_leads else 0, 1
    )

    # Leads needing follow-up (last_followup > 3 days ago or never)
    followup_due = Lead.objects.filter(
        status__in=[Lead.LeadStatus.ASSIGNED, Lead.LeadStatus.IDLE],
    ).filter(
        Q(last_followup__isnull=True) |
        Q(last_followup__lt=now - timedelta(days=3))
    ).count()

    # ── BATCH PROGRESS ──────────────────────────────────────────
    batches_with_progress = []
    for batch in Batch.objects.filter(is_active=True).select_related('course').prefetch_related('trainers')[:6]:
        total_sessions = batch.lesson_sessions.count()
        completed_sessions = batch.lesson_sessions.filter(
            status='completed'
        ).count()
        progress_pct = round(
            (completed_sessions / total_sessions * 100) if total_sessions else 0
        )
        trainer = batch.trainers.first()
        batches_with_progress.append({
            'batch': batch,
            'progress': progress_pct,
            'completed': completed_sessions,
            'total': total_sessions,
            'trainer': trainer,
        })

    # ── ATTENDANCE OVERVIEW ─────────────────────────────────────
    # Import Attendance from the tracker app
    try:
        from apps.trainer.models import Attendance
        # Today's attendance across all batches
        today_records = Attendance.objects.filter(date=today)
        today_present = today_records.filter(status__in=['present', 'late']).count()
        today_total = today_records.count()
        today_attendance_pct = round(
            (today_present / today_total * 100) if today_total else 0
        )

        # Last 6 days for mini bar chart
        attendance_week = []
        for i in range(6, 0, -1):
            day = today - timedelta(days=i)
            recs = Attendance.objects.filter(date=day)
            present = recs.filter(status__in=['present', 'late']).count()
            total = recs.count()
            pct = round((present / total * 100) if total else 0)
            attendance_week.append({'day': day.strftime('%a'), 'pct': pct})

        # Overall average
        overall_attendance = Attendance.objects.filter(
            date__gte=month_start
        ).aggregate(
            present=Count('id', filter=Q(status__in=['present', 'late'])),
            total=Count('id')
        )
        overall_avg = round(
            (overall_attendance['present'] / overall_attendance['total'] * 100)
            if overall_attendance['total'] else 0
        )
    except Exception:
        today_attendance_pct = 0
        attendance_week = [
            {'day': (today - timedelta(days=i)).strftime('%a'), 'pct': 0}
            for i in range(6, 0, -1)
        ]
        overall_avg = 0

    # ── FEE COLLECTION ──────────────────────────────────────────
    fee_summary = FeePayment.objects.filter(
        payment_date__date__gte=month_start
    ).aggregate(
        completed=Sum('amount', filter=Q(payment_status=FeePayment.PaymentStatus.COMPLETED)),
        pending=Sum('amount', filter=Q(payment_status=FeePayment.PaymentStatus.PENDING)),
    )
    fee_collected = fee_summary['completed'] or 0
    fee_pending = fee_summary['pending'] or 0
    fee_total = fee_collected + fee_pending
    fee_collected_pct = round((fee_collected / fee_total * 100) if fee_total else 0)

    # Fee by type breakdown (for donut)
    booking_amt = FeePayment.objects.filter(
        payment_date__date__gte=month_start,
        payment_type=FeePayment.PaymentType.BOOKING,
        payment_status=FeePayment.PaymentStatus.COMPLETED,
    ).aggregate(t=Sum('amount'))['t'] or 0

    full_pay_amt = FeePayment.objects.filter(
        payment_date__date__gte=month_start,
        payment_type=FeePayment.PaymentType.FULL_PAYMENT,
        payment_status=FeePayment.PaymentStatus.COMPLETED,
    ).aggregate(t=Sum('amount'))['t'] or 0

    emi_amt = FeePayment.objects.filter(
        payment_date__date__gte=month_start,
        payment_type=FeePayment.PaymentType.INSTALLMENT,
        payment_status=FeePayment.PaymentStatus.COMPLETED,
    ).aggregate(t=Sum('amount'))['t'] or 0

    # ── ONBOARDING STATUS ───────────────────────────────────────
    pending_onboarding = OnboardingChecklist.objects.filter(
        onboarding_completed=False
    ).select_related('student').order_by('-updated_at')[:5]

    completed_onboarding_month = OnboardingChecklist.objects.filter(
        onboarding_completed=True,
        completed_date__gte=month_start,
    ).count()

    # ── NOTIFICATIONS / RECENT ACTIVITY ─────────────────────────
    recent_notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:10]

    # Recent fee payments (admission fee received events)
    recent_payments = FeePayment.objects.filter(
        payment_status=FeePayment.PaymentStatus.COMPLETED,
    ).select_related('student').order_by('-payment_date')[:5]

    # Recent document uploads
    recent_docs = StudentDocument.objects.select_related(
        'student'
    ).order_by('-uploaded_at')[:4]

    # Recent enrollment agreements signed
    recent_enrollments = EnrollmentAgreement.objects.filter(
        is_signed=True
    ).select_related('student').order_by('-signed_at')[:4]

    # Recent leads
    recent_leads = Lead.objects.order_by('-enquiry_date')[:5]

    # Build a unified activity feed sorted by time
    activity_feed = []

    for p in recent_payments:
        activity_feed.append({
            'type': 'payment',
            'icon': '💳',
            'color': 'green',
            'text': f"<strong>{p.student.full_name or p.student.user.get_full_name()}</strong> paid ₹{p.amount:,.0f} ({p.get_payment_type_display()})",
            'time': p.payment_date,
        })

    for d in recent_docs:
        activity_feed.append({
            'type': 'document',
            'icon': '📄',
            'color': 'blue',
            'text': f"<strong>{d.student.full_name or d.student.user.get_full_name()}</strong> uploaded {d.get_document_type_display()}",
            'time': d.uploaded_at,
        })

    for e in recent_enrollments:
        activity_feed.append({
            'type': 'enrollment',
            'icon': '✍️',
            'color': 'violet',
            'text': f"<strong>{e.student.full_name or e.student.user.get_full_name()}</strong> signed enrollment agreement",
            'time': e.signed_at,
        })

    for lead in recent_leads:
        activity_feed.append({
            'type': 'lead',
            'icon': '🎯',
            'color': 'amber',
            'text': f"New lead <strong>{lead.name}</strong> enquired about {lead.preferred_course.name if lead.preferred_course else 'a course'}",
            'time': lead.enquiry_date,
        })

    # Sort by time descending, take top 12
    activity_feed.sort(key=lambda x: x['time'], reverse=True)
    activity_feed = activity_feed[:12]

    # Format time as "X min ago" etc.
    def time_ago(dt):
        if not dt:
            return ''
        diff = now - dt
        s = int(diff.total_seconds())
        if s < 60:
            return 'just now'
        if s < 3600:
            return f"{s // 60} min ago"
        if s < 86400:
            return f"{s // 3600} hr ago"
        return f"{diff.days} days ago"

    for item in activity_feed:
        item['time_ago'] = time_ago(item['time'])

    # ── PENDING ISSUES ───────────────────────────────────────────
    open_issues = StudentIssue.objects.filter(
        status__in=[StudentIssue.Status.OPEN, StudentIssue.Status.IN_PROGRESS]
    ).select_related('student').order_by('-created_at')[:5]

    urgent_issues = StudentIssue.objects.filter(
        status=StudentIssue.Status.OPEN,
        priority=StudentIssue.Priority.URGENT
    ).count()

    # ── COURSES ──────────────────────────────────────────────────
    total_courses = Course.objects.filter(is_active=True).count()

    # ── UNREAD NOTIFICATIONS ─────────────────────────────────────
    unread_notif_count = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).count()

    context = {
        # Stats
        'total_students': total_students,
        'active_students': active_students,
        'active_batches': active_batches,
        'completing_soon': completing_soon,
        'revenue_this_month': revenue_this_month,
        'revenue_change_pct': revenue_change_pct,
        'total_leads': total_leads,
        'new_leads': new_leads,
        'assigned_leads': assigned_leads,
        'converted_leads': converted_leads,
        'idle_leads': idle_leads,
        'dropped_leads': dropped_leads,
        'followup_due': followup_due,
        'conversion_rate': conversion_rate,
        'total_courses': total_courses,

        # Batch progress
        'batches_with_progress': batches_with_progress,

        # Attendance
        'today_attendance_pct': today_attendance_pct,
        'attendance_week': attendance_week,
        'overall_avg': overall_avg,

        # Fee collection
        'fee_collected': fee_collected,
        'fee_pending': fee_pending,
        'fee_collected_pct': fee_collected_pct,
        'booking_amt': booking_amt,
        'full_pay_amt': full_pay_amt,
        'emi_amt': emi_amt,

        # Onboarding
        'pending_onboarding': pending_onboarding,
        'completed_onboarding_month': completed_onboarding_month,

        # Activity
        'activity_feed': activity_feed,
        'recent_notifications': recent_notifications,
        'unread_notif_count': unread_notif_count,

        # Issues
        'open_issues': open_issues,
        'urgent_issues': urgent_issues,

        # Meta
        'today': today,
        'now': now,
    }

    return render(request, 'bdm/dashboard/dashboard2.html', context)    

#announcement -aleena

def announcement_list(request):
    now = timezone.now()

    announcements = Announcement.objects.filter(
        models.Q(expiry_date__isnull=True) | 
        models.Q(expiry_date__gt=now)
    ).order_by('-publish_date')

    return render(request, "bdm/announcements/announcement_list.html", {
        "announcements": announcements
    })


def announcement_create(request):
    if request.method == "POST":
        Announcement.objects.create(
            title=request.POST.get("title"),
            message=request.POST.get("message"),
            audience=request.POST.get("audience"),
            is_important=bool(request.POST.get("is_important")),
            expiry_date=request.POST.get("expiry_date") or None,
            created_by=request.user
        )

        messages.success(request, "Announcement created successfully 🎉")
        return redirect("bdm:announcement_list")
    
    
    #trainer leave-aleena

def trainer_leave_list(request):
    leaves = TrainerLeave.objects.select_related(
        "trainer", "trainer__user"
    ).order_by("-applied_at")

    leave_type = request.GET.get("leave_type")
    status = request.GET.get("status")
    q = request.GET.get("q")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")

    if q:
        leaves = leaves.filter(trainer__user__username__icontains=q)

    if leave_type:
        leaves = leaves.filter(leave_type=leave_type)

    if status:
        leaves = leaves.filter(status=status)

    if date_from and date_to:
        leaves = leaves.filter(
            start_date__lte=date_to,
            end_date__gte=date_from
        )

    context = {
        "leaves": leaves,
        "pending_count": TrainerLeave.objects.filter(status="PENDING").count(),
        "leave_type_choices": TrainerLeave._meta.get_field("leave_type").choices,
        "status_choices": TrainerLeave._meta.get_field("status").choices,
    }

    return render(request, "bdm/leave/trainer_leave_list.html", context)

def trainer_leave_detail(request, pk):
    leave = get_object_or_404(TrainerLeave, pk=pk)
    return render(request, "bdm/leave/trainer_leave_detail.html", {
        "leave": leave
    })
    
@require_POST
def update_trainer_leave_status(request, pk):
    leave = get_object_or_404(TrainerLeave, pk=pk)

    if leave.status != TrainerLeave.LeaveStatus.PENDING:
        messages.warning(request, "This leave has already been processed.")
        return redirect("bdm:trainer_leave_detail", pk=pk)

    action = request.POST.get("action")  # 'approve' or 'reject'
    remarks = request.POST.get("remarks")

    if action == "approve":
        leave.status = TrainerLeave.LeaveStatus.APPROVED
        messages.success(request, "Leave approved successfully.")
    elif action == "reject":
        leave.status = TrainerLeave.LeaveStatus.REJECTED
        messages.success(request, "Leave rejected.")

    leave.bdm_remarks = remarks
    leave.decision_at = timezone.now()
    leave.save()

    return redirect("bdm:trainer_leave_detail", pk=pk)