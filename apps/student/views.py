from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum
from apps.bdm.models import Student,Trainer,Course,Batch
from .models import FeePayment,StudentFeedback
from django.contrib.auth import update_session_auth_hash
import uuid, os
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import StudentDocument
from . import views
from django.contrib.auth.decorators import login_required
import uuid
from apps.bdm.models import PaymentDocument



# Create your views here.
#dashboard

def dashboard(request):
    """Simple dashboard"""
    
    return render(request, 'student/dashboard/dashboard.html')
    
#one time payment
@login_required
def payment(request):
    student = get_object_or_404(Student, user=request.user)

    # -----------------------------
    # FEE CALCULATION
    # -----------------------------
    admission_fee = Decimal("5400.00")
    course_fee = Decimal("15000.00")
    total_fee = admission_fee + course_fee

    paid_amount = FeePayment.objects.filter(
        student=student,
        payment_status=FeePayment.PaymentStatus.COMPLETED
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    pending_amount = total_fee - paid_amount

    existing_payment = FeePayment.objects.filter(
        student=student,
        payment_type=FeePayment.PaymentType.FULL_PAYMENT
    ).first()

    # -----------------------------
    # HANDLE POST
    # -----------------------------
    if request.method == "POST":

        receipt_file = request.FILES.get("receipt")

        if not receipt_file:
            messages.error(request, "Please upload payment receipt")
            return redirect("student:payment")

        receipt_no = f"RCPT-{uuid.uuid4().hex[:8].upper()}"
        transaction_id = f"FULL-{uuid.uuid4().hex[:12].upper()}"

        # -----------------------------
        # 1️⃣ SAVE PAYMENT (STUDENT APP)
        # -----------------------------
        fee_payment = FeePayment.objects.create(
            student=student,
            payment_type=FeePayment.PaymentType.FULL_PAYMENT,
            amount=pending_amount,
            payment_method=FeePayment.PaymentMethod.UPI,
            payment_status=FeePayment.PaymentStatus.PENDING,  # verification pending
            payment_date=timezone.now(),
            transaction_id=transaction_id,
            receipt_number=receipt_no,
            remarks="Receipt uploaded – verification pending"
        )

        # -----------------------------
        # 2️⃣ SAVE PAYMENT DOCUMENT (BDM)
        # -----------------------------
        PaymentDocument.objects.create(
            fee_payment=fee_payment,
            document_type=PaymentDocument.DocumentType.RECEIPT,
            document_file=receipt_file,
            description=(
                f"FULL PAYMENT RECEIPT\n"
                f"Student: {student.full_name}\n"
                f"Txn ID: {transaction_id}\n"
                f"Receipt No: {receipt_no}\n"
                f"Admission Fee: ₹{admission_fee}\n"
                f"Course Fee: ₹{course_fee}\n"
                f"Total Paid: ₹{pending_amount}\n"
                f"Payment Method: UPI\n"
                f"Status: Verification Pending"
            ),
            uploaded_by=request.user
        )

        messages.success(
            request,
            "Payment receipt uploaded successfully. Awaiting verification."
        )
        return redirect("student:payment")

    # -----------------------------
    # RENDER PAGE
    # -----------------------------
    return render(request, "student/payment/payment.html", {
        "student": student,
        "admission_fee": admission_fee,
        "course_fee": course_fee,
        "total_fee": total_fee,
        "paid_amount": paid_amount,
        "pending_amount": pending_amount,
        "existing_payment": existing_payment,
    })

#admission fee

@login_required
def admission(request):
    student = Student.objects.get(user=request.user)

    ADMISSION_AMOUNT = 5400

    admission_fee = FeePayment.objects.filter(
        student=student,
        payment_type=FeePayment.PaymentType.ADMISSION
    ).first()

    if request.method == "POST":

        # ❌ Prevent double payment
        if admission_fee and admission_fee.payment_status == FeePayment.PaymentStatus.COMPLETED:
            messages.warning(request, "⚠️ Admission fee already paid.")
            return render(request, "student/payment/admission.html", {
                "student": student,
                "admission_fee": admission_fee,
                "admission_amount": ADMISSION_AMOUNT
            })

        receipt_no = f"RCPT-{uuid.uuid4().hex[:8].upper()}"
        transaction_id = f"ADM-{uuid.uuid4().hex[:12].upper()}"

        # 1️⃣ Fee Payment
        if not admission_fee:
            admission_fee = FeePayment.objects.create(
                student=student,
                payment_type=FeePayment.PaymentType.ADMISSION,
                amount=ADMISSION_AMOUNT,
                payment_method=FeePayment.PaymentMethod.UPI,
                payment_status=FeePayment.PaymentStatus.COMPLETED,
                payment_date=timezone.now(),
                transaction_id=transaction_id,
                receipt_number=receipt_no
            )
        else:
            admission_fee.amount = ADMISSION_AMOUNT
            admission_fee.payment_method = FeePayment.PaymentMethod.UPI
            admission_fee.payment_status = FeePayment.PaymentStatus.COMPLETED
            admission_fee.payment_date = timezone.now()
            admission_fee.transaction_id = transaction_id
            admission_fee.receipt_number = receipt_no
            admission_fee.save()

        # 2️⃣ Receipt Upload (optional)
        receipt_file = request.FILES.get("receipt")

        PaymentDocument.objects.create(
            fee_payment=admission_fee,
            document_type=PaymentDocument.DocumentType.RECEIPT,
            document_file=receipt_file,
            description=(
                f"Admission fee paid via UPI\n"
                f"Txn ID: {transaction_id}\n"
                f"Receipt No: {receipt_no}\n"
                f"Amount: ₹{ADMISSION_AMOUNT}"
            ),
            uploaded_by=request.user
        )

        messages.success(request, "✅ Admission fee payment successful.")

    return render(request, "student/payment/admission.html", {
        "student": student,
        "admission_fee": admission_fee,
        "admission_amount": ADMISSION_AMOUNT
    })


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

#EMI

def emi(request):
    student = Student.objects.get(user=request.user)

    context = {
        "student": student,
        "user": request.user,   # Django auth user
        "total_fee": 60000,
        "paid_amount": 45000,   # example (replace with calculation)
        "pending_amount": 5000, # example
        "admission_fee": 5000,
        "course_fee": 45000,
    }

    return render(request, "student/payment/emi.html", context)

#Installments

@login_required
def installments(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    COURSE_FEE = Decimal("15000.00")

    # Admission paid
    admission_paid = (
        FeePayment.objects.filter(
            student=student,
            payment_type=FeePayment.PaymentType.ADMISSION,
            payment_status=FeePayment.PaymentStatus.COMPLETED
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    # ONLY COMPLETED counts as paid
    paid_amount = (
        FeePayment.objects.filter(
            student=student,
            payment_status=FeePayment.PaymentStatus.COMPLETED
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    total_fee = admission_paid + COURSE_FEE
    pending_amount = max(total_fee - paid_amount, Decimal("0.00"))

    installments = FeePayment.objects.filter(
        student=student,
        payment_type=FeePayment.PaymentType.INSTALLMENT
    ).order_by("installment_number")

    return render(
        request,
        "student/payment/installments.html",
        {
            "student": student,
            "admission_fee": admission_paid,
            "course_fee": COURSE_FEE,
            "total_fee": total_fee,
            "paid_amount": paid_amount,
            "pending_amount": pending_amount,
            "installments": installments,
        }
    )
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
def installments_view(request):
    # logged-in student
    student = get_object_or_404(Student, user=request.user)

    # fetch installments
    installments = FeePayment.objects.filter(
        student=student,
        payment_type=FeePayment.PaymentType.INSTALLMENT
    ).order_by("installment_number")

    context = {
        "student": student,
        "installments": installments,
    }

    return render(
        request,
        "student/payment/install_view.html",
        context
    )
def pdc_view(request):
    return render(request, 'student/payment/pdc_view.html')
def onetime_view(request):
    student = get_object_or_404(Student, user=request.user)

    # Fixed / DB values
    admission_fee = Decimal("5000.00")
    course_fee = 8400
    total_fee = admission_fee + course_fee
     # ✅ One-Time payment record (FULL_PAYMENT)
    payment = FeePayment.objects.filter(
        student=student,
        payment_type=FeePayment.PaymentType.FULL_PAYMENT
    ).first()

    context = {
        "student": student,
        "admission_fee": admission_fee,
        "course_fee": course_fee,
        "total_fee": total_fee,
        "payment_mode": "One Time Payment",
        
          # ✅ Safe values (if payment exists)
        "payment_status": payment.payment_status if payment else "Not Paid",
        "payment_date": payment.payment_date if payment else None,
    }

    return render(
        request,
        "student/payment/one_time_view.html",
        context
    )
def emi_view(request):
    return render(request, 'student/payment/emi_view.html')

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


def onboard(request):
    
    return render(request, 'student/dashboard/onboarding.html')



MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def upload(request):
    student = Student.objects.first()  # temp until login

    REQUIRED_DOCS = {
        "photo": "Photograph",
        "education": "Educational Certificates",
        "residence": "Residence Proof",
        "aadhaar": "Aadhaar",
    }

    OPTIONAL_DOCS = {
        "resume": "Resume / CV"
    }

    ALL_DOCS = {**REQUIRED_DOCS, **OPTIONAL_DOCS}

    # Existing documents mapped by document_type
    existing_docs = {
        doc.document_type: doc
        for doc in StudentDocument.objects.filter(student=student)
    }


# Lock uploads if ANY document is pending or verified
    locked = any(
        doc.verification_status in [
            StudentDocument.VerificationStatus.PENDING,
            StudentDocument.VerificationStatus.VERIFIED
        ]
        for doc in existing_docs.values()
    )


    if request.method == "POST":

        if locked:
            messages.error(request, "Documents already submitted.")
            return redirect(request.path)

        # Validate required documents
        missing = []
        for key, label in REQUIRED_DOCS.items():
            if not request.FILES.get(key):
                missing.append(label)

        if missing:
            messages.error(
                request,
                "Please upload: " + ", ".join(missing)
            )
            return redirect(request.path)

        # Save / update documents
        for key, label in ALL_DOCS.items():
            file = request.FILES.get(key)
            if not file:
                continue

            if file.size > MAX_FILE_SIZE:
                messages.error(request, f"{label} exceeds 5MB")
                return redirect(request.path)

            StudentDocument.objects.update_or_create(
                student=student,
                document_type=key,
                defaults={
                    "document_file": file,
                    "verification_status": StudentDocument.VerificationStatus.PENDING
                }
            )

        messages.success(
            request,
            "Documents submitted. Verification in progress."
        )
        return redirect(request.path)

    return render(
        request,
        "student/dashboard/uploaddoc.html",
        {
            "docs": existing_docs,
            "locked": locked
        }
    )

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
def lms_dashboard(request):
    return render(request, 'student/LMS//lms_dashboard.html')
