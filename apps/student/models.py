from django.db import models
from django.conf import settings

# Create your models here.


from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils import timezone


# =============================================
# FINANCIAL MODELS
# =============================================



class FeePayment(models.Model):
    """Track all fee payments - booking, admission, installments"""
    
    class PaymentType(models.TextChoices):
        BOOKING = 'booking', 'Booking Fee'
        ADMISSION = 'admission', 'Admission Fee'
        INSTALLMENT = 'installment', 'EMI/Installment'
        FULL_PAYMENT = 'full', 'Full Payment'
        LATE_FEE = 'late_fee', 'Late Fee'
        OTHER = 'other', 'Other'
    
    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Cash'
        CARD = 'card', 'Debit/Credit Card'
        UPI = 'upi', 'UPI'
        NET_BANKING = 'net_banking', 'Net Banking'
        CHEQUE = 'cheque', 'Cheque/PDC'
        LOAN = 'loan', 'Education Loan'
        EMI = 'emi', 'EMI'
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'
    
    student = models.ForeignKey('bdm.Student', on_delete=models.CASCADE, related_name='fee_payments')
    
    # Payment details
    payment_type = models.CharField(max_length=15, choices=PaymentType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    payment_status = models.CharField(max_length=15, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    
    # Transaction details
    transaction_id = models.CharField(max_length=100, unique=True)
    receipt_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    payment_date = models.DateTimeField()
    due_date = models.DateField(null=True, blank=True)
    
    # For EMI/PDC
    installment_number = models.IntegerField(null=True, blank=True, help_text="EMI number (1, 2, 3...)")
    total_installments = models.IntegerField(null=True, blank=True)
    cheque_number = models.CharField(max_length=50, blank=True)
    cheque_date = models.DateField(null=True, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    
    # For loan
    loan_provider = models.CharField(max_length=100, blank=True)
    loan_approval_number = models.CharField(max_length=100, blank=True)
    
    # Additional
    remarks = models.TextField(blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, 
                                   related_name='received_payments')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.student.name} - {self.payment_type} - ₹{self.amount}"
    
    @classmethod
    def get_payment_summary(cls, student):
        """Get payment summary for a student"""
        payments = cls.objects.filter(student=student, payment_status=cls.PaymentStatus.COMPLETED)
        total_paid = sum(p.amount for p in payments)
        
        pending_payments = cls.objects.filter(
            student=student, 
            payment_status=cls.PaymentStatus.PENDING
        )
        total_pending = sum(p.amount for p in pending_payments)
        
        return {
            'total_paid': total_paid,
            'total_pending': total_pending,
            'course_fee': student.selected_course.course_fee,
            'balance': student.selected_course.course_fee - total_paid
        }


# =============================================
# ONBOARDING MODELS
# =============================================

class StudentDocument(models.Model):
    """Documents uploaded by students during onboarding"""
    
    class DocumentType(models.TextChoices):
        PHOTO = 'photo', 'Passport Size Photo'
        AADHAAR = 'aadhaar', 'Aadhaar Card'
        EDUCATION_CERT = 'education', 'Educational Certificate'
        RESUME = 'resume', 'Resume/CV'
    
    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending Verification'
        VERIFIED = 'verified', 'Verified'
        REJECTED = 'rejected', 'Rejected'
    
    student = models.ForeignKey('bdm.Student', on_delete=models.CASCADE, related_name='documents')
    
    # Document details
    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    document_file = models.FileField(
        upload_to='student_documents/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    document_number = models.CharField(max_length=100, blank=True, help_text="Aadhaar/PAN number")
    
    # Verification
    verification_status = models.CharField(max_length=15, choices=VerificationStatus.choices, 
                                          default=VerificationStatus.PENDING)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='verified_documents')
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
     return f"{self.student} - {self.document_type} ({self.verification_status})"


class EnrollmentAgreement(models.Model):
    """Enrollment letter/agreement signed by student"""
    
    student = models.OneToOneField('bdm.Student', on_delete=models.CASCADE, 
                                   related_name='enrollment_agreement')
    
    # Agreement details
    agreement_number = models.CharField(max_length=50, unique=True)
    agreement_date = models.DateField()
    
    # Terms
    course_fee_agreed = models.DecimalField(max_digits=10, decimal_places=2)
    payment_plan = models.CharField(max_length=20, choices=[
        ('full', 'Full Payment'),
        ('emi', 'EMI'),
        ('pdc', 'PDC'),
        ('loan', 'Education Loan')
    ])
    
    # Digital signature
    is_signed = models.BooleanField(default=False)
    signed_at = models.DateTimeField(null=True, blank=True)
    signature_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Agreement file
    agreement_file = models.FileField(upload_to='enrollment_agreements/', null=True, blank=True)
    
    # Approval
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.full_name} - {self.agreement_number}"


class StudentIDCard(models.Model):
    """Student ID card details"""
    
    student = models.OneToOneField('bdm.Student', on_delete=models.CASCADE, 
                                   related_name='id_card')
    
    # ID details
    card_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField()
    expiry_date = models.DateField()
    
    # QR code or barcode
    qr_code = models.ImageField(upload_to='id_cards/qr_codes/', null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_collected = models.BooleanField(default=False)
    collected_date = models.DateField(null=True, blank=True)
    
    # If lost/reissued
    is_lost = models.BooleanField(default=False)
    lost_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.full_name} - {self.card_number}"


# =============================================
# ACADEMIC OPERATIONS MODELS
# =============================================

class LeaveApplication(models.Model):
    """Student leave applications"""
    
    class LeaveType(models.TextChoices):
        SICK = 'sick', 'Sick Leave'
        PERSONAL = 'personal', 'Personal Leave'
        EMERGENCY = 'emergency', 'Emergency'
        OTHER = 'other', 'Other'
    
    class LeaveStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
    
    student = models.ForeignKey('bdm.Student', on_delete=models.CASCADE, related_name='leave_applications')
    batch = models.ForeignKey('bdm.Batch', on_delete=models.CASCADE, related_name='leave_applications')
    
    # Leave details
    leave_type = models.CharField(max_length=15, choices=LeaveType.choices)
    from_date = models.DateField()
    to_date = models.DateField()
    total_days = models.IntegerField()
    reason = models.TextField()
    
    # Supporting documents
    supporting_document = models.FileField(upload_to='leave_documents/', null=True, blank=True,
                                          help_text="Medical certificate, etc.")
    
    # Approval
    status = models.CharField(max_length=15, choices=LeaveStatus.choices, default=LeaveStatus.PENDING)
    approved_by = models.ForeignKey('bdm.Trainer', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='approved_leaves')
    approval_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.name} - {self.leave_type} - {self.from_date} to {self.to_date}"
    
    def save(self, *args, **kwargs):
        # Calculate total days
        if self.from_date and self.to_date:
            self.total_days = (self.to_date - self.from_date).days + 1
        super().save(*args, **kwargs)


class StudentFeedback(models.Model):
    """Student feedback on trainers, courses, sessions"""
    
    class FeedbackType(models.TextChoices):
        TRAINER = 'trainer', 'Trainer Feedback'
        COURSE = 'course', 'Course Feedback'
        SESSION = 'session', 'Session Feedback'
        BATCH = 'batch', 'Batch Feedback'
        FACILITY = 'facility', 'Facility Feedback'
        GENERAL = 'general', 'General Feedback'
    
    student = models.ForeignKey('bdm.Student', on_delete=models.CASCADE, related_name='feedbacks')
    feedback_type = models.CharField(max_length=15, choices=FeedbackType.choices)
    
    # Related entities (optional based on type)
    trainer = models.ForeignKey('bdm.Trainer', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='student_feedbacks')
    course = models.ForeignKey('bdm.Course', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='student_feedbacks')
    batch = models.ForeignKey('bdm.Batch', on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='student_feedbacks')
    
    # Ratings (1-5)
    content_quality = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    teaching_methodology = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    responsiveness = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    overall_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Comments
    comments = models.TextField()
    suggestions = models.TextField(blank=True)
    
    # Anonymous option
    is_anonymous = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.name if not self.is_anonymous else 'Anonymous'} - {self.feedback_type} - {self.overall_rating}★"


# =============================================
# CERTIFICATION MODELS
# =============================================

class CertificationRequest(models.Model):
    """Student confirmation details before certificate generation"""
    
    student = models.ForeignKey('bdm.Student', on_delete=models.CASCADE, 
                               related_name='certification_requests')
    batch = models.ForeignKey('bdm.Batch', on_delete=models.CASCADE)
    
    # Confirmed details
    confirmed_name = models.CharField(max_length=200, help_text="Name as it should appear on certificate")
    confirmed_email = models.EmailField()
    confirmed_phone = models.CharField(max_length=15)
    confirmed_address = models.TextField()
    
    # Additional info
    linkedin_profile = models.URLField(blank=True)
    github_profile = models.URLField(blank=True)
    portfolio_link = models.URLField(blank=True)
    
    # Consent
    details_confirmed = models.BooleanField(default=False)
    consent_to_display = models.BooleanField(default=False, 
                                            help_text="Allow to display in success stories")
    
    # Submission
    form_submitted_at = models.DateTimeField(auto_now_add=True)
    google_form_response_id = models.CharField(max_length=100, blank=True)
    
    # Processing
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-form_submitted_at']
    
    def __str__(self):
        return f"{self.student.name} - Certification Request"


# =============================================
# PLACEMENT MODELS
# =============================================

class PlacementProfile(models.Model):
    """Student placement profile and preferences"""
    
    class PlacementStatus(models.TextChoices):
        WILLING = 'willing', 'Willing for Placement'
        NOT_WILLING = 'not_willing', 'Not Willing'
        ALREADY_PLACED = 'placed', 'Already Placed'
        ON_HOLD = 'on_hold', 'On Hold'
    
    student = models.OneToOneField('bdm.Student', on_delete=models.CASCADE, 
                                   related_name='placement_profile')
    
    # Placement consent
    placement_status = models.CharField(max_length=20, choices=PlacementStatus.choices, 
                                       default=PlacementStatus.WILLING)
    consent_date = models.DateField(null=True, blank=True)
    
    # Profile details
    resume = models.FileField(upload_to='placement/resumes/')
    current_ctc = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                     help_text="Current CTC in lakhs")
    expected_ctc = models.DecimalField(max_digits=10, decimal_places=2, 
                                      help_text="Expected CTC in lakhs")
    
    # Skills
    technical_skills = models.TextField()
    certifications = models.TextField(blank=True)
    projects_completed = models.TextField(blank=True)
    
    # Preferences
    preferred_locations = models.CharField(max_length=200, help_text="Comma-separated cities")
    preferred_job_type = models.CharField(max_length=50, choices=[
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('internship', 'Internship'),
        ('contract', 'Contract')
    ], default='full_time')
    
    # Availability
    notice_period_days = models.IntegerField(default=0, help_text="Notice period in days")
    available_from = models.DateField(null=True, blank=True)
    
    # Social profiles
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.name} - Placement Profile"


class PlacementDrive(models.Model):
    """Placement drives organized by the institute"""
    
    class DriveStatus(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        ONGOING = 'ongoing', 'Ongoing'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
    
    # Company details
    company_name = models.CharField(max_length=200)
    company_description = models.TextField()
    company_website = models.URLField(blank=True)
    
    # Drive details
    drive_date = models.DateField()
    drive_time = models.TimeField()
    mode = models.CharField(max_length=20, choices=[
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('hybrid', 'Hybrid')
    ])
    venue = models.CharField(max_length=200, blank=True)
    meeting_link = models.URLField(blank=True)
    
    # Job details
    job_role = models.CharField(max_length=200)
    job_description = models.TextField()
    ctc_offered = models.CharField(max_length=100)
    positions_available = models.IntegerField()
    
    # Eligibility
    eligible_courses = models.ManyToManyField('bdm.Course', related_name='placement_drives')
    minimum_percentage = models.IntegerField(default=50)
    minimum_attendance = models.IntegerField(default=75)
    
    # Status
    status = models.CharField(max_length=15, choices=DriveStatus.choices, default=DriveStatus.SCHEDULED)
    
    # Coordinator
    coordinator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name='coordinated_drives')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-drive_date']
    
    def __str__(self):
        return f"{self.company_name} - {self.job_role} - {self.drive_date}"


class PlacementApplication(models.Model):
    """Student applications for placement drives"""
    
    class ApplicationStatus(models.TextChoices):
        APPLIED = 'applied', 'Applied'
        SHORTLISTED = 'shortlisted', 'Shortlisted'
        INTERVIEWED = 'interviewed', 'Interviewed'
        SELECTED = 'selected', 'Selected'
        REJECTED = 'rejected', 'Rejected'
        OFFER_ACCEPTED = 'offer_accepted', 'Offer Accepted'
        OFFER_DECLINED = 'offer_declined', 'Offer Declined'
    
    student = models.ForeignKey('bdm.Student', on_delete=models.CASCADE, 
                               related_name='placement_applications')
    placement_drive = models.ForeignKey(PlacementDrive, on_delete=models.CASCADE,
                                       related_name='applications')
    
    # Application
    applied_at = models.DateTimeField(auto_now_add=True)
    resume_submitted = models.FileField(upload_to='placement/applications/')
    cover_letter = models.TextField(blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=ApplicationStatus.choices, 
                             default=ApplicationStatus.APPLIED)
    
    # Interview details
    interview_scheduled = models.BooleanField(default=False)
    interview_date = models.DateTimeField(null=True, blank=True)
    interview_mode = models.CharField(max_length=20, blank=True)
    interview_feedback = models.TextField(blank=True)
    
    # Offer details
    offer_letter = models.FileField(upload_to='placement/offers/', null=True, blank=True)
    offered_ctc = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    
    # Notes
    remarks = models.TextField(blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'placement_drive']
        ordering = ['-applied_at']
    
    def __str__(self):
        return f"{self.student.name} - {self.placement_drive.company_name} - {self.status}"


# =============================================
# LEARNING RESOURCE MODELS
# =============================================

class LMSAccess(models.Model):
    """Track student access to Learning Management System"""
    
    student = models.OneToOneField('bdm.Student', on_delete=models.CASCADE, 
                                   related_name='lms_access')
    
    # LMS credentials
    lms_username = models.CharField(max_length=100, unique=True)
    lms_user_id = models.CharField(max_length=100, blank=True)
    
    # Access details
    is_active = models.BooleanField(default=True)
    activated_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    
    # Usage tracking
    last_login = models.DateTimeField(null=True, blank=True)
    total_login_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.name} - LMS Access"


class BookIssue(models.Model):
    """Track books issued to students"""
    
    class BookStatus(models.TextChoices):
        ISSUED = 'issued', 'Issued'
        RETURNED = 'returned', 'Returned'
        LOST = 'lost', 'Lost'
        DAMAGED = 'damaged', 'Damaged'
    
    student = models.ForeignKey('bdm.Student', on_delete=models.CASCADE, related_name='issued_books')
    
    # Book details
    book_title = models.CharField(max_length=200)
    book_code = models.CharField(max_length=50)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=20, blank=True)
    
    # Issue details
    issue_date = models.DateField()
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=15, choices=BookStatus.choices, default=BookStatus.ISSUED)
    
    # Charges
    late_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    damage_charge = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Library staff
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                 related_name='issued_books')
    
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"{self.student.name} - {self.book_title} - {self.status}"
    
    @property
    def is_overdue(self):
        """Check if book is overdue"""
        if self.status == self.BookStatus.ISSUED:
            return timezone.now().date() > self.expected_return_date
        return False