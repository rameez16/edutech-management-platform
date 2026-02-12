from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, FileResponse
from django.views.decorators.http import require_POST

from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum

from .forms import EnrollmentAgreementForm

from decimal import Decimal
import uuid, os

from apps.accounts.decorators import role_required

from apps.bdm.models import Student, StudentAdminProfile, Batch, OnboardingChecklist, Course



from apps.trainer.models import Module, LessonPlan

from .models import FeePayment, StudentDocument, EnrollmentAgreement, StudentIDCard


# Create your views here.




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




def download_document(request, doc_id):
    document = get_object_or_404(StudentDocument, id=doc_id)

    if not document.document_file:
        raise Http404("File not found.")

    return FileResponse(
        document.document_file.open('rb'),
        as_attachment=True,
        filename=os.path.basename(document.document_file.name)
    )