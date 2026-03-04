from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


from cloudinary_storage.storage import MediaCloudinaryStorage
from cloudinary_storage.storage import RawMediaCloudinaryStorage
# Import your existing models


class Module(models.Model):
    """Course broken down into major modules/sections"""
    course = models.ForeignKey('bdm.Course', on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Module organization
    module_number = models.IntegerField()  # 1, 2, 3, etc.
    total_sessions = models.IntegerField()  # Number of sessions allocated
    
    # Phase mapping
    phase = models.CharField(max_length=10, choices=[
        ('phase1', 'Phase 1'),
        ('phase2', 'Phase 2'),
        ('phase3', 'Phase 3')
    ])
    
    learning_objectives = models.TextField()
    prerequisites = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course', 'module_number']
        unique_together = ['course', 'module_number']
    
    def __str__(self):
        return f"Module {self.module_number}: {self.title} ({self.course.name})"


class LessonPlan(models.Model):
    """
    Master lesson plan - Daily topics breakdown for each module
    This is the syllabus structure
    """
    course = models.ForeignKey('bdm.Course', on_delete=models.CASCADE, related_name='lesson_plans', null=True, blank=True)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    
    # Session details
    session_number = models.IntegerField()  # e.g., Session 12, 13, 14
    topic = models.CharField(max_length=300)  # e.g., "Pandas Series & DataFrame"
    description = models.TextField()
    
    # Content details
    subtopics = models.TextField(help_text="Comma-separated or line-separated subtopics")
    learning_outcomes = models.TextField()
    estimated_duration_hours = models.DecimalField(max_digits=3, decimal_places=1, default=2.0)
    
    # Resources
    reference_materials = models.TextField(blank=True,)
    practice_exercises = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True,blank=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True)
    
    class Meta:
        ordering = ['module', 'session_number']
        unique_together = ['module', 'session_number']
    
    def __str__(self):
        return f"Session {self.session_number}: {self.topic}"


class LessonSession(models.Model):
    """
    Daily class tracking - Actual implementation of lesson plan for each batch
    This is where trainers mark attendance and progress
    """
    class SessionStatus(models.TextChoices):
        PLANNED = 'planned', 'Planned'
        COMPLETED = 'completed', 'Completed'
        PENDING = 'pending', 'Pending'
        SKIPPED = 'skipped', 'Skipped'
        DELAYED = 'delayed', 'Delayed'
    
    # Relationships
    batch = models.ForeignKey('bdm.Batch', on_delete=models.CASCADE, related_name='lesson_sessions')
    lesson_plan = models.ForeignKey(LessonPlan, on_delete=models.CASCADE, related_name='sessions')
    trainer = models.ForeignKey('bdm.Trainer', on_delete=models.SET_NULL, null=True, related_name='conducted_sessions')
    
    # Scheduling
    planned_date = models.DateField()
    actual_date = models.DateField(null=True, blank=True)
    
    # Status tracking
    status = models.CharField(max_length=10, choices=SessionStatus.choices, default=SessionStatus.PLANNED)
    
    # Session details
    actual_duration_hours = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    topics_covered = models.TextField(blank=True, help_text="What was actually covered in this session")
    
    # Trainer feedback
    remarks = models.TextField(blank=True, help_text="Any notes, delays, or additional comments")
    homework_assigned = models.TextField(blank=True)
    student_queries = models.TextField(blank=True)
    
    # Additional session info
    extra_practice_given = models.BooleanField(default=False)
    requires_revision = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['batch', 'planned_date', 'lesson_plan__session_number']
        unique_together = ['batch', 'lesson_plan']
    
    def __str__(self):
        return f"{self.batch.name} - Session {self.lesson_plan.session_number} - {self.status}"
    
    def mark_completed(self, trainer, actual_date=None, remarks=''):
        """Mark session as completed"""
        self.status = self.SessionStatus.COMPLETED
        self.trainer = trainer
        self.actual_date = actual_date or timezone.now().date()
        self.completed_at = timezone.now()
        if remarks:
            self.remarks = remarks
        self.save()
    
    def mark_delayed(self, reason=''):
        """Mark session as delayed"""
        self.status = self.SessionStatus.DELAYED
        self.remarks = f"Delayed: {reason}"
        self.save()
    
    @classmethod
    def get_batch_progress(cls, batch):
        """Calculate progress statistics for a batch"""
        total = cls.objects.filter(batch=batch).count()
        if total == 0:
            return {
                'total': 0,
                'completed': 0,
                'pending': 0,
                'delayed': 0,
                'skipped': 0,
                'progress_percentage': 0
            }
        
        completed = cls.objects.filter(batch=batch, status=cls.SessionStatus.COMPLETED).count()
        pending = cls.objects.filter(batch=batch, status=cls.SessionStatus.PENDING).count()
        delayed = cls.objects.filter(batch=batch, status=cls.SessionStatus.DELAYED).count()
        skipped = cls.objects.filter(batch=batch, status=cls.SessionStatus.SKIPPED).count()
        
        return {
            'total': total,
            'completed': completed,
            'pending': pending,
            'delayed': delayed,
            'skipped': skipped,
            'progress_percentage': round((completed / total) * 100, 1)
        }

class SessionMaterial(models.Model):
    """
    Materials uploaded by trainer after each session
    Students can access recordings, notes, code files, etc.
    """
    class MaterialType(models.TextChoices):
        RECORDING = 'recording', 'Class Recording'
        NOTES = 'notes', 'Class Notes'
        SLIDES = 'slides', 'Presentation Slides'
        CODE = 'code', 'Code Files'
        REFERENCE = 'reference', 'Reference Material'
        ASSIGNMENT = 'assignment', 'Assignment/Exercise'
        OTHER = 'other', 'Other'
    
    lesson_session = models.ForeignKey(LessonSession, on_delete=models.CASCADE, 
                                       related_name='materials')
    
    # Material details
    title = models.CharField(max_length=200)
    material_type = models.CharField(max_length=15, choices=MaterialType.choices)
    description = models.TextField(blank=True)
    
    # File or link
    file = models.FileField(upload_to='session_materials/%Y/%m/', null=True, blank=True,
                           help_text="Upload files like PDF, PPTX, ZIP, etc.",storage=RawMediaCloudinaryStorage())
    external_link = models.URLField(blank=True, 
                                   help_text="YouTube, Google Drive, GitHub, etc.")
    
    # Recording specific (if material_type is RECORDING)
    duration_minutes = models.IntegerField(null=True, blank=True, 
                                          help_text="Duration of video/recording")
    video_platform = models.CharField(max_length=50, blank=True,
                                     help_text="YouTube, Vimeo, Google Drive, etc.")
    
    # Accessibility
    is_mandatory = models.BooleanField(default=False, 
                                      help_text="Must students view this?")
    is_public = models.BooleanField(default=False,
                                   help_text="Visible to all or only enrolled students?")
    
    # Tracking
    uploaded_by = models.ForeignKey('bdm.Trainer', on_delete=models.SET_NULL, null=True,
                                   related_name='uploaded_materials')
    upload_date = models.DateTimeField(auto_now_add=True)
    file_size_mb = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Student engagement tracking
    view_count = models.IntegerField(default=0)
    download_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-upload_date']
    
    def __str__(self):
        return f"{self.lesson_session.batch.name} - Session {self.lesson_session.lesson_plan.session_number} - {self.title}"
    
    def increment_views(self):
        """Track when a student views this material"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def increment_downloads(self):
        """Track when a student downloads this material"""
        self.download_count += 1
        self.save(update_fields=['download_count'])
        
class MaterialAccess(models.Model):
    """
    Track which students have accessed which materials
    Helps trainers see engagement
    """
    material = models.ForeignKey(SessionMaterial, on_delete=models.CASCADE,
                                related_name='access_logs')
    student = models.ForeignKey('bdm.Student', on_delete=models.CASCADE,
                               related_name='material_access')
    
    # Access tracking
    first_accessed = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    access_count = models.IntegerField(default=1)
    
    # Actions
    has_viewed = models.BooleanField(default=False)
    has_downloaded = models.BooleanField(default=False)
    watch_time_minutes = models.IntegerField(default=0, 
                                            help_text="For video recordings")
    
    class Meta:
        unique_together = ['material', 'student']
        ordering = ['-last_accessed']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.material.title}"
    
    def mark_viewed(self):
        """Mark material as viewed"""
        if not self.has_viewed:
            self.has_viewed = True
            self.material.increment_views()
        self.access_count += 1
        self.save()
    
    def mark_downloaded(self):
        """Mark material as downloaded"""
        if not self.has_downloaded:
            self.has_downloaded = True
            self.material.increment_downloads()
        self.save()

        

class ExtensionRequest(models.Model):
    """Handle course duration extension requests"""
    batch = models.ForeignKey('bdm.Batch', on_delete=models.CASCADE, related_name='extension_requests')
    requested_by = models.ForeignKey('bdm.Trainer', on_delete=models.SET_NULL, null=True)
    
    # Extension details
    current_end_date = models.DateField()
    requested_end_date = models.DateField()
    extension_days = models.IntegerField()
    
    # Justification with lesson plan context
    reason = models.TextField()
    pending_sessions = models.IntegerField(help_text="Number of sessions still pending")
    delayed_sessions = models.IntegerField(help_text="Number of sessions that got delayed")
    pending_topics = models.TextField(help_text="List of topics/modules still pending")
    additional_notes = models.TextField(blank=True)
    
    # Approval workflow
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='pending')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='approved_extensions')
    approval_date = models.DateTimeField(null=True, blank=True)
    admin_comments = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.batch.name} - Extension Request ({self.status})"


class Attendance(models.Model):
    """Daily attendance tracking for students"""
    student = models.ForeignKey('bdm.Student', on_delete=models.CASCADE, related_name='attendance_records')
    batch = models.ForeignKey('bdm.Batch', on_delete=models.CASCADE, related_name='attendance_records')
    lesson_session = models.ForeignKey(LessonSession, on_delete=models.CASCADE, 
                                      related_name='attendance_records', null=True, blank=True)
    date = models.DateField(default=timezone.now)
    
    # Attendance status
    status = models.CharField(max_length=10, choices=[
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused')
    ])
    
    # Additional info
    marked_by = models.ForeignKey('bdm.Trainer', on_delete=models.SET_NULL, null=True)
    remarks = models.TextField(blank=True)
    marked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['student', 'batch', 'date']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.date} - {self.status}"
    
    @classmethod
    def calculate_attendance_percentage(cls, student, batch):
        """Calculate attendance percentage for a student in a batch"""
        total_days = cls.objects.filter(student=student, batch=batch).count()
        if total_days == 0:
            return 0
        present_days = cls.objects.filter(
            student=student, 
            batch=batch, 
            status__in=['present', 'late']
        ).count()
        return round((present_days / total_days) * 100, 2)


class Exam(models.Model):
    """Exam configuration and scheduling"""
    class ExamType(models.TextChoices):
        QUIZ = 'quiz', 'Quiz'
        MIDTERM = 'midterm', 'Mid-term'
        FINAL = 'final', 'Final Exam'
        PRACTICAL = 'practical', 'Practical Exam'
    
    batch = models.ForeignKey('bdm.Batch', on_delete=models.CASCADE, related_name='exams')
    exam_type = models.CharField(max_length=20, choices=ExamType.choices)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Scheduling
    scheduled_date = models.DateField()
    exam_time = models.TimeField(null=True, blank=True) 
    duration_minutes = models.IntegerField()
    total_marks = models.IntegerField()
    passing_marks = models.IntegerField()
    
    questions_file = models.FileField(upload_to='exam_docs/%Y/%m/', null=True, blank=True,
                           help_text="Upload files like PDF, PPTX, ZIP, etc.",storage=RawMediaCloudinaryStorage())
    
    # Prerequisites
    minimum_attendance_required = models.IntegerField(
        default=75,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum attendance % required to appear for exam"
    )
    fees_paid_required = models.BooleanField(default=False)
    
    
  
    
    # Exam details
    syllabus_modules = models.ManyToManyField(Module, related_name='exams', blank=True)
    instructions = models.TextField(blank=True)
    
    # Status
    is_published = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    created_by = models.ForeignKey('bdm.Trainer', on_delete=models.SET_NULL, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"{self.batch.name} - {self.exam_type} - {self.title}"



class ExamSubmission(models.Model):

    class SubmissionStatus(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        LATE = "late", "Late Submission"
        EVALUATED = "evaluated", "Evaluated"
        REJECTED = "rejected", "Rejected"

    exam = models.ForeignKey(
        "Exam",
        on_delete=models.CASCADE,
        related_name="submissions"
    )

    student = models.ForeignKey(
        "bdm.Student",
        on_delete=models.CASCADE,
        related_name="exam_submissions"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exam_submissions"
    )

    # -----------------------------
    # File Upload
    # -----------------------------

    answer_file = models.FileField(
       upload_to='ans_file/%Y/%m/', null=True, blank=True,
                           help_text="Upload files like PDF, PPTX, ZIP, etc.",storage=RawMediaCloudinaryStorage()
    )

    # -----------------------------
    # Tracking
    # -----------------------------

    submitted_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.SUBMITTED
    )

    # -----------------------------
    # Evaluation
    # -----------------------------

    marks_obtained = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )

    evaluated_by = models.ForeignKey(
        "bdm.Trainer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evaluated_submissions"
    )

    evaluated_at = models.DateTimeField(null=True, blank=True)

    feedback = models.TextField(blank=True)

    # -----------------------------

    class Meta:
        unique_together = ('exam', 'student')  # One submission per exam
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.user.username} - {self.exam.title}"





class ExamResult(models.Model):
    """Store individual student exam results"""
    class GradeChoice(models.TextChoices):
        A_PLUS = 'A+', 'A+ (90-100)'
        A = 'A', 'A (80-89)'
        B_PLUS = 'B+', 'B+ (70-79)'
        B = 'B', 'B (60-69)'
        C = 'C', 'C (50-59)'
        D = 'D', 'D (40-49)'
        F = 'F', 'F (Below 40)'
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey('bdm.Student', on_delete=models.CASCADE, related_name='exam_results')
    
    # Eligibility check
    is_eligible = models.BooleanField(default=True)
    ineligibility_reason = models.TextField(blank=True)
    
    # Marks and grading
    marks_obtained = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    grade = models.CharField(max_length=2, choices=GradeChoice.choices, null=True, blank=True)
    is_pass = models.BooleanField(null=True, blank=True)
    
    # Additional info
    evaluator = models.ForeignKey('bdm.Trainer', on_delete=models.SET_NULL, null=True, 
                                 related_name='evaluated_exams')
    remarks = models.TextField(blank=True)
    uploaded_to_erp = models.BooleanField(default=False)
    erp_upload_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['exam', 'student']
        ordering = ['-marks_obtained']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.exam.title} - {self.marks_obtained or 'Not Evaluated'}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate grade and pass/fail
        if self.marks_obtained is not None:
            percentage = (self.marks_obtained / self.exam.total_marks) * 100
            
            if percentage >= 90:
                self.grade = self.GradeChoice.A_PLUS
            elif percentage >= 80:
                self.grade = self.GradeChoice.A
            elif percentage >= 70:
                self.grade = self.GradeChoice.B_PLUS
            elif percentage >= 60:
                self.grade = self.GradeChoice.B
            elif percentage >= 50:
                self.grade = self.GradeChoice.C
            elif percentage >= 40:
                self.grade = self.GradeChoice.D
            else:
                self.grade = self.GradeChoice.F
            
            self.is_pass = self.marks_obtained >= self.exam.passing_marks
        
        super().save(*args, **kwargs)
    
    def check_eligibility(self):
        """Check if student meets exam prerequisites"""
        reasons = []
        
        # Check attendance
        attendance_pct = Attendance.calculate_attendance_percentage(
            self.student, 
            self.exam.batch
        )
        if attendance_pct < self.exam.minimum_attendance_required:
            reasons.append(f"Attendance {attendance_pct}% < Required {self.exam.minimum_attendance_required}%")
        
        # Check fees
        if self.exam.fees_paid_required and not self.student.booking_fee_received:
            reasons.append("Booking fee not received")
        
        # Check phase completion
        if self.exam.phase_required:
            phase_order = {'phase1': 1, 'phase2': 2, 'phase3': 3}
            student_phase = phase_order.get(self.student.course_completion_status, 0)
            required_phase = phase_order.get(self.exam.phase_required, 0)
            
            if student_phase < required_phase:
                reasons.append(f"Student in {self.student.course_completion_status}, exam requires {self.exam.phase_required}")
        
        self.is_eligible = len(reasons) == 0
        self.ineligibility_reason = "; ".join(reasons)
        self.save()
        
        return self.is_eligible


class Certificate(models.Model):
    """Certificate issuance and tracking"""
    class CertificateType(models.TextChoices):
        COMPLETION = 'completion', 'Course Completion'
        EXCELLENCE = 'excellence', 'Certificate of Excellence'
        PARTICIPATION = 'participation', 'Certificate of Participation'
    
    student = models.ForeignKey('bdm.Student', on_delete=models.CASCADE, related_name='certificates')
    batch = models.ForeignKey('bdm.Batch', on_delete=models.CASCADE, related_name='certificates')
    certificate_type = models.CharField(max_length=20, choices=CertificateType.choices)
    
    # Certificate details
    certificate_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField()
    
    # Eligibility criteria
    is_eligible = models.BooleanField(default=False)
    eligibility_checked_at = models.DateTimeField(null=True, blank=True)
    ineligibility_reasons = models.TextField(blank=True)
    
    # Criteria values (snapshot at time of certificate generation)
    final_attendance = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    final_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_marks_scored = models.IntegerField(null=True, blank=True)
    sessions_completed = models.IntegerField(null=True, blank=True)
    
    # Issuance
    issued_by = models.ForeignKey('bdm.Trainer', on_delete=models.SET_NULL, null=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='approved_certificates')
    certificate_file = models.FileField(upload_to='certificates/', null=True, blank=True,storage=RawMediaCloudinaryStorage())
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"{self.certificate_number} - {self.student.full_name}"
    
    def check_eligibility(self, minimum_attendance=75, minimum_percentage=50):
        """
        Check if student meets certification criteria
        - All fees paid
        - Minimum attendance met
        - Course completed (all sessions completed)
        - Minimum academic percentage achieved
        """
        reasons = []
        
        # Check fees
        if not self.student.booking_fee_received:
            reasons.append("Booking fee not received")
        
        # Check attendance
        attendance = Attendance.calculate_attendance_percentage(self.student, self.batch)
        if attendance < minimum_attendance:
            reasons.append(f"Attendance {attendance}% < Required {minimum_attendance}%")
        else:
            self.final_attendance = attendance
        
        # Check course completion (all sessions completed)
        progress = LessonSession.get_batch_progress(self.batch)
        if progress['progress_percentage'] < 100:
            reasons.append(f"Course not fully completed ({progress['progress_percentage']}% completed)")
        else:
            self.sessions_completed = progress['completed']
        
        # Check student course status
        if self.student.course_completion_status != 'completed':
            reasons.append(f"Student status: {self.student.course_completion_status}")
        
        # Check academic percentage
        exam_results = ExamResult.objects.filter(student=self.student, exam__batch=self.batch)
        if exam_results.exists():
            total_marks = sum(r.exam.total_marks for r in exam_results)
            obtained_marks = sum(r.marks_obtained or 0 for r in exam_results)
            percentage = (obtained_marks / total_marks * 100) if total_marks > 0 else 0
            
            if percentage < minimum_percentage:
                reasons.append(f"Academic percentage {percentage:.2f}% < Required {minimum_percentage}%")
            else:
                self.final_percentage = percentage
                self.total_marks_scored = obtained_marks
        else:
            reasons.append("No exam results found")
        
        self.is_eligible = len(reasons) == 0
        self.ineligibility_reasons = "; ".join(reasons)
        self.eligibility_checked_at = timezone.now()
        self.save()
        
        return self.is_eligible


class Task(models.Model):
    """
    Tasks assigned by trainers for specific lesson sessions
    Students see these in their portal
    """
    class TaskType(models.TextChoices):
        HOMEWORK = 'homework', 'Homework'
        ASSIGNMENT = 'assignment', 'Assignment'
        PROJECT = 'project', 'Project'
        PRACTICE = 'practice', 'Practice Exercise'
        QUIZ = 'quiz', 'Quiz'
    
    class DifficultyLevel(models.TextChoices):
        EASY = 'easy', 'Easy'
        MEDIUM = 'medium', 'Medium'
        HARD = 'hard', 'Hard'
    
    # Task belongs to a lesson session
    lesson_session = models.ForeignKey(LessonSession, on_delete=models.CASCADE, 
                                       related_name='tasks')
    batch = models.ForeignKey('bdm.Batch', on_delete=models.CASCADE, related_name='tasks')
    
    # Task details
    title = models.CharField(max_length=200)
    task_type = models.CharField(max_length=15, choices=TaskType.choices)
    description = models.TextField()
    difficulty_level = models.CharField(max_length=10, choices=DifficultyLevel.choices, 
                                       default=DifficultyLevel.MEDIUM)
    
    # Instructions and resources
    instructions = models.TextField()
    reference_links = models.TextField(blank=True, help_text="URLs or resource links")
    attachment = models.FileField(upload_to='task_attachments/', null=True, blank=True,storage=RawMediaCloudinaryStorage())
    
    # Scoring
    total_marks = models.IntegerField(default=10)
    passing_marks = models.IntegerField(default=5)
    
    # Deadlines
    assigned_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    is_mandatory = models.BooleanField(default=True)
    
    # Creator
    created_by = models.ForeignKey('bdm.Trainer', on_delete=models.SET_NULL, null=True,
                                  related_name='created_tasks')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['due_date', '-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.lesson_session.lesson_plan.topic}"
    
    @property
    def is_overdue(self):
        """Check if task is past due date"""
        return timezone.now().date() > self.due_date
    
    def get_completion_stats(self):
        """Get completion statistics for this task"""
        total_students = self.batch.students.count()
        submissions = self.submissions.filter(is_submitted=True).count()
        pending = total_students - submissions
        
        return {
            'total_students': total_students,
            'submitted': submissions,
            'pending': pending,
            'completion_rate': round((submissions / total_students * 100), 1) if total_students > 0 else 0
        }


class TaskSubmission(models.Model):
    """
    Student submissions for tasks
    Students can see their submission status and feedback
    """
    class SubmissionStatus(models.TextChoices):
        NOT_STARTED = 'not_started', 'Not Started'
        IN_PROGRESS = 'in_progress', 'In Progress'
        SUBMITTED = 'submitted', 'Submitted'
        EVALUATED = 'evaluated', 'Evaluated'
        RESUBMIT = 'resubmit', 'Resubmit Required'
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey('bdm.Student', on_delete=models.CASCADE, related_name='task_submissions')
    
    # Submission details
    status = models.CharField(max_length=15, choices=SubmissionStatus.choices, 
                             default=SubmissionStatus.NOT_STARTED)
    submission_text = models.TextField(blank=True)
    submission_file = models.FileField(upload_to='task_submissions/', null=True, blank=True,storage=RawMediaCloudinaryStorage())
    submission_link = models.URLField(blank=True, help_text="GitHub, CodePen, etc.")
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    is_submitted = models.BooleanField(default=False)
    is_late = models.BooleanField(default=False)
    
    # Evaluation
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_pass = models.BooleanField(null=True, blank=True)
    
    # Feedback
    evaluator = models.ForeignKey('bdm.Trainer', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='evaluated_tasks')
    feedback = models.TextField(blank=True)
    evaluated_at = models.DateTimeField(null=True, blank=True)
    
    # Revision
    revision_count = models.IntegerField(default=0)
    needs_revision = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['task', 'student']
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.task.title} - {self.status}"
    
    def submit(self):
        """Mark task as submitted"""
        self.is_submitted = True
        self.submitted_at = timezone.now()
        self.status = self.SubmissionStatus.SUBMITTED
        
        # Check if submission is late
        if timezone.now().date() > self.task.due_date:
            self.is_late = True
        
        self.save()
    
    def start_task(self):
        """Mark task as in progress"""
        if self.status == self.SubmissionStatus.NOT_STARTED:
            self.status = self.SubmissionStatus.IN_PROGRESS
            self.started_at = timezone.now()
            self.save()
    
    def evaluate(self, marks, feedback, evaluator):
        """Evaluate the submission"""
        self.marks_obtained = marks
        self.is_pass = marks >= self.task.passing_marks
        self.feedback = feedback
        self.evaluator = evaluator
        self.evaluated_at = timezone.now()
        self.status = self.SubmissionStatus.EVALUATED
        
        # Update student's total task score
        if self.is_pass:
            self.student.add_task_score(marks)
        
        self.save()
    
    def request_resubmission(self, feedback):
        """Trainer requests student to resubmit"""
        self.status = self.SubmissionStatus.RESUBMIT
        self.needs_revision = True
        self.feedback = feedback
        self.revision_count += 1
        self.save()
    
    @classmethod
    def get_student_pending_tasks(cls, student):
        """Get all pending tasks for a student"""
        return cls.objects.filter(
            student=student,
            status__in=[cls.SubmissionStatus.NOT_STARTED, cls.SubmissionStatus.IN_PROGRESS],
            task__due_date__gte=timezone.now().date()
        ).select_related('task', 'task__lesson_session', 'task__lesson_session__lesson_plan')
    
    @classmethod
    def get_student_overdue_tasks(cls, student):
        """Get all overdue tasks for a student"""
        return cls.objects.filter(
            student=student,
            is_submitted=False,
            task__due_date__lt=timezone.now().date()
        ).select_related('task', 'task__lesson_session', 'task__lesson_session__lesson_plan')


class SubstituteTeaching(models.Model):
    """Track substitute teaching assignments"""
    batch = models.ForeignKey('bdm.Batch', on_delete=models.CASCADE, related_name='substitute_sessions')
    lesson_session = models.ForeignKey(LessonSession, on_delete=models.CASCADE, 
                                      related_name='substitute_records')
    original_trainer = models.ForeignKey('bdm.Trainer', on_delete=models.CASCADE, 
                                        related_name='missed_sessions')
    substitute_trainer = models.ForeignKey('bdm.Trainer', on_delete=models.CASCADE,
                                          related_name='substitute_sessions')
    
    date = models.DateField()
    reason_for_substitution = models.TextField()
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.batch.name} - {self.date} - {self.substitute_trainer.name} for {self.original_trainer.name}"
    
    
from django.db import models
from django.utils.timezone import now




class TrainerLeave(models.Model):

    class LeaveType(models.TextChoices):
        SICK = "sick", "Sick Leave"
        CASUAL = "casual", "Casual Leave"
        EMERGENCY = "emergency", "Emergency Leave"
        VACATION = "vacation", "Vacation"

    class LeaveStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    # ----------------------------
    # Relationships
    # ----------------------------

    trainer = models.ForeignKey(
        "bdm.Trainer",
        on_delete=models.CASCADE,
        related_name="leave_applications"
    )


    # ----------------------------
    # Leave Details
    # ----------------------------

    leave_type = models.CharField(
        max_length=20,
        choices=LeaveType.choices
    )

    start_date = models.DateField()
    end_date = models.DateField()

    total_days = models.PositiveIntegerField(blank=True, null=True)

    reason = models.TextField()

    attachment = models.FileField(
        upload_to='trainer_leave_docs/%Y/%m/', null=True, blank=True,
                           help_text="Upload files like PDF, PPTX, ZIP, etc.",storage=RawMediaCloudinaryStorage()
    )

    # ----------------------------
    # Status
    # ----------------------------

    status = models.CharField(
        max_length=20,
        choices=LeaveStatus.choices,
        default=LeaveStatus.PENDING
    )

    applied_at = models.DateTimeField(auto_now_add=True)
    decision_at = models.DateTimeField(null=True, blank=True)

    bdm_remarks = models.TextField(blank=True)

    # ----------------------------

    class Meta:
        ordering = ['-applied_at']

    def save(self, *args, **kwargs):
        if self.start_date and self.end_date:
            self.total_days = (self.end_date - self.start_date).days + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.trainer.user.username} - {self.status}"    