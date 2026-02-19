from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum
from apps.bdm.models import Student,Trainer,Course,Batch,StudentAdminProfile,OnboardingChecklist
from django.contrib.auth import update_session_auth_hash
import uuid, os
from . import views
from django.contrib.auth.decorators import login_required
import uuid
from apps.bdm.models import PaymentDocument
from apps.trainer.models import Attendance,LessonSession,Task,TaskSubmission
from django.http import HttpResponse, JsonResponse, FileResponse
from django.views.decorators.http import require_POST
from .forms import EnrollmentAgreementForm
from apps.accounts.decorators import role_required
from apps.trainer.models import Module, LessonPlan
from .models import FeePayment, StudentDocument, EnrollmentAgreement, StudentIDCard, StudentFeedback
from apps.student.forms import LeaveApplicationForm
from apps.student.models import LeaveApplication

#one time payment
@login_required
def payment(request):

    student = request.user.student

    # ✅ Payment Plan Check
    if student.enrollment_agreement.payment_plan.lower() != "full":
        messages.error(request, "Full payment not allowed")
        return redirect("student:payment_gateway")

    batch = student.batches.first()

    if not batch:
        messages.error(request, "No batch assigned.")
        return redirect("student:dashboard")

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
        return redirect("student:dashboard")

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

@login_required
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
        return redirect("student:dashboard")

    # ================================
    # ✅ FEE CALCULATION (FIXED ✅)
    # ================================
    course_fee = batch.course.course_fee

    # ✅ Installment Plan → NO admission fee
    admission_fee = Decimal("0.00")

    # ✅ Total Fee = ONLY Course Fee
    total_fee = course_fee

    # ================================
    # ✅ INSTALLMENT LOGIC (4 CASES)
    # ================================
    installment_amount = (course_fee / Decimal("4")).quantize(Decimal("0.01"))

    installments = FeePayment.objects.filter(
        student=student,
        payment_type=FeePayment.PaymentType.INSTALLMENT
    ).order_by("installment_number")

    # ✅ Auto-create installments if not exist
    if not installments.exists():

        for i in range(1, 5):

            FeePayment.objects.create(
                student=student,
                payment_type=FeePayment.PaymentType.INSTALLMENT,
                installment_number=i,
                amount=installment_amount,
                payment_status=FeePayment.PaymentStatus.PENDING
            )

        installments = FeePayment.objects.filter(
            student=student,
            payment_type=FeePayment.PaymentType.INSTALLMENT
        ).order_by("installment_number")

    # ================================
    # ✅ PAID AMOUNT
    # ================================
    paid_amount = (
        FeePayment.objects.filter(
            student=student,
            payment_status=FeePayment.PaymentStatus.COMPLETED
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    # ✅ NEVER NEGATIVE
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
    """
    Scan & Pay Installment – receipt upload page
    """

    # ---------------- GET INSTALLMENT ----------------
    installment = get_object_or_404(
        FeePayment,
        id=installment_id,
        student=request.user.student,
        payment_type=FeePayment.PaymentType.INSTALLMENT
    )

    # ---------------- CHECK RECEIPT EXISTS ----------------
    receipt_exists = PaymentDocument.objects.filter(
        fee_payment=installment,
        document_type=PaymentDocument.DocumentType.RECEIPT
    ).exists()

    # ---------------- BLOCK ALREADY PAID ----------------
    if installment.payment_status == FeePayment.PaymentStatus.COMPLETED:
        messages.info(request, "This installment is already paid")
        return redirect(
            "student:installments",
            student_id=installment.student.id
        )

    # ---------------- HANDLE POST ----------------
    if request.method == "POST":
        receipt = request.FILES.get("receipt")

        if not receipt:
            messages.error(request, "Please upload payment receipt")
            return redirect(request.path)

        # Update installment
        installment.payment_status = FeePayment.PaymentStatus.PENDING
        installment.payment_date = timezone.now()
        installment.transaction_id = f"INS-{uuid.uuid4().hex[:10]}"
        installment.receipt_number = f"RCPT-{uuid.uuid4().hex[:6]}"
        installment.save()

        # Save receipt in BDM
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
                f"Status: Pending Verification"
            ),
            uploaded_by=request.user
        )

        messages.success(
            request,
            "Receipt uploaded successfully. Waiting for verification ⏳"
        )

        return redirect(
            "student:installments",
            student_id=installment.student.id
        )

    # ---------------- RENDER PAGE ----------------
    return render(
        request,
        "student/payment/install_qr.html",
        {
            "installment": installment,
            "receipt_exists": receipt_exists,
        }
    )


@login_required
def onetime_view(request):

    student = get_object_or_404(Student, user=request.user)

    batch = student.batches.first()

    if not batch:
        messages.error(request, "No batch assigned")
        return redirect("student:dashboard")

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




















@role_required("student")
def dashboard(request):
    student = request.user.student
    admin_profile = getattr(student, "admin_profile", None)
    checklist, _ = OnboardingChecklist.objects.get_or_create(student=student)

    # Get latest photo document
    profile_photo = student.documents.filter(
        document_type=StudentDocument.DocumentType.PHOTO
    ).order_by('-id').first()

    # Only show if VERIFIED
    if profile_photo and profile_photo.verification_status != StudentDocument.VerificationStatus.VERIFIED:
        profile_photo = None

    # Step completion logic (same as onboard)
    completed_steps = 0
    if checklist.documents_verified:
        completed_steps += 1

    enrollment_generated = checklist.enrollment_letter_generated
    enrollment_signed = checklist.enrollment_letter_signed
    if enrollment_signed:
        completed_steps += 1

    if getattr(checklist, "id_card_issued", False):
        completed_steps += 1

    # Pass context to template
    context = {
        "student": student,
        "admin_profile": admin_profile,
        "profile_photo": profile_photo,
        "all_docs_verified": checklist.documents_verified,
        "user": request.user,
        "checklist": checklist,
        "completed_steps": completed_steps,
        "enrollment_generated": enrollment_generated,
        "enrollment_signed": enrollment_signed,
    }

    return render(request, "student/dashboard/dashboard.html", context)






   

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






   