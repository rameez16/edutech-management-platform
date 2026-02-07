from django.shortcuts import render, redirect, get_object_or_404
from apps.accounts.decorators import role_required
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum
from django.http import FileResponse
from apps.bdm.models import Student
from .models import FeePayment
from apps.trainer.models import Module, LessonPlan
from apps.bdm.models import StudentAdminProfile, Batch
from apps.bdm.models import OnboardingChecklist
import uuid, os

from .models import StudentDocument


# Create your views here.




@role_required("student")
def dashboard(request):
    student = request.user.student  # Student object
    admin_profile = getattr(student, "admin_profile", None)  # May be None

    context = {
        "student": student,
        "admin_profile": admin_profile
    }
    return render(request, "student/dashboard/dashboard.html", context)


    



def payment(request):
    """
    Student Admission & Fee Management
    ONE-TIME PAYMENT ONLY
    """

    student = Student.objects.first()  # no login

    course_fee = 55000

    # 🔹 Check if ONE-TIME payment already exists
    existing_payment = FeePayment.objects.filter(
        student=student,
        payment_type=FeePayment.PaymentType.FULL_PAYMENT
    ).first()

    # -------------------------
    # 🔹 HANDLE SUBMIT (POST)
    # -------------------------
    if request.method == 'POST':

        if existing_payment:
            messages.warning(
                request,
                "One-time payment already submitted."
            )
            return redirect('student:payment')

        transaction_id = request.POST.get('transaction_id')

        if not transaction_id:
            messages.error(request, "Transaction ID is required")
            return redirect('student:payment')

        FeePayment.objects.create(
            student=student,
            payment_type=FeePayment.PaymentType.FULL_PAYMENT,
            payment_method=FeePayment.PaymentMethod.UPI,
            amount=course_fee,
            payment_status=FeePayment.PaymentStatus.PENDING,
            transaction_id=transaction_id,
            payment_date=timezone.now(),
            remarks="One-time QR payment"
        )

        messages.success(
            request,
            "Payment submitted successfully. Awaiting verification."
        )
        return redirect('student:payment')

    # -------------------------
    # 🔹 DISPLAY DATA (GET)
    # -------------------------

    admission_fee = Decimal('0.00')
    total_fee = admission_fee + course_fee

    paid_amount = Decimal('0.00')
    pending_amount = total_fee
    payment_status = None

    if existing_payment:
        payment_status = existing_payment.payment_status

        if existing_payment.payment_status == FeePayment.PaymentStatus.COMPLETED:
            paid_amount = existing_payment.amount
            pending_amount = Decimal('0.00')

        else:  # PENDING
            paid_amount = Decimal('0.00')
            pending_amount = total_fee

    context = {
        'student': student,
        'admission_fee': admission_fee,
        'course_fee': course_fee,
        'total_fee': total_fee,
        'paid_amount': paid_amount,
        'pending_amount': pending_amount,
        'existing_payment': existing_payment,
        'payment_status': payment_status,
    }

    return render(request, 'student/payment/payment.html', context)





def pdc(request):
    """
    PDC PAGE ONLY
    No separate pdc_view
    No static fee
    Completed / Pay / Upcoming support
    """

    # Temporary access (no login)
    student = Student.objects.first()

    today = timezone.now().date()

    # -------- COURSE FEE (DYNAMIC) --------
    admission_fee = Decimal('0.00')
    course_fee = 55000
    total_fee = admission_fee + course_fee

    # -------- PAID AMOUNT --------
    paid_qs = FeePayment.objects.filter(
        student=student,
        payment_status=FeePayment.PaymentStatus.COMPLETED
    )
    paid_amount = sum(p.amount for p in paid_qs) or Decimal('0.00')

    # -------- PENDING AMOUNT --------
    pending_amount = total_fee - paid_amount

    # -------- PDC CHEQUES --------
    pdc_payments = FeePayment.objects.filter(
        student=student,
        payment_method=FeePayment.PaymentMethod.CHEQUE
    ).order_by('installment_number')

    context = {
        'student': student,
        'admission_fee': admission_fee,
        'course_fee': course_fee,
        'total_fee': total_fee,
        'paid_amount': paid_amount,
        'pending_amount': pending_amount,
        'pdc_payments': pdc_payments,
        'today': today,              # ⭐ IMPORTANT
        'active_mode': 'pdc',
    }

    return render(request, 'student/payment/pdc.html', context)


def emi(request):
    return render(request, 'student/payment/emi.html')

def installments(request):
    """
    INSTALLMENTS PAGE
    - No static fee
    - No installment id
    - Status based view (Paid / Pending / Upcoming)
    """

    # Temporary access (no login)
    student = Student.objects.first()
    today = timezone.now().date()

    # -------- COURSE FEE --------
    admission_fee = Decimal('0.00')
    course_fee = 55000
    total_fee = admission_fee + course_fee

    # -------- PAID AMOUNT --------
    paid_qs = FeePayment.objects.filter(
        student=student,
        payment_status=FeePayment.PaymentStatus.COMPLETED
    )
    paid_amount = sum(p.amount for p in paid_qs) or Decimal('0.00')

    # -------- PENDING AMOUNT --------
    pending_amount = total_fee - paid_amount

    # -------- INSTALLMENTS --------
    installments = FeePayment.objects.filter(
        student=student,
        payment_method=FeePayment.PaymentMethod.EMI   # or INSTALLMENT if you use that
    ).order_by('installment_number')

    context = {
        'student': student,
        'admission_fee': admission_fee,
        'course_fee': course_fee,
        'total_fee': total_fee,
        'paid_amount': paid_amount,
        'pending_amount': pending_amount,
        'installments': installments,
        'today': today,                # 🔑 required for Upcoming/Pay logic
        'active_mode': 'installment',  # tab highlight
    }

    return render(request, 'student/payment/installments.html', context)

def installments_view(request):
    return render(request, 'student/payment/loan_view.html')
def pdc_view(request):
    return render(request, 'student/payment/pdc_view.html')
def onetime_view(request):
    """
    ONE TIME PAYMENT – SUMMARY PAGE
    """

    student = Student.objects.first()

    admission_fee = Decimal('5000.00')
    course_fee = student.selected_course.course_fee
    total_fee = admission_fee + course_fee

    paid_amount = FeePayment.objects.filter(
        student=student,
        payment_status=FeePayment.PaymentStatus.COMPLETED
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    remaining_amount = total_fee - paid_amount

    context = {
        'student': student,
        'admission_fee': admission_fee,
        'course_fee': course_fee,
        'remaining_amount': remaining_amount,
    }

    return render(request, 'student/payment/onetime_view.html', context)
def emi_view(request):
    return render(request, 'student/payment/emi_view.html')
def profile(request):
    return render(request, 'student/profile/profile.html')
def overview(request):
    return render(request, 'student/profile/overview.html')
def password(request):
    return render(request, 'student/profile/password.html')
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
def installments_qr(request):
    """
    Scan & Pay your Installments
    - No installment id
    - Shows all PENDING installments
    """

    # Temporary access (no login)
    student = Student.objects.first()

    # Pending installments only
    installments = FeePayment.objects.filter(
        student=student,
        payment_method=FeePayment.PaymentMethod.EMI,   # or INSTALLMENT if you use that
        payment_status=FeePayment.PaymentStatus.PENDING
    ).order_by('due_date')

    if not installments.exists():
        messages.info(request, "No pending installments")
        return redirect('student:installments')

    # ---------------- SUBMIT PAYMENT ----------------
    if request.method == "POST":
        for ins in installments:
            ins.payment_status = FeePayment.PaymentStatus.COMPLETED
            ins.payment_date = timezone.now()
            ins.transaction_id = f"INST-{uuid.uuid4().hex[:10]}"
            ins.save()

        messages.success(request, "Installment payment submitted successfully")
        return redirect('student:installments')

    context = {
        'student': student,
        'installments': installments,
    }

    return render(request, 'student/payment/installment_qr.html', context)





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

    existing_docs = {
        doc.document_type: doc
        for doc in StudentDocument.objects.filter(student=student)
    }

    # ====================================================
    # 🔥 AUTO-VERIFY DOCUMENTS BASED ON CHECKLIST
    # ====================================================
    if onboarding.documents_verified:  # ← your checklist flag
        for doc in existing_docs.values():
            if doc.verification_status != StudentDocument.VerificationStatus.VERIFIED:
                doc.verification_status = StudentDocument.VerificationStatus.VERIFIED
                doc.save(update_fields=["verification_status"])

    # ====================================================
    # POST: UPLOAD LOGIC
    # ====================================================
    if request.method == "POST":

        if onboarding.documents_uploaded:
            messages.error(request, "Documents already submitted.")
            return redirect(request.path)

        missing = [
            label
            for key, label in REQUIRED_DOCS.items()
            if not request.FILES.get(key)
        ]

        if missing:
            messages.error(request, "Please upload: " + ", ".join(missing))
            return redirect(request.path)

        for key in REQUIRED_DOCS.keys():
            file = request.FILES[key]

            if file.size > MAX_FILE_SIZE:
                messages.error(request, f"{REQUIRED_DOCS[key]} exceeds 5MB")
                return redirect(request.path)

            StudentDocument.objects.update_or_create(
                student=student,
                document_type=key,
                defaults={
                    "document_file": file,
                    "verification_status": StudentDocument.VerificationStatus.PENDING,
                }
            )

        onboarding.documents_uploaded = True
        onboarding.save(update_fields=["documents_uploaded"])

        messages.success(
            request,
            "Documents submitted successfully. Verification in progress."
        )
        return redirect(request.path)

    return render(
        request,
        "student/onboarding/uploaddoc.html",
        {
            "docs": existing_docs,
            "onboarding": onboarding,
            "REQUIRED_DOCS": REQUIRED_DOCS,  # needed for template form
        }
    )

@role_required("student")
def onboard(request):
    student = request.user.student  # get logged-in student's object
    checklist, _ = OnboardingChecklist.objects.get_or_create(student=student)

    # Step 1: Document Upload
    completed_steps = 0
    if checklist.documents_verified:
        completed_steps += 1

    # Step 2: Enrollment Letter
    enrollment_generated = checklist.enrollment_letter_generated
    enrollment_signed = checklist.enrollment_letter_signed
    if enrollment_signed:
        completed_steps += 1  # Only count as completed if signed

    # Step 3: ID Card
    if getattr(checklist, "id_card_downloaded", False):
        completed_steps += 1

    # Calculate progress percentage
    progress_percentage = (completed_steps / 3) * 100

    # Pass context to template
    context = {
        "completed_steps": completed_steps,
        "progress_percentage": progress_percentage,
        "all_docs_verified": checklist.documents_verified,
        "enrollment_generated": enrollment_generated,
        "enrollment_signed": enrollment_signed,
        "checklist": checklist,
    }

    return render(request, "student/onboarding/onboarding.html", context)


@role_required("student")
def download_enrollment_letter(request):
    checklist = request.user.student.onboarding_checklist

    if not checklist.enrollment_letter_generated:
        messages.info(request, "BDM has not generated your enrollment letter yet.")
        return redirect("student:onboarding")

    # Here you would fetch the actual file from EnrollmentAgreement
    try:
        agreement = request.user.student.enrollment_agreement
        if not agreement.agreement_file:
            messages.info(request, "Enrollment letter file is not available yet.")
            return redirect("student:onboarding")
        return FileResponse(agreement.agreement_file.open('rb'), as_attachment=True)
    except:
        messages.info(request, "Enrollment letter not available yet.")
        return redirect("student:onboarding")

@role_required("student")
def upload_signed_enrollment_letter(request):
    checklist = request.user.student.onboarding_checklist

    if not checklist.enrollment_letter_generated:
        messages.error(request, "Cannot upload: BDM has not generated the enrollment letter yet.")
        return redirect("student:onboarding")

    if request.method == "POST" and request.FILES.get("signed_letter"):
        signed_file = request.FILES["signed_letter"]

        # Save file to EnrollmentAgreement
        agreement = request.user.student.enrollment_agreement
        agreement.agreement_file.save(signed_file.name, signed_file)

        # Mark as signed
        agreement.is_signed = True
        agreement.signed_at = timezone.now()
        agreement.signature_ip = request.META.get('REMOTE_ADDR')
        agreement.save()

        # Update checklist
        checklist.enrollment_letter_signed = True
        checklist.save()

        messages.success(request, "Signed enrollment letter uploaded successfully!")
        return redirect("student:onboarding")

    messages.error(request, "Please upload a valid file.")
    return redirect("student:onboarding")



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


def lessonplan(request):
    """Simple dashboard"""
    
    return render(request, 'student/lessonplan/lessonplan.html')
    



@role_required("student")
def lessonplan(request):
    student = request.user.student

    # Get the batch for this student
    batch = student.batches.first()  # Assuming one batch per student
    if not batch:
        return render(request, 'student/lessoplan/lessonplan.html', {'error': 'No batch assigned yet.'})

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
