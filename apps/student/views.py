from django.shortcuts import render, redirect, get_object_or_404
from apps.accounts.decorators import role_required
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum

from apps.bdm.models import Student
from .models import FeePayment

from apps.bdm.models import OnboardingChecklist
import uuid, os

from .models import StudentDocument


# Create your views here.





def dashboard(request):
    """Simple dashboard"""
    
    return render(request, 'student/dashboard/dashboard.html')
    



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
    if onboarding.documents_verified:   # ← your checklist flag
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
            label for key, label in REQUIRED_DOCS.items()
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
        }
    )


@role_required("student")
def onboard(request):
    student = request.user.student  # get logged-in student's object
    checklist, _ = OnboardingChecklist.objects.get_or_create(student=student)

    # Calculate number of completed steps
    completed_steps = 0
    if checklist.documents_verified:
        completed_steps += 1
    if getattr(checklist, "enrollment_uploaded", False):
        completed_steps += 1
    if getattr(checklist, "id_card_downloaded", False):
        completed_steps += 1

    # Calculate progress percentage
    progress_percentage = (completed_steps / 3) * 100

    context = {
        "completed_steps": completed_steps,
        "progress_percentage": progress_percentage,
        "all_docs_verified": checklist.documents_verified,
        "checklist": checklist,
    }


    return render(request, "student/onboarding/onboarding.html", context)


def lessonplan(request):
    """Simple dashboard"""
    
    return render(request, 'student/lessonplan/lessonplan.html')
    
