from django.db import models

# Create your models here.
from django.contrib.auth.models import User



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
    
    # Assignment and Tracking
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
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
    
    # Personal Information
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GenderChoice.choices)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    
    # Professional Details
    qualification = models.CharField(max_length=200)
    coding_languages = models.TextField()  # Python, Java, JavaScript, etc.
    frameworks = models.TextField()  # Django, React, Spring, etc.
    bio = models.TextField(blank=True)
    experience = models.IntegerField()  # Years of experience
    basic_pay = models.DecimalField(max_digits=10, decimal_places=2)
    
    
    
    # System Fields
    is_active = models.BooleanField(default=True)
    date_joined = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.experience} years"
    
    @property
    def languages_list(self):
        return [lang.strip() for lang in self.coding_languages.split(',')]
    
    @property
    def frameworks_list(self):
        return [fw.strip() for fw in self.frameworks.split(',')]    



class Student(models.Model):
    class GenderChoice(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'
    
    class PaymentOption(models.TextChoices):
        EMI = 'emi', 'EMI'
        ADVANCED = 'advanced', 'Advanced Full Payment'
        MONTHLY = 'monthly', 'Monthly Payment'
    
    class CodingExpertise(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        EXPERT = 'expert', 'Expert'
    
    class ModeChoice(models.TextChoices):
        REMOTE = 'remote', 'Remote'
        ONSITE = 'onsite', 'Onsite'
    
    class BatchTime(models.TextChoices):
        MORNING = 'morning', 'Morning'
        EVENING = 'evening', 'Evening'
        FULL_DAY = 'full_day', 'Full Day'
    
    class CourseStatus(models.TextChoices):
        PHASE1 = 'phase1', 'Phase 1'
        PHASE2 = 'phase2', 'Phase 2'
        PHASE3 = 'phase3', 'Phase 3'
        DROPPED = 'dropped', 'Dropped'
        COMPLETED = 'completed', 'Completed'
    
    # Personal Information
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GenderChoice.choices)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    
    # Educational Details
    education = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    coding_expertise = models.CharField(max_length=15, choices=CodingExpertise.choices, 
                                        default=CodingExpertise.BEGINNER)
    
    # Course Details
    selected_course = models.ForeignKey(Course, on_delete=models.PROTECT)
    payment_option = models.CharField(max_length=15, choices=PaymentOption.choices)
    booking_fee_received = models.BooleanField(default=False)
    mode = models.CharField(max_length=10, choices=ModeChoice.choices)
    preferred_batch_time = models.CharField(max_length=10, choices=BatchTime.choices, 
                                           null=True, blank=True)
    
    # Academic Progress
    attendance_percentage = models.FloatField(null=True, blank=True)  # 0-100
    task_score_sum = models.IntegerField(default=0)
    join_date = models.DateField()
    certificate_eligible = models.BooleanField(null=True, blank=True)
    course_completion_status = models.CharField(max_length=10, choices=CourseStatus.choices, 
                                                default=CourseStatus.PHASE1)
 
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-join_date']
    
    def __str__(self):
        return f"{self.name} - {self.selected_course}"
    
    def update_attendance(self, present_days, total_days):
        if total_days > 0:
            self.attendance_percentage = (present_days / total_days) * 100
            self.save()
    
    def add_task_score(self, score):
        self.task_score_sum += score
        self.save()    


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
    
    
   
class TeleCallerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
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