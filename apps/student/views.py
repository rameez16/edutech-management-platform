
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import StudentDocument
from apps.bdm.models import Student

# Create your views here.





def dashboard(request):
    """Simple dashboard"""
    
    return render(request, 'dashboard/dashboard.html')


def onboard(request):
    
    return render(request, 'dashboard/onboarding.html')



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
        "dashboard/uploaddoc.html",
        {
            "docs": existing_docs,
            "locked": locked
        }
    )