#rinta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.utils.timezone import now
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse, FileResponse,HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from decimal import Decimal
from dateutil.relativedelta import relativedelta
import uuid
import requests
import os
import calendar
from apps.bdm.models import Student, Trainer, Course, Batch,StudentAdminProfile, OnboardingChecklist,StudentIssue, PaymentDocument,Announcement,Notification, Admission
from apps.accounts.decorators import role_required
from apps.trainer.models import Module, LessonPlan, TaskSubmission, Task, LessonSession, Attendance, SessionMaterial,Exam,ExamResult,ExamSubmission,Certificate
from apps.accounts.decorators import role_required
from apps.student.models import LeaveApplication
from .models import FeePayment, StudentDocument,EnrollmentAgreement, StudentIDCard,StudentFeedback
from .forms import EnrollmentAgreementForm,TaskSubmissionForm
from apps.student.forms import LeaveApplicationForm,StudentIssueForm
from django.core.paginator import Paginator
from django.db.models import Count, Q
from collections import defaultdict
from datetime import date

from datetime import timedelta
import re
#rinta


#Edit Profile

@login_required
def stud_profile(request):
    # ✅ ALWAYS define first
    student = get_object_or_404(Student, user=request.user)

    if request.method == "POST":
        student.full_name = request.POST.get("full_name", "")
        student.gender = request.POST.get("gender", "")
        student.phone = request.POST.get("phone", "")
        student.bio = request.POST.get("bio", "")
        student.current_education = request.POST.get("current_education", "")
        student.institution = request.POST.get("institution", "")
        student.learning_goals = request.POST.get("learning_goals", "")
        student.preferred_domain = request.POST.get("preferred_domain", "")
        student.skills = request.POST.get("skills", "")
        student.experience_level = request.POST.get("experience_level", "")
        student.portfolio_url = request.POST.get("portfolio_url", "")

        if request.FILES.get("profile_photo"):
            student.profile_photo = request.FILES["profile_photo"]

        student.save()
        messages.success(request, "Profile updated successfully")
        return redirect("student:stud_profile")

    # ✅ GET request safe now
    return render(request, "student/profile/profile.html", {
        "student": student
    })



#Profile Overview

@login_required
def overview(request):
    student = request.user.student
    return render(request, "student/profile/overview.html", {
        "student": student
    })


#Change Password

@login_required
def password(request):
    user = request.user

    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        # 🔴 Check current password
        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect")
            return redirect("student:password")

        # 🔴 Check new passwords match
        if new_password != confirm_password:
            messages.error(request, "New passwords do not match")
            return redirect("student:password")

        # 🔴 Password length validation
        if len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters")
            return redirect("student:password")

        # ✅ Set new password
        user.set_password(new_password)
        user.save()

        # 🔐 Keep user logged in
        update_session_auth_hash(request, user)

        messages.success(request, "Password updated successfully")
        return redirect("student:password")

    return render(request, "student/profile/password.html")







def stud_feedback(request):

    student = Student.objects.get(user=request.user)

    # ✅ Student → Batch (ManyToMany)
    batch = student.batches.filter(is_active=True).first()

    if request.method == "POST":

        if not request.POST.get("feedback_type"):
            messages.error(request, "❌ Please select feedback type")
            return redirect("student:stud_feedback")

        if not request.POST.get("overall_rating"):
            messages.error(request, "❌ Overall rating is required")
            return redirect("student:stud_feedback")

        StudentFeedback.objects.create(
            student=student,
            feedback_type=request.POST.get("feedback_type"),
            trainer_id=request.POST.get("trainer") or None,

            # ✅ SAFE RELATIONS
            course=batch.course if batch else None,
            batch=batch,

            content_quality=request.POST.get("content_quality") or None,
            teaching_methodology=request.POST.get("teaching_methodology") or None,
            responsiveness=request.POST.get("responsiveness") or None,
            overall_rating=request.POST.get("overall_rating"),
            comments=request.POST.get("comments"),
            suggestions=request.POST.get("suggestions"),
            is_anonymous=True if request.POST.get("is_anonymous") else False,
        )

        messages.success(request, "✅ Feedback submitted successfully.")
        return redirect("student:stud_feedback")

    context = {
        "student": student,
        "batch": batch,

        # ✅ Batch → Trainers (ManyToMany)
        "trainers": batch.trainers.filter(user__is_active=True) if batch else [],
    }

    return render(request, "student/dashboard/stud_feedback.html", context)





@login_required
def student_attendance(request):

    student = request.user.student

    # ✅ ALWAYS GET ACTIVE BATCH FIRST
    batch = (
        student.batches
        .filter(is_active=True)
        .select_related("course")
        .prefetch_related("trainers__user")
        .first()
    )

    attendance_records = (
        Attendance.objects
        .filter(student=student, batch=batch)
        .select_related(
            "lesson_session",
            "lesson_session__lesson_plan",
            "marked_by",
            "marked_by__user"
        )
        .order_by("-date")
    )

    if not batch:
        return render(request, "student/dashboard/attendance.html", {
            "student": student,
            "attendance_records": [],
            "percentage": 0,
            "present_days": 0,
            "absent_days": 0,
            "excused_days": 0,
            "batch": None,
        })

    percentage = Attendance.calculate_attendance_percentage(student, batch)

    context = {
        "student": student,
        "batch": batch,
        "attendance_records": attendance_records,
        "percentage": percentage,
        "present_days": attendance_records.filter(status__in=['present', 'late']).count(),
        "absent_days": attendance_records.filter(status='absent').count(),
        "excused_days": attendance_records.filter(status='excused').count(),
    }

    return render(request, "student/dashboard/attendance.html", context)




@login_required
def student_leave(request):

    student = request.user.student

    # ✅ Active Batch
    batch = student.batches.filter(is_active=True).first()

    # ✅ Trainer (CORRECT SOURCE)
    trainer = batch.trainers.first() if batch else None

    # ✅ Leaves
    leaves = LeaveApplication.objects.filter(student=student, batch=batch)

    total_leaves = leaves.count()
    pending_leaves = leaves.filter(status="pending").count()
    approved_leaves = leaves.filter(status="approved").count()
    rejected_leaves = leaves.filter(status="rejected").count()

    # ✅ Form Handling
    if request.method == "POST":
        form = LeaveApplicationForm(request.POST, request.FILES)

        if form.is_valid():
            leave = form.save(commit=False)
            leave.student = student
            leave.batch = batch
            leave.save()

             # ✅ Notify trainer about leave application
            if trainer:
                Notification.objects.create(
                    recipient=trainer.user,
                    notification_type=Notification.NotificationType.GENERAL,
                    title="Leave Application Submitted",
                    message=f"{student.full_name} submitted a leave application.",
                    link_url=f"/trainer/leaves/"  # update this URL to match your trainer leaves page
                )

            messages.success(request, "Leave submitted successfully")
            return redirect("student:student_leave")

    else:
        form = LeaveApplicationForm()

    context = {
        "student": student,
        "batch": batch,
        "trainer": trainer,
        "form": form,
        "leaves": leaves,

        "total_leaves": total_leaves,
        "pending_leaves": pending_leaves,
        "approved_leaves": approved_leaves,
        "rejected_leaves": rejected_leaves,
    }

    return render(request, "student/dashboard/leaves.html", context)



@login_required
def student_evaluation(request):

    student = request.user.student
    submission_id = request.GET.get("submission")

    # ✅ PAGE 2 → INDIVIDUAL EVALUATION
    if submission_id:

        submission = (
            TaskSubmission.objects
            .select_related(
                "student",
                "student__user",
                "task",
                "task__batch",
                "task__lesson_session",
                "task__lesson_session__trainer",
                "task__lesson_session__lesson_plan",
            )
            .filter(id=submission_id, student=student)
            .first()
        )

        return render(
            request,
            "student/dashboard/individual_evaluation.html",
            {"submission": submission}
        )

    # ✅ PAGE 1 → LIST PAGE
    submissions = (
        TaskSubmission.objects
        .select_related("task", "task__batch")
        .filter(student=student)
        .order_by("-submitted_at")
    )

    evaluated_submissions = submissions.filter(
        marks_obtained__isnull=False
    )

    totals = evaluated_submissions.aggregate(
        obtained=Sum("marks_obtained"),
        total=Sum("task__total_marks")
    )

    obtained_marks = totals["obtained"] or 0
    total_marks = totals["total"] or 0

    percentage = 0
    if total_marks > 0:
        percentage = (obtained_marks / total_marks) * 100

    context = {
        "student": student,
        "submissions": submissions,
        "obtained_marks": obtained_marks,
        "total_marks": total_marks,
        "percentage": round(percentage, 2),
    }

    return render(
        request,
        "student/dashboard/Evaluation.html",
        context
    )
@login_required
def student_issues(request):

    student = (
        Student.objects
        .select_related("user")
        .prefetch_related("batches__trainers")
        .get(user=request.user)
    )

    # ✅ Active Batch
    batch = student.batches.filter(is_active=True).first()

    # ✅ Trainer
    trainer = batch.trainers.first() if batch else None

    # ✅ HANDLE POST
    if request.method == "POST":

        # ---------------- FEEDBACK SUBMISSION ----------------
        if "issue_id" in request.POST:

            try:
                issue = StudentIssue.objects.get(
                    id=request.POST.get("issue_id"),
                    student=student
                )

                issue.student_satisfied = (
                    request.POST.get("student_satisfied") == "true"
                )

                issue.satisfaction_comments = request.POST.get(
                    "satisfaction_comments"
                )

                issue.save()

                messages.success(request, "Feedback submitted ✅")

            except StudentIssue.DoesNotExist:
                messages.error(request, "Issue not found ❌")

            return redirect("student:student_issues")

        # ---------------- ISSUE SUBMISSION ----------------
        form = StudentIssueForm(request.POST)

        if form.is_valid():
            issue = form.save(commit=False)
            issue.student = student
            issue.save()

            from django.contrib.auth import get_user_model
            User = get_user_model()

            bdm_users = User.objects.filter(role="admin")

            for bdm in bdm_users:
                Notification.objects.create(
                    recipient=bdm,
                    notification_type=Notification.NotificationType.GENERAL,
                    title="New Student Issue Submitted",
                    message=f"{student.full_name} submitted a new issue.",
                    link_url="/bdm/issues/"  # update to your BDM issues URL
                )

            messages.success(request, "Issue submitted successfully ✅")
            return redirect("student:student_issues")

    else:
        form = StudentIssueForm()

    issues = StudentIssue.objects.filter(student=student)

    context = {
        "student": student,
        "batch": batch,
        "trainer": trainer,
        "form": form,
        "issues": issues,
    }

    return render(request, "student/dashboard/issues.html", context)



@login_required
def announcement_view(request):

    now = timezone.now()

    base_qs = Announcement.objects.filter(
        audience__in=["students", "both"]
    ).filter(
        Q(expiry_date__isnull=True) |
        Q(expiry_date__gt=now)
    ).order_by("-publish_date")

    # ✅ Active Tab
    active_tab = request.GET.get("tab", "all")

    # ✅ Pagination
    paginator = Paginator(base_qs, 5)   # 5 per page
    page_number = request.GET.get("page")

    announcements_all = paginator.get_page(page_number)

    announcements_trainer = base_qs.filter(
        created_by__trainer__isnull=False
    )

    announcements_bdm = base_qs.filter(
        created_by__trainer__isnull=True
    )

    return render(request, "student/dashboard/announcement.html", {
        "announcements_all": announcements_all,
        "announcements_trainer": announcements_trainer,
        "announcements_bdm": announcements_bdm,
        "active_tab": active_tab,
    })
@login_required
def notification_view(request):

    # MARK AS READ
    if request.method == "POST":

        notification_id = request.POST.get("notification_id")

        notification = Notification.objects.filter(
            id=notification_id,
            recipient=request.user
        ).first()

        if notification:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()

        return redirect("student:notification_view")

    # SHOW ONLY UNREAD
    notifications_list = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).order_by("-created_at")

    paginator = Paginator(notifications_list, 10)

    page_number = request.GET.get("page", 1)

    notifications = paginator.get_page(page_number)

    return render(
        request,
        "student/dashboard/notification.html",
        {"notifications": notifications}
    )


@login_required
def certificate_view(request):

    student = request.user.student

    certificate = Certificate.objects.filter(
        student=student,
        is_eligible=True
    ).first()

    # FORCE DOWNLOAD PROPERLY
    if request.GET.get("download") and certificate:
        if certificate.certificate_file:

            file_url = certificate.certificate_file.url
            file_name = file_url.split("/")[-1]

            response = requests.get(file_url)

            download_response = HttpResponse(
                response.content,
                content_type="application/pdf"
            )
            download_response["Content-Disposition"] = f'attachment; filename="{file_name}"'

            return download_response

    context = {
        "certificate": certificate,
        "student": student
    }

    return render(request, "student/dashboard/certificate.html", context)








































































































































































































#Niranjana

@role_required("student")
def dashboard(request):

    student = request.user.student

    # ✅ SAFE STUDENT NAME
    student_name = (
        student.full_name
        or student.user.get_full_name()
        or student.user.first_name
        or student.user.username
    )

    admin_profile = getattr(student, "admin_profile", None)
    checklist, _ = OnboardingChecklist.objects.get_or_create(student=student)

    batch = (
        student.batches
        .filter(is_active=True)
        .select_related("course")
        .prefetch_related("trainers__user")
        .first()
    )

    # ✅ PROFILE PHOTO
    profile_photo = student.documents.filter(
        document_type=StudentDocument.DocumentType.PHOTO
    ).order_by('-id').first()

    if profile_photo and profile_photo.verification_status != StudentDocument.VerificationStatus.VERIFIED:
        profile_photo = None

    # ✅ ONBOARDING PROGRESS
    completed_steps = 0

    if checklist.documents_verified:
        completed_steps += 1

    enrollment_generated = checklist.enrollment_letter_generated
    enrollment_signed = checklist.enrollment_letter_signed

    if enrollment_signed:
        completed_steps += 1

    if getattr(checklist, "id_card_issued", False):
        completed_steps += 1

    # ✅ MARKS
    submissions = TaskSubmission.objects.filter(
        student=student,
        marks_obtained__isnull=False
    ).select_related("task")

    obtained_marks = submissions.aggregate(
        total=Sum("marks_obtained")
    )["total"] or 0

    task_ids = submissions.values_list("task_id", flat=True).distinct()

    total_marks = Task.objects.filter(
        id__in=task_ids
    ).aggregate(
        total=Sum("total_marks")
    )["total"] or 0

    percentage = 0
    if total_marks > 0:
        percentage = (obtained_marks / total_marks) * 100

    # =====================================================
    # ✅ ATTENDANCE (Late = Attendance)
    # =====================================================

    attendance = Attendance.objects.filter(
        student=student,
        batch=batch
    )

    present_count = attendance.filter(status__iexact="present").count()
    late_count = attendance.filter(status__iexact="late").count()
    absent_count = attendance.filter(status__iexact="absent").count()

    total_attendance = present_count + late_count + absent_count
    circumference = 339.3

    if total_attendance > 0:
        present_dash = ((present_count + late_count) / total_attendance) * circumference
        absent_dash = (absent_count / total_attendance) * circumference
        attendance_percentage = round(((present_count + late_count) / total_attendance) * 100, 1)
    else:
        present_dash = 0
        absent_dash = 0
        attendance_percentage = 0


    #  ATTENDANCE ALERT — latest completed session not marked
    attendance_alert = False

    if batch:
        latest_completed_session = LessonSession.objects.filter(
            batch=batch,
            status=LessonSession.SessionStatus.COMPLETED
        ).order_by('-completed_at').first()

        if latest_completed_session:
            already_marked = Attendance.objects.filter(
                student=student,
                batch=batch,
            ).filter(
                Q(lesson_session=latest_completed_session) |
                Q(date=latest_completed_session.actual_date)
            ).exists()

            if not already_marked:
                attendance_alert = True




    # ✅ LEARNING PROGRESS
    covered_percentage = 0
    pending_percentage = 0

    if batch:
        progress_data = LessonSession.get_batch_progress(batch)
        covered_percentage = progress_data["progress_percentage"]
        pending_percentage = 100 - covered_percentage

    # =====================================================
    # ✅ PAYMENT CARD LOGIC
    # =====================================================

    today = timezone.now().date()

    admission = Admission.objects.filter(
        student=student,
        status=Admission.AdmissionStatus.ACTIVE
    ).first()

    total_fee = Decimal("0")
    if admission and admission.total_fee:
        total_fee = admission.total_fee
    elif batch and batch.course:
        total_fee = batch.course.course_fee or Decimal("0")


    other_paid_amount = FeePayment.objects.filter(
        student=student,
        payment_status=FeePayment.PaymentStatus.COMPLETED
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    admission_fee_paid_amount = admission.admission_fee_amount if admission and admission.admission_fee_amount else Decimal("0.00")

    paid_amount = admission_fee_paid_amount + other_paid_amount
    balance = max(total_fee - paid_amount, Decimal("0.00"))

    payment_portal_unlocked = (
        checklist.onboarding_completed
        or (checklist.documents_verified and checklist.enrollment_letter_signed)
    )

   

    # Detect plan type from admission
    plan = ""
    if admission and admission.payment_plan:
        plan = admission.payment_plan.lower()

    has_full_payment = FeePayment.objects.filter(
        student=student,
        payment_type=FeePayment.PaymentType.FULL_PAYMENT,
        payment_status=FeePayment.PaymentStatus.COMPLETED
    ).exists()

    # For installment/emi/pdc — use the correct PaymentType per plan
    plan_type_map = {
        "installment": FeePayment.PaymentType.INSTALLMENT,
        "emi":         FeePayment.PaymentType.EMI,
        "pdc":         FeePayment.PaymentType.PDC,
    }
    plan_payment_type = plan_type_map.get(plan)

    has_installments = False
    next_installment = None
    overdue_installment = None
    completed_installments = 0
    total_installments = {"installment": 4, "emi": 6, "pdc": 5}.get(plan, 0)

    if plan_payment_type:
        has_installments = FeePayment.objects.filter(
            student=student,
            payment_type=plan_payment_type,
        ).exists()

        next_installment = FeePayment.objects.filter(
            student=student,
            payment_type=plan_payment_type,
                payment_status=FeePayment.PaymentStatus.PENDING,
        ).order_by("installment_number").first()

        overdue_installment = FeePayment.objects.filter(
            student=student,
                payment_type=plan_payment_type,
            payment_status=FeePayment.PaymentStatus.PENDING,
            due_date__lt=today,
        ).order_by("due_date").first()

        completed_installments = FeePayment.objects.filter(
            student=student,
            payment_type=plan_payment_type,
            payment_status=FeePayment.PaymentStatus.COMPLETED,
        ).count()

    # Determine payment card state
    if not payment_portal_unlocked:
        payment_card_state = "locked"
   
    elif has_full_payment or balance <= 0:
        payment_card_state = "full_paid"
    elif plan in ["installment", "emi", "pdc"]:
        payment_card_state = "installment"
    else:
        payment_card_state = "balance_due"

    # Legacy notification (for other parts of template)
    payment_notification = "No Pending Payments"
    payment_css = "success"
    pending_payment = None

    if balance > 0:
        overdue_payment = FeePayment.objects.filter(
            student=student,
            payment_status=FeePayment.PaymentStatus.PENDING,
            due_date__lt=today
        ).order_by("due_date").first()

        upcoming_payment = FeePayment.objects.filter(
            student=student,
            payment_status=FeePayment.PaymentStatus.PENDING
        ).order_by("due_date").first()

        if overdue_payment:
            payment_notification = "Payment Overdue"
            payment_css = "danger"
            pending_payment = overdue_payment
        else:
            payment_notification = "Payment Pending"
            payment_css = "warning"
            pending_payment = upcoming_payment

    # =====================================================
    # ✅ PENDING TASKS (not_started + in_progress)
    # =====================================================

    pending_tasks = []

    if batch:
        # Get all tasks belonging to sessions in this student's batch
        batch_tasks = Task.objects.filter(
            batch=batch
        ).order_by("due_date")

        for task in batch_tasks:
            # Find this student's submission for the task (if any)
            submission = TaskSubmission.objects.filter(
                task=task,
                student=student
            ).first()

            # Determine current status
            if submission:
                status = submission.status  # 'submitted', 'evaluated', 'in_progress', 'resubmit'
            else:
                status = "not_started"

            # Only include pending statuses
            if status in ["not_started", "in_progress"]:
                # Auto-priority based on days until due date
                if task.due_date:
                    days_left = (task.due_date - today).days
                    if days_left < 0:
                        priority = "high"   # overdue
                    elif days_left <= 1:
                        priority = "high"
                    elif days_left <= 4:
                        priority = "medium"
                    else:
                        priority = "low"
                else:
                    priority = "low"

                pending_tasks.append({
                    "id":       task.id,
                    "title":    task.title,
                    "due_date": task.due_date,
                    "priority": priority,
                    "status":   status,
                })

    pending_task_count = len(pending_tasks)


    #LATEST MATERIALS (from LMS SessionMaterial)


    latest_materials = []

    if batch:
        materials = SessionMaterial.objects.filter(
            lesson_session__batch=batch
        ).select_related('lesson_session__lesson_plan').order_by('-id')[:5]

        for m in materials:
            latest_materials.append({
                'id':            m.id,
                'title':         m.title,
                'material_type': m.material_type,
                'type_display':  m.get_material_type_display(),
                'session_number': m.lesson_session.lesson_plan.session_number if m.lesson_session and m.lesson_session.lesson_plan else '',
            })





    # ✅ CALENDAR
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(today.year, today.month)

    month_name = calendar.month_name[today.month]
    year = today.year
    today_day = today.day

    # ✅ ANNOUNCEMENTS — last 48 hours, for students or both
    
    cutoff = timezone.now() - timedelta(hours=48)

    announcements = Announcement.objects.filter(
        audience__in=['students', 'both'],
        publish_date__gte=cutoff,
    ).filter(
        Q(expiry_date__isnull=True) | Q(expiry_date__gt=timezone.now())
    ).order_by('-publish_date').select_related('created_by')




    # ✅ PLANNED SESSIONS
    planned_sessions = []

    if batch:
        planned_sessions = list(
            LessonSession.objects.filter(
                batch=batch,
                status=LessonSession.SessionStatus.PLANNED
            )
            .select_related("lesson_plan__module")
            .order_by(
                "lesson_plan__module__module_number",
                "lesson_plan__session_number",
            )[:5]  # limit to next 5 on dashboard
        )


    context = {
        "student": student,
        "student_name": student_name,

        "admin_profile": admin_profile,
        "profile_photo": profile_photo,
        "all_docs_verified": checklist.documents_verified,
        "batch": batch,
        "today": today,
        "checklist": checklist,
        "completed_steps": completed_steps,

        "obtained_marks": obtained_marks,
        "total_marks": total_marks,
        "percentage": round(percentage, 2),

        "present_count": present_count,
        "late_count": late_count,
        "absent_count": absent_count,
        "present_dash": round(present_dash, 1),
        "absent_dash": round(absent_dash, 1),
        "attendance_percentage": attendance_percentage,

        "covered_percentage": covered_percentage,
        "pending_percentage": pending_percentage,

        "payment_notification": payment_notification,
        "payment_css": payment_css,
        "pending_payment": pending_payment,

        "fee_balance": balance,
        "paid_amount": paid_amount,
        "total_fee": total_fee,

        "month_days": month_days,
        "month_name": month_name,
        "year": year,
        "today_day": today_day,


        "pending_tasks":      pending_tasks,
        "pending_task_count": pending_task_count,
        "latest_materials": latest_materials,
        "attendance_alert": attendance_alert,
        "announcements": announcements,
        "planned_sessions": planned_sessions,
        "payment_card_state":      payment_card_state,
        "payment_portal_unlocked": payment_portal_unlocked,
        "admission_fee_paid_amount":    admission_fee_paid_amount,
        "has_installments":        has_installments,
        "has_full_payment":        has_full_payment,
        "next_installment":        next_installment,
        "overdue_installment":     overdue_installment,
        "completed_installments":  completed_installments,
        "total_installments":      total_installments,
        "fee_balance":             balance,
        "paid_amount":             paid_amount,
        "total_fee":               total_fee,
    }

    return render(request, "student/dashboard/dashboard.html", context)











def _notify_bdm_payment(student, payment_plan_label, installment_number, amount):
    from django.contrib.auth import get_user_model
    User = get_user_model()

    bdm_users = User.objects.filter(role="admin")

    # ✅ Handle full payment (no installment number)
    if installment_number:
        detail = f"#{installment_number} of ₹{amount}"
    else:
        detail = f"of ₹{amount}"

    for bdm in bdm_users:
        Notification.objects.create(
            recipient=bdm,
            notification_type=Notification.NotificationType.GENERAL,
            title=f"{payment_plan_label} Submitted",
            message=f"{student.full_name} submitted {payment_plan_label} {detail}.",
        )






       
@login_required
def payment_portal(request):

    student = request.user.student

    admission = Admission.objects.filter(
        student=student,
        status=Admission.AdmissionStatus.ACTIVE
    ).first()

    if not admission:
        messages.error(request, "No active admission found.")
        return redirect("student:stud_dashboard")

    if not admission.payment_plan:
        messages.error(request, "Payment plan not assigned.")
        return redirect("student:stud_dashboard")

    plan = admission.payment_plan.lower()
    total_fee = admission.total_fee or Decimal("0.00")

    # =========================
    # PAYMENT SUMMARY
    # =========================

    admission_fee_paid_amount = Decimal("0.00")
    if admission.admission_fee_paid and admission.admission_fee_amount:
        admission_fee_paid_amount = admission.admission_fee_amount

    paid_amount = (
        FeePayment.objects.filter(
            student=student,
            payment_status=FeePayment.PaymentStatus.COMPLETED
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    pending_amount = max(total_fee - paid_amount, Decimal("0.00"))

    # =========================
    # INSTALLMENT
    # =========================

    if plan == "installment":

        today = date(2026, 9, 25)  # simulate date
        start_date = admission.admission_date.date()
        count = 4
        template = "student/payment/installment_payment.html"
        payment_type = FeePayment.PaymentType.INSTALLMENT

        original_pending = max(total_fee - admission_fee_paid_amount, Decimal("0.00"))
        installment_amount = (
            original_pending / Decimal(str(count))
        ).quantize(Decimal("0.01"))

        all_plan_payments = FeePayment.objects.filter(
            student=student,
            payment_type=payment_type
        )

        if request.method == "POST":
            installment_number = request.POST.get("installment_number")
            receipt_file = request.FILES.get("receipt")

            if installment_number:
                installment_number = int(installment_number)

                already_exists = FeePayment.objects.filter(
                    student=student,
                    payment_type=payment_type,
                    installment_number=installment_number
                ).exists()

                if not already_exists:
                    payment = FeePayment.objects.create(
                        student=student,
                        payment_type=payment_type,
                        installment_number=installment_number,
                        total_installments=count,
                        amount=installment_amount,
                        payment_method=FeePayment.PaymentMethod.UPI,
                        transaction_id=str(uuid.uuid4()),
                        payment_date=timezone.now(),
                        due_date=start_date + relativedelta(months=installment_number - 1, day=21),
                        payment_status=FeePayment.PaymentStatus.PENDING,
                        remarks="Submitted via portal",
                        received_by=None
                    )

                    if receipt_file:
                        PaymentDocument.objects.create(
                            fee_payment=payment,
                            document_type=PaymentDocument.DocumentType.RECEIPT,
                            document_file=receipt_file,
                            description="Installment payment receipt",
                            uploaded_by=request.user
                        )

                        _notify_bdm_payment(student, "Installment", installment_number, installment_amount)
                        messages.success(request, "Installment payment submitted successfully.")

                    messages.success(request, "Installment payment submitted successfully.")

                return redirect("student:payment_portal")

        selected_number = request.GET.get("pay")
        selected_summary = request.GET.get("summary")
        installments = _build_payment_list(
            all_plan_payments, count, start_date, today, installment_amount
        )
        summary_detail = _resolve_summary(installments, selected_summary)

        return render(request, template, {
            "student": student,
            "admission": admission,
            "total_fee": total_fee,
            "paid_amount": paid_amount,
            "pending_amount": pending_amount,
            "installments": installments,
            "selected_installment": int(selected_number) if selected_number else None,
            "selected_summary": int(selected_summary) if selected_summary else None,
            "summary_detail": summary_detail,
            "plan": plan,
        })

    # =========================
    # EMI
    # =========================

    if plan == "emi":

        today = date(2026, 9, 25)  # simulate date
        start_date = admission.admission_date.date()
        count = 6
        template = "student/payment/emi_payment.html"
        payment_type = FeePayment.PaymentType.EMI

        original_pending = max(total_fee - admission_fee_paid_amount, Decimal("0.00"))
        installment_amount = (
            original_pending / Decimal(str(count))
        ).quantize(Decimal("0.01"))

        all_plan_payments = FeePayment.objects.filter(
            student=student,
            payment_type=payment_type
        )

        if request.method == "POST":
            installment_number = request.POST.get("installment_number")
            receipt_file = request.FILES.get("receipt")

            if installment_number:
                installment_number = int(installment_number)

                already_exists = FeePayment.objects.filter(
                    student=student,
                    payment_type=payment_type,
                    installment_number=installment_number
                ).exists()

                if not already_exists:
                    payment = FeePayment.objects.create(
                        student=student,
                        payment_type=payment_type,
                        installment_number=installment_number,
                        total_installments=count,
                        amount=installment_amount,
                        payment_method=FeePayment.PaymentMethod.UPI,
                        transaction_id=str(uuid.uuid4()),
                        payment_date=timezone.now(),
                        due_date=start_date + relativedelta(months=installment_number - 1, day=21),
                        payment_status=FeePayment.PaymentStatus.PENDING,
                        remarks="Submitted via EMI portal",
                        received_by=None
                    )

                    if receipt_file:
                        PaymentDocument.objects.create(
                            fee_payment=payment,
                            document_type=PaymentDocument.DocumentType.RECEIPT,
                            document_file=receipt_file,
                            description="EMI payment receipt",
                            uploaded_by=request.user
                        )

                        _notify_bdm_payment(student, "EMI", installment_number, installment_amount)
                        messages.success(request, "EMI payment submitted successfully.")

                    messages.success(request, "EMI payment submitted successfully.")

                return redirect("student:payment_portal")

        selected_number = request.GET.get("pay")
        selected_summary = request.GET.get("summary")
        installments = _build_payment_list(
            all_plan_payments, count, start_date, today, installment_amount
        )
        summary_detail = _resolve_summary(installments, selected_summary)

        return render(request, template, {
            "student": student,
            "admission": admission,
            "total_fee": total_fee,
            "paid_amount": paid_amount,
            "pending_amount": pending_amount,
            "installments": installments,
            "selected_installment": int(selected_number) if selected_number else None,
            "selected_summary": int(selected_summary) if selected_summary else None,
            "summary_detail": summary_detail,
            "plan": plan,
        })

    # =========================
    # PDC
    # =========================

    if plan == "pdc":

        today = date(2026, 9, 25)  # simulate date
        start_date = admission.admission_date.date()
        count = 5
        template = "student/payment/pdc_payment.html"
        payment_type = FeePayment.PaymentType.PDC

        original_pending = max(total_fee - admission_fee_paid_amount, Decimal("0.00"))
        installment_amount = (
            original_pending / Decimal(str(count))
        ).quantize(Decimal("0.01"))

        all_plan_payments = FeePayment.objects.filter(
            student=student,
            payment_type=payment_type
        )

        if request.method == "POST":
            installment_number = request.POST.get("installment_number")
            cheque_file = request.FILES.get("receipt")

            if installment_number:
                installment_number = int(installment_number)

                already_exists = FeePayment.objects.filter(
                    student=student,
                    payment_type=payment_type,
                    installment_number=installment_number
                ).exists()

                if not already_exists:
                    payment = FeePayment.objects.create(
                        student=student,
                        payment_type=payment_type,
                        installment_number=installment_number,
                        total_installments=count,
                        amount=installment_amount,
                        payment_method=FeePayment.PaymentMethod.CHEQUE,
                        transaction_id=str(uuid.uuid4()),
                        payment_date=timezone.now(),
                        due_date=start_date + relativedelta(months=installment_number - 1, day=21),
                        payment_status=FeePayment.PaymentStatus.PENDING,
                        remarks="Submitted via PDC portal",
                        received_by=None
                    )

                    if cheque_file:
                        PaymentDocument.objects.create(
                            fee_payment=payment,
                            document_type=PaymentDocument.DocumentType.RECEIPT,
                            document_file=cheque_file,
                            description="PDC cheque image",
                            uploaded_by=request.user
                        )

                        _notify_bdm_payment(student, "PDC Cheque", installment_number, installment_amount)
                        messages.success(request, "PDC cheque submitted successfully.")


                    messages.success(request, "PDC cheque submitted successfully.")

                return redirect("student:payment_portal")

        selected_number = request.GET.get("pay")
        selected_summary = request.GET.get("summary")
        installments = _build_payment_list(
            all_plan_payments, count, start_date, today, installment_amount
        )
        summary_detail = _resolve_summary(installments, selected_summary)

        return render(request, template, {
            "student": student,
            "admission": admission,
            "total_fee": total_fee,
            "paid_amount": paid_amount,
            "pending_amount": pending_amount,
            "installments": installments,
            "selected_installment": int(selected_number) if selected_number else None,
            "selected_summary": int(selected_summary) if selected_summary else None,
            "summary_detail": summary_detail,
            "plan": plan,
        })

    # =========================
    # FULL PAYMENT
    # =========================

    if request.method == "POST":
        receipt_file = request.FILES.get("receipt")

        if receipt_file:
            already_exists = FeePayment.objects.filter(
                student=student,
                payment_type=FeePayment.PaymentType.FULL_PAYMENT,
                payment_status=FeePayment.PaymentStatus.PENDING
            ).exists()

            if not already_exists:
                payment = FeePayment.objects.create(
                    student=student,
                    payment_type=FeePayment.PaymentType.FULL_PAYMENT,
                    amount=pending_amount,
                    payment_method=FeePayment.PaymentMethod.UPI,
                    transaction_id=str(uuid.uuid4()),
                    payment_date=timezone.now(),
                    payment_status=FeePayment.PaymentStatus.PENDING,
                    remarks="Submitted via full payment portal",
                    received_by=None
                )

                if receipt_file:
                    PaymentDocument.objects.create(
                        fee_payment=payment,
                        document_type=PaymentDocument.DocumentType.RECEIPT,
                        document_file=receipt_file,
                        description="Full payment receipt",
                        uploaded_by=request.user
                    )

                _notify_bdm_payment(student, "Full Payment", None, pending_amount)
                messages.success(request, "Full payment submitted successfully.")

        return redirect("student:payment_portal")

    existing_payment = FeePayment.objects.filter(
        student=student,
        payment_type=FeePayment.PaymentType.FULL_PAYMENT
    ).order_by("-created_at").first()

    view_summary = request.GET.get("summary") == "1"

    return render(request, "student/payment/full_payment.html", {
        "student": student,
        "admission": admission,
        "total_fee": total_fee,
        "paid_amount": paid_amount,
        "pending_amount": pending_amount,
        "existing_payment": existing_payment,
        "view_summary": view_summary,
    })


# =========================
# HELPER FUNCTIONS
# =========================

def _build_payment_list(all_plan_payments, count, start_date, today, installment_amount):
    """Shared helper to build installment/EMI/PDC row list."""
    installments = []

    for i in range(1, count + 1):

        payment = all_plan_payments.filter(
            installment_number=i
        ).order_by("-created_at").first()

        due_date = start_date + relativedelta(months=i - 1, day=21)

        if payment and payment.payment_status == FeePayment.PaymentStatus.COMPLETED:
            display_status = "Paid"
            amount = payment.amount

        elif payment and payment.payment_status == FeePayment.PaymentStatus.PENDING:
            display_status = "Pending Verification"
            amount = payment.amount

        elif payment and payment.payment_status == FeePayment.PaymentStatus.FAILED:
            display_status = "Rejected"
            amount = installment_amount

        else:
            amount = installment_amount
            if today < due_date:
                display_status = "Upcoming"
            elif today == due_date:
                display_status = "Due Today"
            else:
                display_status = "Overdue"

        installments.append({
            "number": i,
            "amount": amount,
            "due_date": due_date,
            "display_status": display_status,
            "payment_date": payment.payment_date if payment else None,
            "payment_method_display": payment.get_payment_method_display() if payment else None,
            "transaction_id": payment.transaction_id if payment else None,
        })

    return installments


def _resolve_summary(installments, selected_summary):
    """Find the matching installment dict for the summary panel."""
    if not selected_summary:
        return None
    for ins in installments:
        if ins["number"] == int(selected_summary):
            return ins
    return None











@role_required("student")
def lessonplan(request):
    student = request.user.student

    # Get the batch for this student
    batch = student.batches.first()  # Assuming one batch per student
    if not batch:
        return render(request, 'student/lessonplan/lessonplan.html', {'error': 'No batch assigned yet.'})

    course = batch.course
    course_name = course.name

    # Get all modules for this course
    modules = Module.objects.filter(course=course).prefetch_related('lessons')

    # Prepare lessons dict keyed by module.id
    lessons_by_module = {}
    for module in modules:
        lessons_by_module[module.id] = LessonPlan.objects.filter(module=module).order_by('session_number')

    context = {
        'course_name': course_name,
        'modules': modules,
        'lessons_by_module': lessons_by_module,
    }
    return render(request, 'student/lessonplan/lessonplan.html', context)







@role_required("student")
def syllabus(request):
    student = request.user.student

    batch = student.batches.filter(is_active=True).select_related("course").first()

    course = None

    if batch:
        course = batch.course

        #  Remove extra blank lines from tech_stack
        if course.tech_stack:
            course.tech_stack = "\n".join(
                line.strip()
                for line in course.tech_stack.splitlines()
                if line.strip()
            )

        #  Remove extra blank lines from syllabus
        if course.syllabus:
            course.syllabus = "\n".join(
                line.strip()
                for line in course.syllabus.splitlines()
                if line.strip()
            )

    return render(request, "student/coursesyllabus/syllabus.html", {
        "course": course
    })












@role_required("student")
def batch_details(request):
    student = request.user.student

    batch = student.batches.filter(
        is_active=True
    ).select_related(
        "course"
    ).prefetch_related(
        "trainers__user"
    ).first()


    schedules = []
    if batch:
        schedules = list(
            batch.schedules.filter(is_active=True)
            .select_related("trainer__user")
            .order_by("day_of_week", "start_time")
        )



    modules_data       = []
    completed_sessions = []
    planned_sessions   = []
    pending_sessions   = []
    skipped_sessions   = []

    if batch:
        # One query — all sessions for this batch, with module info
        # Chain: LessonSession → lesson_plan → module
        all_sessions = list(
            LessonSession.objects.filter(batch=batch)
            .select_related("lesson_plan__module")
            .order_by(
                "lesson_plan__module__module_number",
                "lesson_plan__session_number",
            )
        )

        # All modules for this batch's course, in order
        modules = Module.objects.filter(
            course=batch.course
        ).order_by("module_number")

        # Build a dict per module — filter sessions in Python (no extra queries)
        for module in modules:
            module_sessions = [
                s for s in all_sessions
                if s.lesson_plan.module_id == module.id
            ]

            completed = [s for s in module_sessions if s.status == LessonSession.SessionStatus.COMPLETED]
            planned   = [s for s in module_sessions if s.status == LessonSession.SessionStatus.PLANNED]
            pending   = [s for s in module_sessions if s.status == LessonSession.SessionStatus.PENDING]
            skipped   = [s for s in module_sessions if s.status == LessonSession.SessionStatus.SKIPPED]

            modules_data.append({
                "module":          module,
                "completed":       completed,
                "planned":         planned,
                "pending":         pending,
                "skipped":         skipped,
                "completed_count": len(completed),
                "planned_count":   len(planned),
                "pending_count":   len(pending),
                "skipped_count":   len(skipped),
                "total":           len(module_sessions),
            })

        # Flat lists for fallback (template uses these only when modules is empty)
        completed_sessions = [s for s in all_sessions if s.status == LessonSession.SessionStatus.COMPLETED]
        planned_sessions   = [s for s in all_sessions if s.status == LessonSession.SessionStatus.PLANNED]
        pending_sessions   = [s for s in all_sessions if s.status == LessonSession.SessionStatus.PENDING]
        skipped_sessions   = [s for s in all_sessions if s.status == LessonSession.SessionStatus.SKIPPED]

    return render(request, "student/batch/batch.html", {
        "batch":              batch,
        "schedules":          schedules,
        "modules":            modules_data,       # list of dicts — one per module
        "completed_sessions": completed_sessions,  # flat fallback
        "planned_sessions":   planned_sessions,
        "pending_sessions":   pending_sessions,
        "skipped_sessions":   skipped_sessions,
    })








MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@role_required("student")
def upload(request):

    student = request.user.student

    REQUIRED_DOCS = {
        "photo": "Photograph",
        "education": "Educational Certificate",
        "aadhaar": "Aadhaar",
        "resume": "Resume / CV",
    }

    onboarding, _ = OnboardingChecklist.objects.get_or_create(student=student)

    # =====================================
    # Get existing documents
    # =====================================
    existing_docs = {
        doc.document_type: doc
        for doc in StudentDocument.objects.filter(student=student)
    }

    # =====================================
    # If any doc rejected → allow re-upload
    # =====================================
    if any(
        doc.verification_status == StudentDocument.VerificationStatus.REJECTED
        for doc in existing_docs.values()
    ):
        onboarding.documents_uploaded = False
        onboarding.save(update_fields=["documents_uploaded"])

    # =====================================
    # POST: Upload logic
    # =====================================
    if request.method == "POST":

        uploaded_any = False

        for key, label in REQUIRED_DOCS.items():

            file = request.FILES.get(key)
            if not file:
                continue

            if file.size > MAX_FILE_SIZE:
                messages.error(request, f"{label} exceeds 5MB")
                return redirect(request.path)

            last_doc = existing_docs.get(key)

            # =====================================
            # Block overwrite if pending or verified
            # =====================================
            if last_doc and last_doc.verification_status in (
                StudentDocument.VerificationStatus.PENDING,
                StudentDocument.VerificationStatus.VERIFIED,
            ):
                continue

            # =====================================
            # Replace rejected document
            # =====================================
            if last_doc:

                # delete old file
                if last_doc.document_file:
                    last_doc.document_file.delete(save=False)

                last_doc.document_file = file
                last_doc.verification_status = StudentDocument.VerificationStatus.PENDING
                last_doc.rejection_reason = ""
                last_doc.save()

            else:
                # create new document
                StudentDocument.objects.create(
                    student=student,
                    document_type=key,
                    document_file=file,
                    verification_status=StudentDocument.VerificationStatus.PENDING,
                    rejection_reason="",
                )

            uploaded_any = True

        if not uploaded_any:
            messages.error(request, "No new documents uploaded.")
            return redirect(request.path)

        onboarding.documents_uploaded = True
        onboarding.save(update_fields=["documents_uploaded"])

        # =====================================
        # Notify BDM
        # =====================================
        from django.contrib.auth import get_user_model
        User = get_user_model()

        for bdm in User.objects.filter(role="admin"):
            Notification.objects.create(
                recipient=bdm,
                notification_type=Notification.NotificationType.GENERAL,
                title="Student Documents Submitted",
                message=f"{student.full_name} uploaded documents for verification.",
            )

        messages.success(
            request,
            "Documents uploaded successfully. Verification in progress."
        )

        return redirect(request.path)

    # =====================================
    # Prepare documents for template display
    # =====================================
    display_docs = {}

    for key, doc in existing_docs.items():

        # Rejected → always show rejected
        if doc.verification_status == StudentDocument.VerificationStatus.REJECTED:
            if not doc.rejection_reason:
                doc.rejection_reason = "No reason provided"
            display_docs[key] = doc
            continue

        # Checklist not verified → force pending in UI
        if not onboarding.documents_verified:
            doc.verification_status = StudentDocument.VerificationStatus.PENDING
            display_docs[key] = doc
            continue

        display_docs[key] = doc

    # =====================================
    # Check if submit button should be enabled
    # =====================================
    can_submit = True

    for key in REQUIRED_DOCS:
        doc = existing_docs.get(key)

        if not doc or doc.verification_status == StudentDocument.VerificationStatus.REJECTED:
            can_submit = False
            break

    return render(
        request,
        "student/onboarding/uploaddoc.html",
        {
            "docs": display_docs,
            "onboarding": onboarding,
            "REQUIRED_DOCS": REQUIRED_DOCS,
            "can_submit": can_submit,
        },
    )





@role_required("student")
def onboard(request):
    student = request.user.student
    checklist, _ = OnboardingChecklist.objects.get_or_create(student=student)

    agreement, _ = EnrollmentAgreement.objects.get_or_create(
        student=student,
        defaults={
            "agreement_number": f"AGR-{student.id}",
            "agreement_date": timezone.now().date(),
            "course_fee_agreed": 0,
        }
    )

    form = EnrollmentAgreementForm(instance=agreement)

    # GET CHOICES PROPERLY
    payment_plan_choices = form.fields["payment_plan"].choices

    # Step logic
    completed_steps = 0
    if checklist.documents_verified:
        completed_steps += 1

    enrollment_generated = checklist.enrollment_letter_generated
    enrollment_signed = checklist.enrollment_letter_signed
    if enrollment_signed:
        completed_steps += 1

    if getattr(checklist, "id_card_issued", False):
        completed_steps += 1

    progress_percentage = (completed_steps / 3) * 100

    context = {
        "completed_steps": completed_steps,
        "progress_percentage": progress_percentage,
        "all_docs_verified": checklist.documents_verified,
        "enrollment_generated": enrollment_generated,
        "enrollment_signed": enrollment_signed,
        "agreement": agreement,
        "checklist": checklist,
        "form": form,
        "payment_plan_choices": payment_plan_choices,
    }

    return render(request, "student/onboarding/onboarding.html", context)







#when merging delete this view this is for just check logic correct or not

@role_required("student")
def download_enrollment_letter(request):
    checklist = request.user.student.onboarding_checklist

    if not checklist.enrollment_letter_generated:
        messages.info(request, "Enrollment letter not generated yet.")
        return redirect("student:onboarding")

    content = (
        "ENROLLMENT LETTER (TEMP)\n\n"
        f"Student: {request.user.get_full_name()}\n\n"
        "This is a temporary enrollment letter.\n"
        "A PDF version will be added by BDM."
    )

    response = HttpResponse(content, content_type="application/octet-stream")
    response["Content-Disposition"] = 'attachment; filename="enrollment_letter.txt"'
    return response







@role_required("student")
def upload_signed_enrollment_letter(request):

    if request.method != "POST":
        return JsonResponse({"success": False}, status=400)

    student = request.user.student
    checklist = student.onboarding_checklist

    agreement, _ = EnrollmentAgreement.objects.get_or_create(
        student=student
    )

    # ─────────────────────────────
    # SIGNED LETTER UPLOAD ONLY
    # ─────────────────────────────
    signed_file = request.FILES.get("signed_letter")

    if signed_file:
        agreement.agreement_file = signed_file
        agreement.is_signed = True
        agreement.signed_at = timezone.now()
        agreement.signature_ip = request.META.get("REMOTE_ADDR")
        agreement.save()

        checklist.enrollment_letter_signed = True
        checklist.save(update_fields=["enrollment_letter_signed"])



        # ✅ Notify BDM about signed enrollment letter
        from django.contrib.auth import get_user_model
        User = get_user_model()

        for bdm in User.objects.filter(role="admin"):
            Notification.objects.create(
                recipient=bdm,
                notification_type=Notification.NotificationType.GENERAL,
                title="Enrollment Letter Signed",
                message=f"{student.full_name} uploaded a signed enrollment letter.",
                
            )

        return JsonResponse({
            "success": True,
            "type": "file_uploaded"
        })

    return JsonResponse({
        "success": False,
        "message": "No file uploaded"
    }, status=400)









@role_required("student")
def view_id_card(request):
    student = request.user.student

    # Try to get the student's photo document
    try:
        photo = student.documents.get(document_type=StudentDocument.DocumentType.PHOTO)
    except StudentDocument.DoesNotExist:
        photo = None

    try:
        id_card = student.id_card  # may not exist
        context = {
            "id_card": id_card,
            "photo": photo,
            "available": True
        }
    except student.id_card.RelatedObjectDoesNotExist:
        context = {
            "photo": photo,
            "available": False
        }

    return render(request, "student/onboarding/view_id_card.html", context)







@role_required("student")
def download_id_card(request):
    checklist = request.user.student.onboarding_checklist

    if not checklist.id_card_generated:
        messages.info(request, "ID Card has not been generated by BDM yet.")
        return redirect("student:onboarding")

    try:
        # Assuming student model has `id_card` FileField
        id_card_file = request.user.student.id_card
        if not id_card_file:
            messages.info(request, "ID Card file is not available yet.")
            return redirect("student:onboarding")
        
        # Optional: mark as issued when downloaded
        checklist.id_card_issued = True
        checklist.save()

        return FileResponse(id_card_file.open('rb'), as_attachment=True)
    except Exception as e:
        messages.error(request, "ID Card not available: " + str(e))
        return redirect("student:onboarding")










@role_required("student")
def student_tasks(request):
    student = request.user.student

    batch = student.batches.filter(
        is_active=True
    ).select_related("course").first()

    modules = []

    if batch:
        # One query: all tasks for this batch with full chain prefetched
        # Task → lesson_session → lesson_plan → module
        all_tasks = list(
            Task.objects.filter(batch=batch)
            .select_related(
                "lesson_session__lesson_plan__module",
                "lesson_session__lesson_plan",
            )
            .prefetch_related("submissions")
            .order_by(
                "lesson_session__lesson_plan__module__module_number",
                "lesson_session__lesson_plan__session_number",
                "due_date",
            )
        )

        # Attach student_submission to each task so template can use task.student_submission
        for task in all_tasks:
            task.student_submission = task.submissions.filter(
                student=student
            ).first()

        # Get all modules for this batch's course
        raw_modules = Module.objects.filter(
            course=batch.course
        ).order_by("module_number")

        for module in raw_modules:
            # Tasks belonging to this module
            module_tasks = [
                t for t in all_tasks
                if t.lesson_session.lesson_plan.module_id == module.id
            ]

            if not module_tasks:
                continue  # skip modules with no tasks

            # Group module tasks by lesson_session
            sessions_dict = {}
            for task in module_tasks:
                session = task.lesson_session
                if session.id not in sessions_dict:
                    sessions_dict[session.id] = {
                        "session": session,
                        "tasks": [],
                    }
                sessions_dict[session.id]["tasks"].append(task)

            # Build sessions list, add task_count
            sessions_list = []
            for sd in sessions_dict.values():
                sd["task_count"] = len(sd["tasks"])
                sessions_list.append(sd)

            # Sort sessions by session_number
            sessions_list.sort(
                key=lambda s: s["session"].lesson_plan.session_number
            )

            modules.append({
                "module":        module,
                "sessions":      sessions_list,
                "session_count": len(sessions_list),
                "task_count":    len(module_tasks),
            })

    return render(request, "student/task/task_list.html", {
        "batch":   batch,
        "modules": modules,
    })


@role_required("student")
def task_detail(request, task_id):
    student = request.user.student

    # Get active batch
    batch = student.batches.filter(is_active=True).first()

    # Get task only from that batch
    task = get_object_or_404(
        Task,
        id=task_id,
        batch=batch
    )

    # Get student submission (if exists)
    submission = TaskSubmission.objects.filter(
        task=task,
        student=student
    ).first()

    return render(request, "student/task/task_detail.html", {
        "task": task,
        "batch": batch,
        "submission": submission
    })
   


@role_required("student")
def do_task(request, task_id):
    student = request.user.student
    task = get_object_or_404(Task, id=task_id)

    submission, created = TaskSubmission.objects.get_or_create(
        task=task,
        student=student
    )

    # If first time opening
    if created:
        submission.status = TaskSubmission.SubmissionStatus.IN_PROGRESS
        submission.started_at = timezone.now()
        submission.save()

    if request.method == "POST":
        submission.submission_text = request.POST.get("submission_text", "").strip()
        submission.submission_link = request.POST.get("submission_link", "").strip()

        if request.FILES.get("submission_file"):
            submission.submission_file = request.FILES["submission_file"]

        # Prevent empty submission
        if not submission.submission_text and not submission.submission_link and not submission.submission_file:
            messages.error(request, "Please provide at least one submission method.")
        else:
            submission.submit()

            trainer = task.created_by

            if trainer:
                Notification.objects.create(
                    recipient=trainer.user,
                    notification_type=Notification.NotificationType.GENERAL,
                    title="Task Submitted",
                    message=f"{student.full_name} submitted '{task.title}'.",
                    
                )

            messages.success(request, "Task submitted successfully.")
            return redirect("student:task_detail", task_id=task.id)

    return render(request, "student/task/do_task.html", {
        "task": task,
        "submission": submission
    })


def clean(self):
    cleaned_data = super().clean()
    text = cleaned_data.get("submission_text")
    file = cleaned_data.get("submission_file")
    link = cleaned_data.get("submission_link")

    if not text and not file and not link:
        raise forms.ValidationError(
            "You must provide at least one submission method."
        )

    return cleaned_data








@role_required("student")
def lmsdashboard(request):
    student = request.user.student

    batch = student.batches.filter(
        is_active=True
    ).select_related("course").first()

    sessions_with_materials = []
    total_materials   = 0
    recordings_count  = 0
    notes_count       = 0
    slides_count      = 0
    code_files_count  = 0
    assignments_count = 0
    reference_count   = 0
    other_count       = 0

    VALID_FILTERS = {'recording', 'notes', 'slides', 'code', 'assignment', 'reference', 'other'}
    filter_type = request.GET.get("type", "all")
    if filter_type not in VALID_FILTERS:
        filter_type = "all"

    if batch:
        all_sessions = (
            LessonSession.objects.filter(
                batch=batch,
                status=LessonSession.SessionStatus.COMPLETED
            )
            .select_related("lesson_plan__module")
            .prefetch_related("materials")
            .order_by("lesson_plan__session_number")
        )

        all_materials = SessionMaterial.objects.filter(
            lesson_session__batch=batch
        )

        total_materials   = all_materials.count()
        recordings_count  = all_materials.filter(material_type=SessionMaterial.MaterialType.RECORDING).count()
        notes_count       = all_materials.filter(material_type=SessionMaterial.MaterialType.NOTES).count()
        slides_count      = all_materials.filter(material_type=SessionMaterial.MaterialType.SLIDES).count()
        code_files_count  = all_materials.filter(material_type=SessionMaterial.MaterialType.CODE).count()
        assignments_count = all_materials.filter(material_type=SessionMaterial.MaterialType.ASSIGNMENT).count()
        reference_count   = all_materials.filter(material_type=SessionMaterial.MaterialType.REFERENCE).count()
        other_count       = all_materials.filter(material_type=SessionMaterial.MaterialType.OTHER).count()

        for session in all_sessions:
            mats = session.materials.all()
            if filter_type != "all":
                mats = mats.filter(material_type=filter_type)
                mats = list(mats)
    
            # Attach thumbnail to each recording
            for mat in mats:
                if mat.material_type == SessionMaterial.MaterialType.RECORDING:
                    mat.thumbnail_url = extract_video_thumbnail(mat.external_link)
                else:
                    mat.thumbnail_url = None

            if mats:
                sessions_with_materials.append({
                    "session": session,
                    "materials": mats,
                    "material_count": len(mats),
                })

    return render(request, "student/LMS/lms_dashboard.html", {
        "batch":                   batch,
        "sessions_with_materials": sessions_with_materials,
        "total_materials":         total_materials,
        "recordings_count":        recordings_count,
        "notes_count":             notes_count,
        "slides_count":            slides_count,
        "code_files_count":        code_files_count,
        "assignments_count":       assignments_count,
        "reference_count":         reference_count,
        "other_count":             other_count,
        "active_filter":           filter_type,
    })



@role_required("student")
def lms_view_material(request, pk):
    material = get_object_or_404(SessionMaterial, pk=pk)
    material.increment_views()
    if material.external_link:
        return redirect(material.external_link)
    if material.file:
        return redirect(material.file.url)
    return redirect('student:lms_dashboard')


@role_required("student")
def lms_download_material(request, pk):
    material = get_object_or_404(SessionMaterial, pk=pk)
    material.increment_downloads()
    if material.file:
        return redirect(material.file.url)
    if material.external_link:
        return redirect(material.external_link)
    return redirect('student:lms_dashboard')



def extract_video_thumbnail(url):
    """Extract thumbnail URL from YouTube links."""
    if not url:
        return None
    yt = re.search(r'(?:youtube\.com/(?:watch\?v=|embed/)|youtu\.be/)([\w-]{11})', url)
    if yt:
        return f"https://img.youtube.com/vi/{yt.group(1)}/mqdefault.jpg"
    return None




@role_required("student")
def exam(request):
    student = request.user.student
    batch = student.batches.filter(is_active=True).select_related("course").first()

    exam_data = []

    if batch:

        # ── Fee calculation (same logic as payment_portal) ──
        admission = Admission.objects.filter(
            student=student,
            status=Admission.AdmissionStatus.ACTIVE
        ).first()

        total_fee = admission.total_fee if admission else (batch.course.course_fee or Decimal("0.00"))

        admission_fee_paid_amount = Decimal("0.00")
        if admission and admission.admission_fee_paid and admission.admission_fee_amount:
            admission_fee_paid_amount = admission.admission_fee_amount

        other_paid_amount = (
            FeePayment.objects.filter(
                student=student,
                payment_status=FeePayment.PaymentStatus.COMPLETED
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        paid_amount = admission_fee_paid_amount + other_paid_amount
        pending_amount = max(total_fee - paid_amount, Decimal("0.00"))
        fees_ok = pending_amount == Decimal("0.00")

        # ── Task completion ──
        total_tasks = Task.objects.filter(batch=batch, is_mandatory=True).count()

        if total_tasks > 0:
            completed_tasks = TaskSubmission.objects.filter(
                student=student,
                task__batch=batch,
                task__is_mandatory=True,
                is_submitted=True
            ).count()
            task_completion_pct = (completed_tasks / total_tasks) * 100
        else:
            completed_tasks = 0
            task_completion_pct = 100

        task_ok = task_completion_pct >= 80

        # ── Exams ──
        exams = Exam.objects.filter(
            batch=batch,
        ).prefetch_related("syllabus_modules").order_by("-scheduled_date")

        for ex in exams:

            attendance_pct = Attendance.calculate_attendance_percentage(student, batch)
            att_ok = attendance_pct >= ex.minimum_attendance_required

            is_eligible = att_ok and fees_ok and task_ok

            criteria = [
                {
                    "label": "Attendance",
                    "detail": f"{attendance_pct:.0f}% (Required: {ex.minimum_attendance_required}%)",
                    "ok": att_ok,
                    "value": f"{attendance_pct:.0f}%",
                    "bar": int(attendance_pct),
                },
                {
                    "label": "Course Fees",
                    "detail": "All payments completed" if fees_ok else f"₹{pending_amount} still pending",
                    "ok": fees_ok,
                    "value": "Fully Paid" if fees_ok else f"₹{pending_amount} due",
                    "bar": None,
                },
                {
                    "label": "Task Completion",
                    "detail": f"{completed_tasks}/{total_tasks} mandatory tasks submitted (Required: 80%)"
                              if total_tasks > 0 else "No mandatory tasks assigned",
                    "ok": task_ok,
                    "value": f"{task_completion_pct:.0f}%",
                    "bar": int(task_completion_pct),
                },
            ]

            try:
                result = ExamResult.objects.get(exam=ex, student=student)
            except ExamResult.DoesNotExist:
                result = None

            exam_data.append({
                "exam": ex,
                "result": result,
                "is_eligible": is_eligible,
                "criteria": criteria,
                "failed_count": sum(1 for c in criteria if not c["ok"]),
            })

    return render(request, "student/exam/exam.html", {
        "batch": batch,
        "exam_data": exam_data,
    })


@role_required("student")
def attend_exam(request, exam_id):
    student = request.user.student
    exam    = get_object_or_404(Exam, id=exam_id)
    batch   = student.batches.filter(is_active=True, id=exam.batch.id).first()

    if not batch:
        return redirect('student:exam')

    attendance_pct = Attendance.calculate_attendance_percentage(student, batch)
    att_ok = attendance_pct >= exam.minimum_attendance_required

    # ── Fee check (same logic as payment_portal) ──
    admission = Admission.objects.filter(
        student=student,
        status=Admission.AdmissionStatus.ACTIVE
    ).first()

    total_fee = admission.total_fee if admission else (batch.course.course_fee or Decimal("0.00"))

    admission_fee_paid_amount = Decimal("0.00")
    if admission and admission.admission_fee_paid and admission.admission_fee_amount:
        admission_fee_paid_amount = admission.admission_fee_amount

    other_paid_amount = (
        FeePayment.objects.filter(
            student=student,
            payment_status=FeePayment.PaymentStatus.COMPLETED
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    paid_amount = admission_fee_paid_amount + other_paid_amount
    pending_amount = max(total_fee - paid_amount, Decimal("0.00"))
    fees_ok = pending_amount == Decimal("0.00")

    # ── Task check ──
    total_tasks = Task.objects.filter(batch=batch, is_mandatory=True).count()
    completed_tasks = TaskSubmission.objects.filter(
        student=student,
        task__batch=batch,
        task__is_mandatory=True,
        is_submitted=True
    ).count()
    task_pct = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 100
    task_ok  = task_pct >= 80

    if not (att_ok and fees_ok and task_ok):
        return redirect('student:exam')

    try:
        submission = ExamSubmission.objects.get(exam=exam, student=student)
    except ExamSubmission.DoesNotExist:
        submission = None

    from datetime import datetime, timedelta
    import zoneinfo
    IST = zoneinfo.ZoneInfo("Asia/Kolkata")
    exam_end_iso = None
    if exam.exam_time:
        exam_start   = datetime.combine(exam.scheduled_date, exam.exam_time).replace(tzinfo=IST)
        exam_end     = exam_start + timedelta(minutes=exam.duration_minutes)
        exam_end_iso = exam_end.isoformat()

    return render(request, 'student/exam/attend_exam.html', {
        'exam':         exam,
        'batch':        batch,
        'submission':   submission,
        'exam_started': exam.is_published,
        'exam_end_iso': exam_end_iso,
    })


@role_required("student")
def submit_exam(request, exam_id):
    if request.method != "POST":
        return redirect('student:exam')

    student     = request.user.student
    exam        = get_object_or_404(Exam, id=exam_id)
    answer_file = request.FILES.get('answer_file')

    if not answer_file:
        return redirect('student:attend_exam', exam_id=exam_id)

    from datetime import datetime, timedelta
    import zoneinfo
    IST = zoneinfo.ZoneInfo("Asia/Kolkata")
    now     = timezone.now()
    is_late = False
    if exam.exam_time:
        exam_end  = datetime.combine(exam.scheduled_date, exam.exam_time).replace(tzinfo=IST)
        exam_end += timedelta(minutes=exam.duration_minutes)
        is_late   = now > exam_end

    status = ExamSubmission.SubmissionStatus.LATE if is_late else ExamSubmission.SubmissionStatus.SUBMITTED

    submission, created = ExamSubmission.objects.get_or_create(
        exam=exam,
        student=student,
        defaults={
            'user':        request.user,
            'answer_file': answer_file,
            'status':      status,
        }
    )

    if not created:
        pass

    # ✅ Notify trainer about exam submission
    if created:
        trainer = exam.created_by  # update field name if different

        if trainer:
            Notification.objects.create(
                recipient=trainer.user,
                notification_type=Notification.NotificationType.GENERAL,
                title="Exam Submitted",
                message=f"{student.full_name} submitted '{exam.title}' {'(Late)' if is_late else ''}.",
            )

    return redirect('student:attend_exam', exam_id=exam_id)




@login_required
def get_notifications(request):
    notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).order_by('-created_at')[:20]

    data = [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "type": n.notification_type,
            "created_at": n.created_at.strftime("%b %d, %I:%M %p"),
        }
        for n in notifications
    ]
    return JsonResponse({"notifications": data, "count": len(data)})


@login_required
def mark_notification_read(request, notif_id):
    if request.method == "POST":
        try:
            notif = Notification.objects.get(id=notif_id, recipient=request.user)
            notif.mark_as_read()
            return JsonResponse({"success": True})
        except Notification.DoesNotExist:
            return JsonResponse({"success": False}, status=404)
    return JsonResponse({"success": False}, status=405)