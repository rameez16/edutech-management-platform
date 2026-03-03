from django.db import models
from django.conf import settings
from apps.bdm.constants import REQUIRED_DOCUMENT_TYPES
from cloudinary_storage.storage import MediaCloudinaryStorage
from cloudinary_storage.storage import RawMediaCloudinaryStorage
from apps.student.models import StudentDocument

# Create your models here.

from django.utils import timezone



class Lead(models.Model):
    
    class LeadStatus(models.TextChoices):
        NEW = 'new', 'New'
        ASSIGNED = 'assigned', 'Assigned'
        CONVERTED = 'converted', 'Converted'
        IDLE = 'idle', 'Idle'
        DROPPED = 'dropped', 'Dropped'
    
    class ModeChoice(models.TextChoices):
        REMOTE = 'remote', 'Remote'
        OFFLINE = 'offline', 'Offline'
    
    # Basic Information
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    preferred_course = models.ForeignKey('Course', on_delete=models.SET_NULL, null=True, blank=True)
    mode = models.CharField(max_length=10, choices=ModeChoice.choices, default=ModeChoice.OFFLINE)
    status = models.CharField(max_length=10, choices=LeadStatus.choices, default=LeadStatus.NEW)
    
    
        # -----------------------------------
    # 2️⃣ Telecaller Collected Information
    # -----------------------------------

    educational_qualification = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    confirmed_course = models.ForeignKey(
        'Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmed_leads"
    )

    interested_batch = models.ForeignKey(
        'Batch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_batches"
    )

    discussed_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    payment_plan = models.CharField(
        max_length=20,
        choices=[
            ("full", "Full Payment"),
            ("installment", "Installment"),
            ("emi", "EMI"),
            ("pdc", "PDC"),
        ],
        blank=True,
        null=True
    )
    admission_fee_paid = models.BooleanField(
        default=False
    )

    admission_fee_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

   
    telecaller_notes = models.TextField(blank=True)
    
    # Assignment and Tracking
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                                   limit_choices_to={'groups__name': 'TELE-CALLER'})
    enquiry_date = models.DateTimeField(auto_now_add=True)
    last_followup = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-enquiry_date']
    
    def __str__(self):
        return f"{self.name} - {self.status}"
    
    
class Course(models.Model):
    name = models.CharField(max_length=200)
    description=models.CharField(max_length=200,blank=True)
    duration = models.CharField(max_length=50)  # e.g., "3 months", "6 weeks"
    tech_stack = models.TextField()  # Comma-separated or JSON field
    course_fee = models.DecimalField(max_digits=10, decimal_places=2)
    syllabus = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def tech_stack_list(self):
        return [tech.strip() for tech in self.tech_stack.split(',')]


class Trainer(models.Model):

    class GenderChoice(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'

    class TeachingStyle(models.TextChoices):
        PROJECT = 'project', 'Project-based'
        THEORY = 'theory', 'Theory-oriented'
        MIXED = 'mixed', 'Mixed approach'

    # --------------------------------------------------
    # RELATION
    # --------------------------------------------------
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trainer"
    )

    # --------------------------------------------------
    # BASIC IDENTITY (Trainer Editable)
    # --------------------------------------------------
    full_name = models.CharField(max_length=150, blank=True)
    profile_photo = models.ImageField(upload_to="trainers/", null=True, blank=True,storage=MediaCloudinaryStorage())
    gender = models.CharField(max_length=1, choices=GenderChoice.choices, blank=True)

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    bio = models.TextField(blank=True)

    languages_spoken = models.CharField(
        max_length=200,
        blank=True,
        help_text="Comma-separated languages"
    )

    location = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, blank=True)

    # --------------------------------------------------
    # PROFESSIONAL EXPERTISE (Trainer Editable)
    # --------------------------------------------------
    qualification = models.CharField(max_length=200, blank=True)

    certifications = models.TextField(
        blank=True,
        help_text="AWS, Google, Microsoft etc."
    )

    primary_domain = models.CharField(
        max_length=100,
        blank=True,
        help_text="Backend / Frontend / Data etc."
    )

    secondary_skills = models.TextField(
        blank=True,
        help_text="DevOps, Cloud, AI etc."
    )

    coding_languages = models.TextField(blank=True)
    frameworks = models.TextField(blank=True)

    experience_years = models.PositiveIntegerField(null=True, blank=True)
    teaching_experience_years = models.PositiveIntegerField(null=True, blank=True)

    teaching_style = models.CharField(
        max_length=20,
        choices=TeachingStyle.choices,
        blank=True
    )

    portfolio_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)

    # --------------------------------------------------
    # PROFILE STATUS
    # --------------------------------------------------
    profile_completed = models.BooleanField(default=False)

    # --------------------------------------------------
    # META
    # --------------------------------------------------
    def __str__(self):
        return self.full_name or self.user.username
    
    

class TrainerAdminProfile(models.Model):

    trainer = models.OneToOneField(
        "Trainer",
        on_delete=models.CASCADE,
        related_name="admin_profile"
    )

    # -----------------------------
    # HR / ADMIN CONTROLS
    # -----------------------------
    employee_id = models.CharField(
        max_length=20,
        blank=True
    )

    date_joined = models.DateField(auto_now_add=True)

    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Monthly salary"
    )

    batches_assigned = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of batches assigned"
    )

    performance_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True
    )

    background_verified = models.BooleanField(default=False)
    profile_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # -----------------------------
    # AUTO EMPLOYEE ID (NO SIGNAL)
    # -----------------------------
    def save(self, *args, **kwargs):
        if not self.employee_id:
            last_pk = (
                TrainerAdminProfile.objects
                .order_by("-pk")
                .values_list("pk", flat=True)
                .first()
            ) or 0

            self.employee_id = f"TRN-{last_pk + 1:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_id} | {self.trainer}"
    
    
class Student(models.Model):

    class GenderChoice(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'

    # --------------------------------------------------
    # RELATION
    # --------------------------------------------------
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student"
    )

    # --------------------------------------------------
    # BASIC IDENTITY (Student Editable)
    # --------------------------------------------------
    full_name = models.CharField(max_length=150, blank=True)
    profile_photo = models.ImageField(upload_to="students/", null=True, blank=True,storage=MediaCloudinaryStorage())
    gender = models.CharField(max_length=1, choices=GenderChoice.choices, blank=True)

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    # --------------------------------------------------
    # ACADEMIC PROFILE (Student Editable)
    # --------------------------------------------------
    bio = models.TextField(blank=True)

    current_education = models.CharField(
        max_length=150,
        blank=True,
        help_text="BSc / Diploma / High School etc."
    )

    institution = models.CharField(max_length=200, blank=True)

    learning_goals = models.TextField(blank=True)

    preferred_domain = models.CharField(
        max_length=100,
        blank=True,
        help_text="Web / Data / Mobile / AI"
    )

    skills = models.TextField(
        blank=True,
        help_text="Python, HTML, SQL etc."
    )

    experience_level = models.CharField(
        max_length=50,
        blank=True,
        help_text="Beginner / Intermediate / Advanced"
    )

    portfolio_url = models.URLField(blank=True)

    # --------------------------------------------------
    # PROFILE STATUS
    # --------------------------------------------------
    profile_completed = models.BooleanField(default=False)
    
    
    
    def required_documents_queryset(self):
        return self.documents.filter(
            document_type__in=REQUIRED_DOCUMENT_TYPES
        )
    
    print(required_documents_queryset)

    def all_required_documents_uploaded(self):
        return self.required_documents_queryset().count() == len(REQUIRED_DOCUMENT_TYPES)

    def all_required_documents_verified(self):
        qs = self.required_documents_queryset()

        if qs.count() != len(REQUIRED_DOCUMENT_TYPES):
            return False

        return not qs.filter(
            verification_status__in=[
                StudentDocument.VerificationStatus.PENDING,
                StudentDocument.VerificationStatus.REJECTED,
            ]
        ).exists()

    # --------------------------------------------------
    # META
    # --------------------------------------------------
    def __str__(self):
        return self.full_name or self.user.username
    





    
    
class Batch(models.Model):
    # Basic Information
    name = models.CharField(max_length=100, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    
    trainers = models.ManyToManyField(
        Trainer,
        related_name='batches',
        blank=True
    )
    
    # Schedule
    start_date = models.DateField()
    expected_finish_date = models.DateField()
    duration_months = models.IntegerField()  # Duration in months
    requested_extension = models.BooleanField(default=False)
    
    # Students (Many-to-Many through auto-created junction table)
    students = models.ManyToManyField(Student, related_name="batches", blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Batches"
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} - {self.course.name}"
    
    @property
    def total_students(self):
        return self.students.count()
    
    @property
    def is_completed(self):
        from django.utils import timezone
        return timezone.now().date() > self.expected_finish_date
    
    def get_average_attendance(self):
        students = self.students.filter(attendance_percentage__isnull=False)
        if students.exists():
            return students.aggregate(models.Avg('attendance_percentage'))['attendance_percentage__avg']
        return 0        
    
    

class StudentAdminProfile(models.Model):

    student = models.OneToOneField(
        "Student",
        on_delete=models.CASCADE,
        related_name="admin_profile"
    )

    # --------------------------------------------------
    # ADMIN CONTROLS
    # --------------------------------------------------
    student_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    date_joined = models.DateField(auto_now_add=True)

    enrolled_course = models.ForeignKey(Course,on_delete=models.SET_NULL,null=True,blank=True)

    batch_assigned = models.ForeignKey(Batch,on_delete=models.SET_NULL,null=True,blank=True
)

    booking_fee_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )



    background_verified = models.BooleanField(default=False)
    profile_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # --------------------------------------------------
    # AUTO STUDENT ID (NO SIGNAL)
    # --------------------------------------------------
    def save(self, *args, **kwargs):
        if not self.student_id:
            last_pk = (
                StudentAdminProfile.objects
                .order_by("-pk")
                .values_list("pk", flat=True)
                .first()
            ) or 0

            self.student_id = f"STD-{last_pk + 1:04d}"

        super().save(*args, **kwargs)

    # --------------------------------------------------
    # META
    # --------------------------------------------------
    def __str__(self):
        return f"{self.student_id} | {self.student}"    
    
   
class TeleCallerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    department = models.CharField(max_length=100, default='Business Development')
    join_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Performance Metrics
    total_leads = models.IntegerField(default=0)
    converted_leads = models.IntegerField(default=0)
    
    def __str__(self):
        return f"TELE-CALLER: {self.user.get_full_name()}"
    
    def update_conversion_rate(self):
        total = self.total_leads if self.total_leads > 0 else 1
        return (self.converted_leads / total) * 100 
    
    
    
class Counselor(models.Model):
    """
    Counselors who handle lead follow-ups
    Similar to TeleCallerProfile but with counseling focus
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    department = models.CharField(max_length=100, default='Admissions & Counseling')
    join_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Specialization
    specialization_courses = models.ManyToManyField('Course', blank=True,
                                                    help_text="Courses this counselor specializes in")
    
    # Performance Metrics
    total_leads_assigned = models.IntegerField(default=0)
    total_conversions = models.IntegerField(default=0)
    active_leads = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Counselor: {self.user.get_full_name()}"
    
    @property
    def conversion_rate(self):
        if self.total_leads_assigned > 0:
            return (self.total_conversions / self.total_leads_assigned) * 100
        return 0


class CallHistory(models.Model):
    """
    Track all calls made to leads
    """
    class CallStatus(models.TextChoices):
        ANSWERED = 'answered', 'Answered'
        NO_ANSWER = 'no_answer', 'No Answer'
        BUSY = 'busy', 'Busy'
        CALLBACK = 'callback', 'Requested Callback'
        VOICEMAIL = 'voicemail', 'Voicemail'
    
    class CallOutcome(models.TextChoices):
        INTERESTED = 'interested', 'Interested'
        NOT_INTERESTED = 'not_interested', 'Not Interested'
        NEED_INFO = 'need_info', 'Need More Info'
        FOLLOWUP = 'followup', 'Follow-up Required'
        CONVERTED = 'converted', 'Converted'
    
    lead = models.ForeignKey('Lead', on_delete=models.CASCADE, related_name='call_history')
    caller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                              related_name='calls_made')
    
    # Call details
    call_date = models.DateTimeField(default=timezone.now)
    duration_minutes = models.IntegerField(default=0)
    call_status = models.CharField(max_length=15, choices=CallStatus.choices)
    call_outcome = models.CharField(max_length=20, choices=CallOutcome.choices, 
                                   null=True, blank=True)
    
    # Notes
    discussion_summary = models.TextField(blank=True)
    concerns_raised = models.TextField(blank=True)
    action_items = models.TextField(blank=True)
    
    # Follow-up
    followup_required = models.BooleanField(default=False)
    next_followup_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-call_date']
        verbose_name_plural = "Call Histories"
    
    def __str__(self):
        return f"{self.lead.name} - {self.call_date.strftime('%Y-%m-%d %H:%M')}"


class PaymentDocument(models.Model):
    """
    Upload payment receipts, transaction screenshots, etc.
    Links to FeePayment from student portal models
    """
    class DocumentType(models.TextChoices):
        RECEIPT = 'receipt', 'Payment Receipt'
        SCREENSHOT = 'screenshot', 'Transaction Screenshot'
        CHEQUE_COPY = 'cheque', 'Cheque Copy'
        LOAN_APPROVAL = 'loan', 'Loan Approval Letter'
        OTHER = 'other', 'Other'
    
    fee_payment = models.ForeignKey('student.FeePayment', on_delete=models.CASCADE,
                                   related_name='documents')
    
    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    document_file = models.FileField(upload_to='payment_documents/%Y/%m/',storage=MediaCloudinaryStorage())
    description = models.TextField(blank=True)
    
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.fee_payment.student.full_name} - {self.document_type}"


class PaymentReminder(models.Model):
    """
    Automated and manual payment reminders
    """
    class ReminderType(models.TextChoices):
        BOOKING_FEE = 'booking', 'Booking Fee Reminder'
        INSTALLMENT = 'installment', 'Installment Due'
        BALANCE_FEE = 'balance', 'Balance Fee Reminder'
        OVERDUE = 'overdue', 'Overdue Payment'
    
    class ReminderStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        ACKNOWLEDGED = 'acknowledged', 'Acknowledged'
        PAID = 'paid', 'Paid'
    
    student = models.ForeignKey('Student', on_delete=models.CASCADE, 
                               related_name='payment_reminders')
    fee_payment = models.ForeignKey('student.FeePayment', on_delete=models.CASCADE,
                                   related_name='reminders', null=True, blank=True)
    
    # Reminder details
    reminder_type = models.CharField(max_length=15, choices=ReminderType.choices)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    
    # Status
    status = models.CharField(max_length=15, choices=ReminderStatus.choices, 
                             default=ReminderStatus.PENDING)
    
    # Communication
    reminder_sent_date = models.DateTimeField(null=True, blank=True)
    reminder_method = models.CharField(max_length=20, choices=[
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('call', 'Phone Call'),
        ('in_app', 'In-App Notification')
    ], default='email')
    
    message_template = models.TextField()
    
    # Follow-up
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['due_date', '-created_at']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.reminder_type} - ₹{self.amount_due}"


class PDCCollection(models.Model):
    """
    Post-Dated Cheque collection and tracking
    """
    class ChequeStatus(models.TextChoices):
        COLLECTED = 'collected', 'Collected'
        DEPOSITED = 'deposited', 'Deposited'
        CLEARED = 'cleared', 'Cleared'
        BOUNCED = 'bounced', 'Bounced'
        CANCELLED = 'cancelled', 'Cancelled'
    
    student = models.ForeignKey('Student', on_delete=models.CASCADE,
                               related_name='pdc_cheques')
    fee_payment = models.OneToOneField('student.FeePayment', on_delete=models.CASCADE,
                                      related_name='pdc_details')
    
    # Cheque details
    cheque_number = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=100)
    branch_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    cheque_date = models.DateField()
    
    # Collection details
    collected_date = models.DateField()
    collected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                    related_name='collected_cheques')
    
    # Status tracking
    status = models.CharField(max_length=15, choices=ChequeStatus.choices, 
                             default=ChequeStatus.COLLECTED)
    deposit_date = models.DateField(null=True, blank=True)
    clearance_date = models.DateField(null=True, blank=True)
    
    # If bounced
    bounce_reason = models.TextField(blank=True)
    bounce_charges = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Scanned copy
    cheque_image = models.FileField(upload_to='pdc_cheques/', null=True, blank=True,storage=MediaCloudinaryStorage())
    
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['cheque_date']
    
    def __str__(self):
        return f"{self.student.full_name} - Cheque {self.cheque_number} - ₹{self.amount}"


class OnboardingChecklist(models.Model):
    """
    Track onboarding completion status for each student
    """
    student = models.OneToOneField('Student', on_delete=models.CASCADE,
                                   related_name='onboarding_checklist')
    
    # Document Collection
    documents_uploaded = models.BooleanField(default=False)
    documents_verified = models.BooleanField(default=False)
    
    # Payment
    booking_fee_paid = models.BooleanField(default=False)
    admission_fee_paid= models.BooleanField(default=False)
    payment_plan_created = models.BooleanField(default=False)
    
    # Enrollment
    enrollment_letter_generated = models.BooleanField(default=False)
    enrollment_letter_signed = models.BooleanField(default=False)
    
    # ID & Access
    id_card_generated = models.BooleanField(default=False)
    id_card_issued = models.BooleanField(default=False)
    lms_access_created = models.BooleanField(default=False)
    
    # PDC (if applicable)
    pdc_collected = models.BooleanField(default=False)
    pdc_count = models.IntegerField(default=0)
    
    # Batch Assignment
    batch_assigned = models.BooleanField(default=False)
    orientation_completed = models.BooleanField(default=False)
    
    # Completion
    onboarding_completed = models.BooleanField(default=False)
    completed_date = models.DateField(null=True, blank=True)
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
     return f"Onboarding progress- {self.student.full_name}"
    
    @property
    def completion_percentage(self):
        """Calculate onboarding completion percentage"""

        total_steps = 12

        # Check if student has any PDC payments
        has_pdc_or_emi = self.student.fee_payments.filter(
            payment_type__in=["installment"]
        ).exists()

        completed_steps = sum([
            self.documents_uploaded,
            self.documents_verified,
            self.booking_fee_paid,
            self.admission_fee_paid,
            self.payment_plan_created,
            self.enrollment_letter_generated,
            self.enrollment_letter_signed,
            self.id_card_generated,
            self.id_card_issued,
            self.lms_access_created,
            self.pdc_collected if has_pdc_or_emi else True,
            self.batch_assigned,
            self.orientation_completed
        ])

        return round((completed_steps / total_steps) * 100, 1)


class StudentIssue(models.Model):
    """
    Track student issues and complaints
    """
    class IssueType(models.TextChoices):
        ACADEMIC = 'academic', 'Academic Issue'
        PAYMENT = 'payment', 'Payment Issue'
        TECHNICAL = 'technical', 'Technical Issue'
        FACILITY = 'facility', 'Facility Issue'
        TRAINER = 'trainer', 'Trainer Related'
        OTHER = 'other', 'Other'
    
    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'
    
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'
    
    student = models.ForeignKey('Student', on_delete=models.CASCADE,
                               related_name='issues')
    
    # Issue details
    issue_type = models.CharField(max_length=15, choices=IssueType.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices, 
                               default=Priority.MEDIUM)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    
    # Assignment
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='assigned_issues')
    
    # Status tracking
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)
    
    # Resolution
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='resolved_issues')
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Satisfaction
    student_satisfied = models.BooleanField(null=True, blank=True)
    satisfaction_comments = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.issue_type} - {self.status}"


class BatchSchedule(models.Model):
    """
    Detailed schedule for each batch
    """
    class DayOfWeek(models.TextChoices):
        MONDAY = 'monday', 'Monday'
        TUESDAY = 'tuesday', 'Tuesday'
        WEDNESDAY = 'wednesday', 'Wednesday'
        THURSDAY = 'thursday', 'Thursday'
        FRIDAY = 'friday', 'Friday'
        SATURDAY = 'saturday', 'Saturday'
        SUNDAY = 'sunday', 'Sunday'
    
    batch = models.ForeignKey('Batch', on_delete=models.CASCADE,
                             related_name='schedules')
    
    # Schedule details
    day_of_week = models.CharField(max_length=10, choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Trainer assignment for this slot
    trainer = models.ForeignKey('Trainer', on_delete=models.SET_NULL, null=True,
                               related_name='scheduled_slots')
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['day_of_week', 'start_time']
        unique_together = ['batch', 'day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.batch.name} - {self.day_of_week} {self.start_time}-{self.end_time}"


class Notification(models.Model):
    """
    In-app notifications for BDM users
    """
    class NotificationType(models.TextChoices):
        LEAD_ASSIGNED = 'lead_assigned', 'New Lead Assigned'
        PAYMENT_REMINDER = 'payment_reminder', 'Payment Reminder'
        PAYMENT_RECEIVED = 'payment_received', 'Payment Received'
        ISSUE_ASSIGNED = 'issue_assigned', 'Issue Assigned'
        FOLLOWUP_DUE = 'followup_due', 'Follow-up Due'
        DOCUMENT_PENDING = 'document_pending', 'Document Pending'
        GENERAL = 'general', 'General Notification'
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='notifications')
    
    # Notification details
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Link to related object (optional)
    link_url = models.CharField(max_length=500, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.recipient.username} - {self.title}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class UserNotificationSettings(models.Model):
    """
    User preferences for notifications
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='notification_settings')
    
    # Email notifications
    email_lead_assignment = models.BooleanField(default=True)
    email_payment_reminders = models.BooleanField(default=True)
    email_payment_received = models.BooleanField(default=True)
    email_issue_assignment = models.BooleanField(default=True)
    email_daily_summary = models.BooleanField(default=False)
    
    # In-app notifications
    inapp_lead_assignment = models.BooleanField(default=True)
    inapp_payment_updates = models.BooleanField(default=True)
    inapp_issue_updates = models.BooleanField(default=True)
    
    # SMS notifications
    sms_important_only = models.BooleanField(default=True)
    sms_payment_received = models.BooleanField(default=False)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification Settings - {self.user.username}"
    

class Announcement(models.Model):

    AUDIENCE_CHOICES = (
        ('students', 'Students'),
        ('trainers', 'Trainers'),
        ('both', 'Both'),
    )

    title = models.CharField(max_length=255)
    message = models.TextField()
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    is_important = models.BooleanField(default=False)
    publish_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title    
    
       


class Admission(models.Model):

    class PaymentPlan(models.TextChoices):
        FULL = "full", "Full Payment"
        INSTALLMENT = "installment", "Installment"
        EMI = "emi", "EMI"
        PDC = "pdc", "Post Dated Cheque"

    class AdmissionStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        ON_HOLD = "on_hold", "On Hold"

    # -------------------------
    # Core Relations
    # -------------------------

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admissions"
    )

    student = models.ForeignKey(
        "Student",
        on_delete=models.CASCADE,
        related_name="admissions"
    )

    course = models.ForeignKey(
        "Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admissions"
    )

    batch = models.ForeignKey(
        "Batch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admissions"
    )

    # -------------------------
    # Optional Details
    # -------------------------

    educational_qualification = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    payment_plan = models.CharField(
        max_length=20,
        choices=PaymentPlan.choices,
        blank=True,
        null=True
    )

    total_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    admission_fee_paid = models.BooleanField(
        default=False
    )

    admission_fee_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    # -------------------------
    # Status & Tracking
    # -------------------------

    status = models.CharField(
        max_length=20,
        choices=AdmissionStatus.choices,
        default=AdmissionStatus.ACTIVE
    )

    admitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admissions_done"
    )

    admission_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.course if self.course else 'No Course'}"    