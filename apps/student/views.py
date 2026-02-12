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

from .models import EnrollmentAgreement
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages


#one time payment
@login_required
def payment(request):

    student = request.user.student

    if student.enrollment_agreement.payment_plan.lower() != "full":
        messages.error(request, "Full payment not allowed")
        return redirect("student:payment_gateway")

    batch = student.batches.first()

    if not batch:
        messages.error(request, "No batch assigned.")
        return redirect("student:dashboard")

    course_fee = batch.course.course_fee
    admission_fee = course_fee * Decimal("0.10")

    payments = FeePayment.objects.filter(student=student)

    paid_amount = payments.filter(
        payment_status=FeePayment.PaymentStatus.COMPLETED
    ).aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00")

    total_fee = course_fee
    pending_amount = max(total_fee - paid_amount, Decimal("0.00"))

    # ✅ ADDED (THIS WAS MISSING)
    existing_payment = payments.filter(
        payment_type=FeePayment.PaymentType.FULL_PAYMENT
    ).first()

    # ✅ ADDED (RECEIPT UPLOAD LOGIC)
    if request.method == "POST":

        if existing_payment:
            messages.warning(request, "Payment already submitted")
            return redirect("student:payment")

        receipt = request.FILES.get("receipt")

        if not receipt:
            messages.error(request, "Please upload receipt")
            return redirect("student:payment")

        payment = FeePayment.objects.create(
            student=student,
            payment_type=FeePayment.PaymentType.FULL_PAYMENT,
            amount=pending_amount,
            payment_method=FeePayment.PaymentMethod.UPI,
            payment_status=FeePayment.PaymentStatus.PENDING,
            payment_date=timezone.now(),
            transaction_id=f"FULL-{uuid.uuid4().hex[:10]}",
            receipt_number=f"RCPT-{uuid.uuid4().hex[:6]}"
        )

        PaymentDocument.objects.create(
            fee_payment=payment,   # ✅ CORRECT OBJECT
            document_type=PaymentDocument.DocumentType.RECEIPT,
            document_file=receipt,
            uploaded_by=request.user
        )

        messages.success(request, "Receipt uploaded successfully")
        return redirect("student:payment")

    return render(request, "student/payment/payment.html", {
        "student": student,
        
        "course_fee": course_fee,
        "admission_fee": admission_fee,
        "total_fee": total_fee,
        "paid_amount": paid_amount,
        "pending_amount": pending_amount,
        "existing_payment": existing_payment,   # ✅ CRITICAL FIX
    })




#admission fee


@login_required
def admission(request):

    student = request.user.student
    batch = student.batches.first()

    if not batch:
        messages.error(request, "No batch assigned.")
        return redirect("student:dashboard")
    course = batch.course   # ✅ ADD THIS LINE

    course_fee = batch.course.course_fee
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

        if receipt_file:
            PaymentDocument.objects.create(
                fee_payment=admission_fee,
                document_type=PaymentDocument.DocumentType.RECEIPT,
                document_file=receipt_file,
                uploaded_by=request.user
            )

        messages.success(request, "✅ Admission Fee Paid Successfully")

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

















