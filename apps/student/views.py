#rinta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.utils.timezone import now
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse, FileResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from decimal import Decimal
from dateutil.relativedelta import relativedelta
import uuid
import os
import calendar
from apps.bdm.models import Student, Trainer, Course, Batch,StudentAdminProfile, OnboardingChecklist,StudentIssue, PaymentDocument
from apps.accounts.decorators import role_required
from apps.trainer.models import Module, LessonPlan, TaskSubmission, Task, LessonSession, Attendance, SessionMaterial
from apps.student.models import LeaveApplication
from .models import FeePayment, StudentDocument,EnrollmentAgreement, StudentIDCard,StudentFeedback
from .forms import EnrollmentAgreementForm,TaskSubmissionForm
from apps.student.forms import LeaveApplicationForm,StudentIssueForm


#rinta

from django.db.models import Count, Q
from collections import defaultdict

#one time payment
@login_required
def payment(request):

    student = request.user.student
     # ✅ ADDED AGREEMENT SAFETY 🔥🔥🔥
    try:
        agreement = student.enrollment_agreement
    except EnrollmentAgreement.DoesNotExist:
        messages.error(request, "Enrollment agreement not generated")
        return redirect("student:stud_dashboard")

    # ✅ Payment Plan Check
    if student.enrollment_agreement.payment_plan.lower() != "full":
        messages.error(request, "Full payment not allowed")
        return redirect("student:payment_gateway")

    batch = student.batches.first()

    if not batch:
        messages.error(request, "No batch assigned.")
        return redirect("student:stud_dashboard")

    # =====================================
    # ✅ FEES
    # =====================================
    course_fee = batch.course.course_fee

    # ✅ FIXED 🔥🔥🔥 (THIS WAS MISSING)
    admission_fee = course_fee * Decimal("0.10")

    total_fee = course_fee   # Full payment → no addition

    # =====================================
    # ✅ PAYMENTS
    # =====================================
    payments = FeePayment.objects.filter(student=student)

    paid_amount = payments.filter(
        payment_status=FeePayment.PaymentStatus.COMPLETED
    ).aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00")

    pending_amount = max(total_fee - paid_amount, Decimal("0.00"))

    existing_payment = payments.filter(
        payment_type=FeePayment.PaymentType.FULL_PAYMENT
    ).first()

    # =====================================
    # ✅ PAYMENT SUBMISSION
    # =====================================
    if request.method == "POST":

        if existing_payment:
            messages.warning(request, "Payment already submitted")
            return redirect("student:payment")

        receipt = request.FILES.get("receipt")

        if not receipt:
            messages.error(request, "Please upload receipt")
            return redirect("student:payment")

        receipt_no = f"RCPT-{uuid.uuid4().hex[:8].upper()}"
        transaction_id = f"FULL-{uuid.uuid4().hex[:12].upper()}"

        payment = FeePayment.objects.create(
            student=student,
            payment_type=FeePayment.PaymentType.FULL_PAYMENT,
            amount=pending_amount,
            payment_method=FeePayment.PaymentMethod.UPI,
            payment_status=FeePayment.PaymentStatus.PENDING,
            payment_date=timezone.now(),
            transaction_id=transaction_id,
            receipt_number=receipt_no
        )

        # =====================================
        # ✅ SAVE DOCUMENT 🔥
        # =====================================
        PaymentDocument.objects.create(
            fee_payment=payment,
            document_type=PaymentDocument.DocumentType.RECEIPT,
            document_file=receipt,
            uploaded_by=request.user,

            description=(
                f"Full Fee Payment\n"
                f"Student: {student.full_name}\n"
                f"Batch: {batch.name}\n"
                f"Course Fee: ₹{course_fee}\n"
                f"Admission Fee (10%): ₹{admission_fee}\n"
                f"Paid Amount: ₹{paid_amount}\n"
                f"Pending Paid: ₹{pending_amount}\n"
                f"Receipt No: {receipt_no}\n"
                f"Transaction ID: {transaction_id}"
            )
        )

        messages.success(request, "✅ Receipt uploaded successfully")
        return redirect("student:payment")

    # =====================================
    # ✅ RENDER
    # =====================================
    return render(request, "student/payment/payment.html", {
        "student": student,
        "course_fee": course_fee,
        "admission_fee": admission_fee,   # ✅ FIXED
        "total_fee": total_fee,
        "paid_amount": paid_amount,
        "pending_amount": pending_amount,
        "existing_payment": existing_payment,
    })



#admission fee
@login_required
def admission(request):

    student = request.user.student
    batch = student.batches.first()

    if not batch:
        messages.error(request, "No batch assigned.")
        return redirect("student:stud_dashboard")

    course = batch.course

    course_fee = course.course_fee
    admission_amount = course_fee * Decimal("0.10")

    admission_fee = FeePayment.objects.filter(
        student=student,
        payment_type=FeePayment.PaymentType.ADMISSION
    ).first()

    if request.method == "POST":

        if admission_fee:
            messages.warning(request, "Admission fee already paid.")
            return redirect("student:admission")

        receipt_no = f"RCPT-{uuid.uuid4().hex[:8].upper()}"
        transaction_id = f"ADM-{uuid.uuid4().hex[:12].upper()}"

        # ✅ CREATE PAYMENT
        admission_fee = FeePayment.objects.create(
            student=student,
            payment_type=FeePayment.PaymentType.ADMISSION,
            amount=admission_amount,
            payment_method=FeePayment.PaymentMethod.UPI,
            payment_status=FeePayment.PaymentStatus.COMPLETED,
            payment_date=timezone.now(),
            transaction_id=transaction_id,
            receipt_number=receipt_no
        )

        receipt_file = request.FILES.get("receipt")

        # ✅ SAVE FULL DETAILS TO BDM DOCUMENT 🔥🔥🔥
        PaymentDocument.objects.create(
            fee_payment=admission_fee,
            document_type=PaymentDocument.DocumentType.RECEIPT,
            document_file=receipt_file if receipt_file else None,
            uploaded_by=request.user,

            description=(
                f"Admission Fee Payment\n"
                f"Student: {student.full_name}\n"
                f"Batch: {batch.name}\n"
                f"Course: {course.name}\n"
                f"Amount: ₹{admission_amount}\n"
                f"Receipt No: {receipt_no}\n"
                f"Transaction ID: {transaction_id}"
            )
        )

        messages.success(request, "✅ Admission Fee Paid Successfully")
        return redirect("student:admission")

    return render(request, "student/payment/admission.html", {
        "student": student,
        "batch": batch,
        "course": course,
        "course_fee": course_fee,
        "admission_amount": admission_amount,
        "admission_fee": admission_fee,
        "active_tab": "admission",
    })
@login_required
def pdc(request):

    student = request.user.student

    if student.enrollment_agreement.payment_plan.lower() != "pdc":
        messages.error(request, "PDC not allowed")
        return redirect("student:payment_gateway")

    batch = student.batches.first()

    if not batch:
        messages.error(request, "No batch assigned")
        return redirect("student:dashboard")

    course_fee = batch.course.course_fee
    admission_fee = Decimal("0.00")
    total_fee = course_fee + admission_fee

    paid_amount = FeePayment.objects.filter(
        student=student,
        payment_status=FeePayment.PaymentStatus.COMPLETED
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    pending_amount = total_fee - paid_amount

    pdc_payments = FeePayment.objects.filter(
        student=student,
        payment_method=FeePayment.PaymentMethod.CHEQUE
    )

    return render(request, "student/payment/pdc.html", {

        "student": student,

        # ✅ ADDED (Explicit student info)
        "student_name": student.user.get_full_name(),
        "student_email": student.user.email,
        "student_id": student.id,

        "total_fee": total_fee,
        "paid_amount": paid_amount,
        "pending_amount": pending_amount,
        "pdc_payments": pdc_payments,
    })


#EMI

@login_required
def emi(request):

    student = request.user.student

    if student.enrollment_agreement.payment_plan.lower() != "emi":
        messages.error(request, "EMI not allowed")
        return redirect("student:payment_gateway")

    batch = student.batches.first()

    if not batch:
        messages.error(request, "No batch assigned.")
        return redirect("student:dashboard")

    course_fee = batch.course.course_fee
    admission_fee = course_fee * Decimal("0.10")
    total_fee = course_fee + admission_fee

    paid_amount = FeePayment.objects.filter(
        student=student,
        payment_status=FeePayment.PaymentStatus.COMPLETED
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    pending_amount = total_fee - paid_amount

    return render(request, "student/payment/emi.html", {
        "student": student,
        "course_fee": course_fee,
        "admission_fee": admission_fee,
        "total_fee": total_fee,
        "paid_amount": paid_amount,
        "pending_amount": pending_amount,
    })




#Installments

def installments(request, student_id):

    student = get_object_or_404(Student, id=student_id)

    # ✅ SECURITY CHECK
    if request.user.student != student:
        messages.error(request, "Unauthorized access")
        return redirect("student:payment_gateway")

    # ✅ Agreement Check
    if not hasattr(student, "enrollment_agreement"):
        messages.error(request, "Enrollment agreement not found")
        return redirect("student:payment_gateway")

    if student.enrollment_agreement.payment_plan.lower() != "installment":
        messages.error(request, "Installments not allowed")
        return redirect("student:payment_gateway")

    batch = student.batches.first()

    if not batch:
        messages.error(request, "No batch assigned")
        return redirect("student:stud_dashboard")

    # ================================
    # ✅ FEE CALCULATION ⭐⭐⭐⭐⭐
    # ================================
    course_fee = batch.course.course_fee

    admission_fee = (course_fee * Decimal("0.10")).quantize(Decimal("0.01"))

    remaining_fee = course_fee - admission_fee

    total_fee = course_fee

    # ================================
    # ✅ INSTALLMENT LOGIC ⭐⭐⭐⭐⭐
    # ================================
    installment_amount = (remaining_fee / Decimal("4")).quantize(Decimal("0.01"))

    installments_qs = FeePayment.objects.filter(
        student=student,
        payment_type=FeePayment.PaymentType.INSTALLMENT
    ).order_by("installment_number")

    today = now().date()

    if today.day > 21:
        start_date = today + relativedelta(months=1)
    else:
        start_date = today

    # ✅ ENSURE ALL 4 INSTALLMENTS EXIST ⭐⭐⭐⭐⭐
    existing_numbers = set(
        installments_qs.values_list("installment_number", flat=True)
    )

    for i in range(1, 5):

        due_date = start_date + relativedelta(months=i-1, day=21)

        if i not in existing_numbers:

            FeePayment.objects.create(
                student=student,
                payment_type=FeePayment.PaymentType.INSTALLMENT,
                installment_number=i,
                amount=installment_amount,
                payment_status=FeePayment.PaymentStatus.PENDING,
                payment_date=now(),
                due_date=due_date,
                transaction_id=str(uuid.uuid4())
            )

    # ✅ REFRESH QUERYSET ⭐⭐⭐⭐⭐
    installments = FeePayment.objects.filter(
        student=student,
        payment_type=FeePayment.PaymentType.INSTALLMENT
    ).order_by("installment_number")

    # ================================
    # ✅ DISPLAY STATUS LOGIC ⭐⭐⭐⭐⭐🔥
    # ================================
    for inst in installments:

        if inst.payment_status == FeePayment.PaymentStatus.COMPLETED:
            inst.display_status = "Paid"

        elif today < inst.due_date:
            inst.display_status = "Upcoming"

        else:
            inst.display_status = "Pending"

    # ================================
    # ✅ PAID AMOUNT ⭐⭐⭐⭐⭐
    # ================================
    paid_amount = (
        FeePayment.objects.filter(
            student=student,
            payment_status=FeePayment.PaymentStatus.COMPLETED
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    pending_amount = max(total_fee - paid_amount, Decimal("0.00"))

    return render(request, "student/payment/installments.html", {
        "student": student,
        "course_fee": course_fee,
        "admission_fee": admission_fee,
        "total_fee": total_fee,
        "paid_amount": paid_amount,
        "pending_amount": pending_amount,
        "installments": installments,
    })





#scan installemts using QR code
@login_required
def install_qr(request, installment_id):

    installment = get_object_or_404(
        FeePayment,
        id=installment_id,
        student=request.user.student,
        payment_type=FeePayment.PaymentType.INSTALLMENT
    )

    receipt_exists = PaymentDocument.objects.filter(
        fee_payment=installment,
        document_type=PaymentDocument.DocumentType.RECEIPT
    ).exists()

    if installment.payment_status == FeePayment.PaymentStatus.COMPLETED:
        messages.info(request, "This installment is already paid")
        return redirect("student:installments", student_id=installment.student.id)

    # ✅ BLOCK UPCOMING INSTALLMENTS ⭐⭐⭐⭐⭐
    if timezone.now().date() < installment.due_date:
        messages.error(request, "Installment not due yet")
        return redirect("student:installments", student_id=installment.student.id)

    if request.method == "POST":
        receipt = request.FILES.get("receipt")

        if not receipt:
            messages.error(request, "Please upload payment receipt")
            return redirect(request.path)

        # ✅ UPDATE INSTALLMENT ⭐⭐⭐⭐⭐🔥
        installment.payment_status = FeePayment.PaymentStatus.PENDING
        installment.mode_of_payment = FeePayment.PaymentMode.UPI   # ⭐⭐⭐⭐⭐ FIX
        installment.payment_date = timezone.now()
        installment.transaction_id = f"INS-{uuid.uuid4().hex[:10]}"
        installment.receipt_number = f"RCPT-{uuid.uuid4().hex[:6]}"
        installment.save()

        PaymentDocument.objects.create(
            fee_payment=installment,
            document_type=PaymentDocument.DocumentType.RECEIPT,
            document_file=receipt,
            description=(
                f"Installment Payment Receipt\n"
                f"Student: {installment.student.user.get_full_name()}\n"
                f"Student ID: {installment.student.id}\n"
                f"Installment No: {installment.installment_number}\n"
                f"Amount: ₹{installment.amount}\n"
                f"Transaction ID: {installment.transaction_id}\n"
                f"Mode: UPI\n"
                f"Status: Pending Verification"
            ),
            uploaded_by=request.user
        )

        messages.success(
            request,
            "Receipt uploaded successfully. Waiting for verification ⏳"
        )

        return redirect("student:installments", student_id=installment.student.id)

    return render(request, "student/payment/install_qr.html", {
        "installment": installment,
        "receipt_exists": receipt_exists,
    })

@login_required
def onetime_view(request):

    student = get_object_or_404(Student, user=request.user)

    batch = student.batches.first()

    if not batch:
        messages.error(request, "No batch assigned")
        return redirect("student:stud_dashboard")

    course_fee = batch.course.course_fee
    admission_fee = course_fee * Decimal("0.10")

    # ✅ FIXED 🔥
    total_fee = course_fee

    payment = FeePayment.objects.filter(
        student=student,
        payment_type=FeePayment.PaymentType.FULL_PAYMENT
    ).first()

    context = {
        "student": student,
        "admission_fee": admission_fee,
        "course_fee": course_fee,
        "total_fee": total_fee,
        "payment_status": payment.payment_status if payment else "not paid",
        "payment_date": payment.payment_date if payment else None,
    }

    return render(
        request,
        "student/payment/one_time_view.html",
        context)



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





#one time installment-using QR code

def QR_pay(request):
    """
    Scan & Pay (PDC)
    NO pdc_id required
    """

    # First pending PDC installment
    pdc = FeePayment.objects.filter(
        payment_method=FeePayment.PaymentMethod.CHEQUE,
        payment_status=FeePayment.PaymentStatus.PENDING
    ).order_by('cheque_date').first()

    if not pdc:
        messages.info(request, "No pending PDC payments")
        return redirect('student:pdc')

    # Submit payment
    if request.method == "POST":
        pdc.payment_status = FeePayment.PaymentStatus.COMPLETED
        pdc.payment_date = timezone.now()
        pdc.transaction_id = f"PDC-{pdc.id}"
        pdc.save()

        messages.success(request, "Payment submitted successfully")
        return redirect('student:pdc')

    context = {
        'pdc': pdc,
        'amount': pdc.amount,
        'due_date': pdc.cheque_date,
    }

    return render(request, 'student/payment/QR_pay.html', context)





def stud_feedback(request):
    if request.method == "POST":

        # 🔴 BASIC VALIDATION
        if not request.POST.get("feedback_type"):
            messages.error(request, "❌ Please select feedback type")
            return redirect("student:stud_feedback")

        if not request.POST.get("overall_rating"):
            messages.error(request, "❌ Overall rating is required")
            return redirect("student:stud_feedback")

        # ✅ SAVE FEEDBACK
        StudentFeedback.objects.create(
            student_id=request.POST.get("student") or None,
            feedback_type=request.POST.get("feedback_type"),
            trainer_id=request.POST.get("trainer") or None,
            course_id=request.POST.get("course") or None,
            batch_id=request.POST.get("batch") or None,
            content_quality=request.POST.get("content_quality") or None,
            teaching_methodology=request.POST.get("teaching_methodology") or None,
            responsiveness=request.POST.get("responsiveness") or None,
            overall_rating=request.POST.get("overall_rating"),
            comments=request.POST.get("comments"),
            suggestions=request.POST.get("suggestions"),
            is_anonymous=True if request.POST.get("is_anonymous") else False,
        )

        # ✅ SUCCESS MESSAGE
        messages.success(
            request,
            "✅ Thank you! Your feedback has been submitted successfully."
        )

        return redirect("student:stud_feedback")

    # GET REQUEST
    context = {
        "students": Student.objects.all(),
        "trainers": Trainer.objects.all(),
        "courses": Course.objects.all(),
        "batches": Batch.objects.all(),
    }

    return render(request, "student/dashboard/stud_feedback.html", context)


def lms_login(request):
    return render(request,'student/LMS/lms_login.html')


@login_required
def payment_gateway(request):

    student = request.user.student

    try:
        agreement = student.enrollment_agreement
    except EnrollmentAgreement.DoesNotExist:
        messages.error(request, "Enrollment agreement not found")
        return redirect("student:dashboard")

    if not agreement.is_signed:
        messages.warning(request, "Agreement not signed yet")
        return redirect("student:dashboard")

    plan = agreement.payment_plan.lower()

    if plan == "full":
        return redirect("student:payment")

    elif plan == "emi":
        return redirect("student:emi")

    elif plan == "pdc":
        return redirect("student:pdc")

    elif plan == "installment":
        return redirect("student:installments", student_id=student.id)  

    messages.error(request, "Invalid payment plan")
    return redirect("student:dashboard")
@login_required
def student_attendance(request):

    student = request.user.student

    attendance_records = (
        Attendance.objects
        .filter(student=student)
        .select_related(
            "lesson_session",
            "lesson_session__lesson_plan",
            "marked_by",
            "marked_by__user"
        )
        .order_by("-date")
    )

    if not attendance_records.exists():
        return render(request, "student/dashboard/attendance.html", {
            "student": student,
            "attendance_records": [],
            "percentage": 0,
            "present_days": 0,
            "absent_days": 0,
            "excused_days": 0,
            "batch": None,
        })

    batch = attendance_records.first().batch
    attendance_records = attendance_records.filter(batch=batch)

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

    # ✅ SMART Trainer Fetch (From Sessions 🔥)
    trainer = None

    if batch:
        session = (
            LessonSession.objects
            .filter(batch=batch, trainer__isnull=False)
            .select_related("trainer")
            .first()
        )

        if session:
            trainer = session.trainer

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

    # ✅ PAGE 2 → INDIVIDUAL EVALUATION 🔥
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
            .filter(
                id=submission_id,
                student=student
            )
            .first()
        )

        return render(
            request,
            "student/dashboard/individual_evaluation.html",
            {"submission": submission}
        )

    # ✅ PAGE 1 → LIST PAGE 🔥
    submissions = (
        TaskSubmission.objects
        .select_related("task", "task__batch")
        .filter(student=student)
        .order_by("-submitted_at")
    )

    totals = submissions.filter(
        marks_obtained__isnull=False
    ).aggregate(
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























































































































































































#rinta+niranjana

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

    # ✅ LEARNING PROGRESS
    covered_percentage = 0
    pending_percentage = 0

    if batch:
        progress_data = LessonSession.get_batch_progress(batch)
        covered_percentage = progress_data["progress_percentage"]
        pending_percentage = 100 - covered_percentage

    # =====================================================
    # ✅ PAYMENT ENGINE
    # =====================================================

    today = timezone.now().date()

    payment_notification = "No Pending Payments"
    payment_css = "success"
    pending_payment = None

    total_fee = Decimal("0")

    if batch and batch.course:
        total_fee = batch.course.course_fee or Decimal("0")

    paid_amount = FeePayment.objects.filter(
        student=student,
        payment_status=FeePayment.PaymentStatus.COMPLETED
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    balance = total_fee - paid_amount

    overdue_payment = FeePayment.objects.filter(
        student=student,
        payment_status=FeePayment.PaymentStatus.PENDING,
        due_date__lt=today
    ).order_by("due_date").first()

    upcoming_payment = FeePayment.objects.filter(
        student=student,
        payment_status=FeePayment.PaymentStatus.PENDING
    ).order_by("due_date").first()

    if balance > 0:

        if overdue_payment:
            payment_notification = "Payment Overdue"
            payment_css = "danger"
            pending_payment = overdue_payment

        else:
            payment_notification = "Payment Pending"
            payment_css = "warning"
            pending_payment = upcoming_payment

    # ✅ CALENDAR
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(today.year, today.month)

    month_name = calendar.month_name[today.month]
    year = today.year
    today_day = today.day

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
    }

    return render(request, "student/dashboard/dashboard.html", context)







   






#niranjana

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
    # Get latest document per type
    # =====================================
    latest_docs_qs = (
        StudentDocument.objects
        .filter(student=student)
        .order_by("document_type", "-id")
        .distinct("document_type")
    )
    existing_docs = {doc.document_type: doc for doc in latest_docs_qs}

    # =====================================
    # If any doc rejected → allow re-upload
    # =====================================
    if any(doc.verification_status == StudentDocument.VerificationStatus.REJECTED
           for doc in existing_docs.values()):
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

            # Block overwrite if already pending or verified
            if last_doc and last_doc.verification_status in (
                StudentDocument.VerificationStatus.PENDING,
                StudentDocument.VerificationStatus.VERIFIED,
            ):
                continue

            # Create new doc only if rejected or not exists
            StudentDocument.objects.create(
                student=student,
                document_type=key,
                document_file=file,
                verification_status=StudentDocument.VerificationStatus.PENDING,
                rejection_reason="",  # clear old reason
            )
            uploaded_any = True

        if not uploaded_any:
            messages.error(request, "No new documents uploaded.")
            return redirect(request.path)

        onboarding.documents_uploaded = True
        onboarding.save(update_fields=["documents_uploaded"])

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

        # Rejected → always rejected, ensure rejection reason
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

        # Checklist verified → show actual status
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
        }
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







@role_required("student")
def upload_signed_enrollment_letter(request):
    if request.method != "POST":
        return JsonResponse({"success": False}, status=400)

    student = request.user.student
    checklist = student.onboarding_checklist

    agreement, _ = EnrollmentAgreement.objects.get_or_create(
        student=student,
        defaults={"course_fee_agreed": 0}
    )
    # -----------------------------
    # 0️⃣ COURSE FEE SAVE
    # -----------------------------
    # -----------------------------
# 0️⃣ COURSE FEE SAVE
# -----------------------------
    course_fee = request.POST.get("course_fee_agreed")
    if course_fee:
        try:
            agreement.course_fee_agreed = float(course_fee)
            agreement.save(update_fields=["course_fee_agreed"])
            return JsonResponse({"success": True, "type": "course_fee_saved"})
        except ValueError:
            return JsonResponse({"success": False, "message": "Invalid fee value"})


    # -----------------------------
    # 1️⃣ PAYMENT PLAN SAVE
    # -----------------------------
    payment_plan = request.POST.get("payment_plan")

    if payment_plan:
        agreement.payment_plan = payment_plan
        agreement.save(update_fields=["payment_plan"])

        checklist.payment_plan_created = True
        checklist.save(update_fields=["payment_plan_created"])

        return JsonResponse({
            "success": True,
            "type": "payment_saved"
        })

    # -----------------------------
    # 2️⃣ SIGNED LETTER UPLOAD
    # -----------------------------
    signed_file = request.FILES.get("signed_letter")

    if signed_file:
        agreement.agreement_file = signed_file
        agreement.is_signed = True
        agreement.signed_at = timezone.now()
        agreement.signature_ip = request.META.get("REMOTE_ADDR")

        agreement.save()

        checklist.enrollment_letter_signed = True
        checklist.save(update_fields=["enrollment_letter_signed"])

        return JsonResponse({
            "success": True,
            "type": "file_uploaded"
        })

    return JsonResponse({"success": False}, status=400)






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

        # 🔥 Remove extra blank lines from tech_stack
        if course.tech_stack:
            course.tech_stack = "\n".join(
                line.strip()
                for line in course.tech_stack.splitlines()
                if line.strip()
            )

        # 🔥 Remove extra blank lines from syllabus
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
def batch_details(request):
    student = request.user.student

    batch = student.batches.filter(
        is_active=True
    ).select_related(
        "course"
    ).prefetch_related(
        "trainers__user"
    ).first()

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
        "modules":            modules_data,       # list of dicts — one per module
        "completed_sessions": completed_sessions,  # flat fallback
        "planned_sessions":   planned_sessions,
        "pending_sessions":   pending_sessions,
        "skipped_sessions":   skipped_sessions,
    })





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





