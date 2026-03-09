from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Max
from decimal import Decimal
import datetime
from zoneinfo import ZoneInfo
from datetime import date

from apps.trainer.forms import TrainerProfileForm, TaskForm, EvaluationForm , CompletedSessionForm, SessionMaterialForm,TrainerIssueResolveForm,AnnouncementForm,ExamForm,TrainerLeaveForm

from apps.bdm.models import Trainer, Batch, Student, StudentIssue, Announcement, Notification
from apps.trainer.models import Module, Attendance, LessonSession, Task, TaskSubmission, SessionMaterial,TrainerLeave, Exam, ExamSubmission, ExamResult, SubstituteTeaching
from apps.student.models import StudentFeedback, LeaveApplication

from django.contrib.auth import get_user_model
User = get_user_model()




# dashboard
def dashboard(request):
    """Dashboard view"""
    
    trainer = request.user.trainer
    
    
    #upcoming planned sections
    # Get last 4 planned sessions for this trainer
    planned_sessions = (
        LessonSession.objects
        .filter(
            trainer=trainer,
            status=LessonSession.SessionStatus.PLANNED
        )
        .select_related("batch", "lesson_plan")
        .order_by("-planned_date")[:4]
    )
    
    # Newly assigned batches - e.g.,
    newly_assigned_batches = (
        Batch.objects
        .filter(trainers=trainer, is_active=True)
        .order_by('-start_date')[:4]  # latest 4 batches
    )
    
    
    # attendance summary
    # All completed sessions by this trainer
    completed_sessions = LessonSession.objects.filter(
        trainer=trainer,
        status=LessonSession.SessionStatus.COMPLETED
    )

    classes_conducted = completed_sessions.count()

    # Sessions where attendance is already marked
    marked_session_ids = Attendance.objects.filter(
        lesson_session__trainer=trainer
    ).values_list("lesson_session_id", flat=True).distinct()

    # Sessions where attendance is NOT marked
    pending_sessions = completed_sessions.exclude(
        id__in=marked_session_ids
    ).order_by("actual_date")

    pending_attendance = pending_sessions.count()

    # First pending session (for redirect button)
    first_pending_session = pending_sessions.first()

    # Last attendance update date
    last_updated = Attendance.objects.filter(
        lesson_session__trainer=trainer
    ).aggregate(last=Max("date"))["last"]
    
    completed_attendance = classes_conducted - pending_attendance
    
    # todays schedule
    today = timezone.now().date()
    today_sessions = (
    LessonSession.objects
    .filter(
        trainer=trainer,
        planned_date=today  # or actual_date if you use that
    )
    .select_related("batch", "lesson_plan")
    .order_by("planned_date")[:4]
    )
    
    # batch progress 
    
    active_batches = Batch.objects.filter(
    trainers=trainer,
    is_active=True
)

    active_batches_count = active_batches.count()

    total_students = Student.objects.filter(
        batches__in=active_batches
    ).distinct().count()
    total_sessions_count = LessonSession.objects.filter(
        trainer=trainer
    ).count()

    completed_sessions_count = LessonSession.objects.filter(
        trainer=trainer,
        status=LessonSession.SessionStatus.COMPLETED
    ).count()

    if total_sessions_count > 0:
        progress_percentage = round((completed_sessions_count / total_sessions_count) * 100)
    else:
        progress_percentage = 0
        
    # Class Uploads
    # Completed sessions (queryset)
    completed_sessions_qs = LessonSession.objects.filter(
        trainer=trainer,
        status=LessonSession.SessionStatus.COMPLETED
    )

    # Sessions that have at least one material uploaded
    uploaded_session_ids = SessionMaterial.objects.filter(
        lesson_session__trainer=trainer
    ).values_list("lesson_session_id", flat=True).distinct()

    uploaded_sessions_count = completed_sessions_qs.filter(
        id__in=uploaded_session_ids
    ).count()

    # Completed but no material uploaded
    pending_uploads_count = completed_sessions_qs.exclude(
        id__in=uploaded_session_ids
    ).count()
    
    pending_upload_sessions = completed_sessions_qs.exclude(
    id__in=uploaded_session_ids
    ).order_by('-completed_at')

    last_pending_upload_session = pending_upload_sessions.first()
        
    #notification
    # attendance
    # completed_sessions,marked_session_ids
    
    attendance_pending_count = completed_sessions.exclude(
        id__in=marked_session_ids
    ).count()
    # upload materials
    uploaded_session_ids = SessionMaterial.objects.filter(
    lesson_session__trainer=trainer
    ).values_list("lesson_session_id", flat=True)

    material_pending_count = completed_sessions.exclude(
        id__in=uploaded_session_ids
    ).count()
    
    # student evaluation task
    
    pending_evaluations_count = TaskSubmission.objects.filter(
        task__lesson_session__trainer=trainer,
        status=TaskSubmission.SubmissionStatus.SUBMITTED
    ).count()
            
    
    # announcements
    announcement_notifications = Announcement.objects.filter(
    created_by__is_staff=True,
    audience__in=['trainers', 'both']
    ).order_by('-publish_date')[:4]

    announcement_count = announcement_notifications.count()
    
    notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).order_by('-created_at')
    
    context = {
        'page_title': 'Dashboard',
        "planned_sessions": planned_sessions,
        "newly_assigned_batches": newly_assigned_batches,
        
        "classes_conducted": classes_conducted,
        "pending_attendance": pending_attendance,
        "last_updated": last_updated,
        "first_pending_session": first_pending_session,
        "completed_attendance": completed_attendance,
        
        "today_sessions": today_sessions,
        
        "active_batches_count": active_batches_count,
        "total_students": total_students,
        "progress_percentage": progress_percentage,
        
        
        "attendance_pending_count": attendance_pending_count,
        "material_pending_count": material_pending_count,
        "pending_evaluations_count": pending_evaluations_count,
        
        "uploaded_sessions_count": uploaded_sessions_count,
        "pending_uploads_count": pending_uploads_count,
        "last_pending_upload_session": last_pending_upload_session,
        
        "announcement_notifications": announcement_notifications,
        "announcement_count": announcement_count,
        
        'notifications': notifications,
        'unread_count': notifications.count(),
    }
    return render(request, 'trainer/dashboard/overview.html', context)


# my profile 
@login_required
def profile_view(request):
    """Profile view"""
    # Get trainer instance for logged-in user
    trainer = get_object_or_404(Trainer, user=request.user)
    return render(request, "trainer/myprofile/profile_view.html", {"trainer": trainer})


@login_required
def profile_edit(request):
    """Profile edit"""
    trainer = get_object_or_404(Trainer, user=request.user)

    if request.method == "POST":
        form = TrainerProfileForm(request.POST, request.FILES, instance=trainer)
        if form.is_valid():
            if form.has_changed():   
                form.save()
                messages.success(request, "Profile updated successfully")

            return redirect("trainer:profile")

    else:
        # If full_name is blank set initial from user object like first name + lastname
        initial_data = {}
        if not trainer.full_name:
            initial_data['full_name'] = request.user.get_full_name()

        form = TrainerProfileForm(instance=trainer, initial=initial_data)

    return render(request, "trainer/myprofile/profile_edit.html", {"form": form, "trainer": trainer})


# my batches 
@login_required
def my_batches(request):
    """
    Display all active batches assigned to the logged-in trainer
    """

    trainer = Trainer.objects.select_related("user").get(user=request.user)

    batches = (
        Batch.objects
        .filter(trainers=trainer, is_active=True)
        .select_related("course")
        .prefetch_related("students","lesson_sessions")
        .order_by("-start_date")
    )

    today = timezone.now().date()
    batch_list = []

    for batch in batches:
        
        progress_data = LessonSession.get_batch_progress(batch)
        

        progress = 0
        if progress_data["progress_percentage"] >= 100:
            status = "Completed"
        elif progress_data["completed"] == 0:
            status = "Upcoming"
        else:
            status = "Ongoing"

        batch_list.append({
            "id": batch.id,
            "name": batch.name,
            "course": batch.course.name,
            "start_date": batch.start_date,
            "end_date": batch.expected_finish_date,
            "duration": f"{batch.duration_months} Months",
            "classes_completed": progress_data["completed"],
            "progress": progress_data["progress_percentage"],
            "total_students": batch.students.count(),
            "status": status,
        })

    context = {
        "batches": batch_list
    }

    return render(request, "trainer/mybatches/batchlist.html", context)


@login_required
def batch_overview_view(request, batch_id):
    """Batch overview with Summary"""
    trainer = Trainer.objects.get(user=request.user)

    batch = (
        Batch.objects
        .select_related("course")
        .prefetch_related("students")
        .get(id=batch_id, trainers=trainer)
    )

    # Progress calculation based on LessonSession
    progress_data = LessonSession.get_batch_progress(batch)

    progress = progress_data["progress_percentage"]
    classes_completed = progress_data["completed"]
    total_classes = progress_data["total"]

    # Student stats
    total_students = batch.students.count()
    active_students = batch.students.filter(user__is_active=True).count()
    inactive_students = batch.students.filter(user__is_active=False).count()
    
    # Batch schedules
    schedules = batch.schedules.filter(is_active=True)

    context = {
        "batch": batch,
        "progress": progress,
        "classes_completed": classes_completed,
        "total_classes": total_classes,
        "total_students": total_students,
        "active_students": active_students,
        "inactive_students": inactive_students,
        "schedules": schedules,
        "active_tab": "overview",
    }

    return render(request,"trainer/mybatches/overview.html",context)

@login_required
def batch_students_view(request, batch_id):
    """Batch students list"""
    batch = get_object_or_404(
        Batch.objects.prefetch_related("students__user"),
        id=batch_id
    )
    students = batch.students.all()
    
    context={
        "batch": batch,
        "students": students,
        "active_tab": "students",
    }

    return render(request, "trainer/mybatches/students.html", context)

@login_required
def student_details_view(request, batch_id, student_id):
    """Batch each student details"""
    batch = get_object_or_404(Batch, id=batch_id)
    student = get_object_or_404(Student, id=student_id, batches=batch)

    context = {
        "batch": batch,
        "student": student,
        "active_tab": "students",
    }
    return render(request, "trainer/mybatches/student_details.html", context)


# lesson plan 
@login_required
def batch_lesson_plan(request, batch_id):
    """Batch lesson plan"""
    batch = get_object_or_404(
        Batch.objects.select_related("course"),
        id=batch_id
    )
    modules = (
        Module.objects
        .filter(course=batch.course)
        .prefetch_related('lessons')
        .order_by('module_number')
    )
    context = {
    'batch': batch,
    'modules': modules,
    'active_tab': 'lesson_plan',
    }
    
    return render(request, 'trainer/mybatches/lesson_plan.html', context)

@login_required
def batch_feedback_view(request, batch_id):
    trainer = request.user.trainer

    # Secure batch access
    batch = get_object_or_404(
        Batch.objects.filter(trainers=trainer),
        id=batch_id
    )

    feedbacks = StudentFeedback.objects.filter(
        batch=batch,
        trainer=trainer,
        feedback_type__in=[
            StudentFeedback.FeedbackType.TRAINER,
            StudentFeedback.FeedbackType.BATCH,
            StudentFeedback.FeedbackType.COURSE,
        ]
    ).select_related(
        "student", "course", "batch"
    ).order_by("-created_at")

    return render(request,"trainer/mybatches/feedback.html",{"batch": batch,"feedbacks": feedbacks,})


# attendance
@login_required
def attendance_batch_list(request):
    # Get the logged-in trainer
    trainer = request.user.trainer  # adjust if your User model is linked differently

    # Fetch only batches assigned to this trainer
    batches = Batch.objects.filter(trainers=trainer)
    batch_data = []

    for batch in batches:
        total_sessions = batch.lesson_sessions.count()
        classes_completed = batch.lesson_sessions.filter(status='completed').count()

        # Sessions where attendance is fully marked
        completed_attendance = Attendance.objects.filter(
            batch=batch,
            lesson_session__status='completed'
        ).values('lesson_session').distinct().count()

        pending_attendance = classes_completed - completed_attendance

        # Next upcoming session
        next_session = batch.lesson_sessions.filter(
            status='planned'
        ).order_by('planned_date').first()

        batch_data.append({
            'id': batch.id,
            'name': batch.name,
            'status': 'ongoing',  # Or compute based on start/end
            'total_students': batch.students.count(),
            'total_sessions': total_sessions,
            'classes_completed': classes_completed,
            'completed_attendance': completed_attendance,
            'pending_attendance': pending_attendance,
            'next_session': next_session.planned_date if next_session else None,
        })

    return render(request, "trainer/attendance/batch_list.html", {
        "batches": batch_data
    })


@login_required  
def attendance_session_list(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)

    sessions = LessonSession.objects.filter(
        batch=batch,
        status=LessonSession.SessionStatus.COMPLETED
    ).select_related("lesson_plan").order_by("-completed_at")
    # ).select_related("lesson_plan").order_by("-lesson_plan__session_number","-planned_date")
    
     # Attach attendance status manually
    for session in sessions:
        session.attendance_marked = Attendance.objects.filter(
            lesson_session=session
        ).exists()

    return render(request, "trainer/attendance/session_list.html", {
        "batch": batch,
        "sessions": sessions
    })
    
@login_required
def attendance_mark(request, session_id):
    session = get_object_or_404(LessonSession, id=session_id)
    batch = session.batch
    students = batch.students.all().order_by("full_name")

    # Only allow marking if session is completed
    if session.status != LessonSession.SessionStatus.COMPLETED:
        messages.error(request, "Attendance can only be marked for completed sessions.")
        return redirect("trainer:attendance-sessions", batch_id=batch.id)

    # When form is submitted
    if request.method == "POST":
        for student in students:
            status = request.POST.get(f"status_{student.id}", "absent")

            Attendance.objects.update_or_create(
                student=student,
                batch=batch,
                date=session.actual_date,
                defaults={
                    "lesson_session": session,
                    "status": status,
                    "marked_by": session.trainer,
                    "remarks": ""
                }
            )

        messages.success(request, "Attendance saved successfully.")
        return redirect("trainer:attendance-sessions", batch_id=batch.id)

    # Prefill existing attendance
    existing_attendance = dict(
        Attendance.objects.filter(
            batch=batch,
            date=session.actual_date
        ).values_list("student_id", "status")
    )

    # Attach status to each student
    for student in students:
        student.current_status = existing_attendance.get(student.id, "absent")

    return render(request, "trainer/attendance/mark_attendance.html", {
        "session": session,
        "students": students,
    })

@login_required
def attendance_view(request, session_id):
    session = get_object_or_404(LessonSession, id=session_id)
    batch = session.batch

    attendance_records = Attendance.objects.filter(
        batch=batch,
        date=session.actual_date
    ).select_related("student")

    total_students = batch.students.count()
    present_count = attendance_records.filter(status="present").count()
    late_count = attendance_records.filter(status="late").count()
    absent_count = attendance_records.filter(status="absent").count()

    return render(request, "trainer/attendance/view_attendance.html", {
        "session": session,
        "attendance_records": attendance_records,
        "total_students": total_students,
        "present_count": present_count,
        "absent_count": absent_count,
        "late_count": late_count,
    })

# leave

@login_required
def leave_dashboard(request):
    trainer = request.user.trainer

    leave_applications = LeaveApplication.objects.filter(
        batch__trainers=trainer
    ).select_related("student", "batch", "approved_by").distinct()

    # Precompute counts
    pending_count = leave_applications.filter(status='pending').count()
    approved_count = leave_applications.filter(status='approved').count()
    rejected_count = leave_applications.filter(status='rejected').count()

    return render(request, "trainer/leave/leave_dashboard.html", {
        "leave_applications": leave_applications,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
    })


@login_required
def leave_detail(request, leave_id):
    """
    Trainer can view a single leave application in detail
    """
    leave = get_object_or_404(LeaveApplication, id=leave_id)
    trainer = request.user.trainer

    if not leave.batch.trainers.filter(id=trainer.id).exists():
        messages.error(request, "You are not authorized to view this leave.")
        return redirect("trainer:leave-dashboard")

    return render(request, "trainer/leave/leave_detail.html", {"leave": leave})


@login_required
def process_leave(request, leave_id):
    """
    Approve or Reject leave applications
    """
    leave = get_object_or_404(LeaveApplication, id=leave_id)
    trainer = request.user.trainer

    if not leave.batch.trainers.filter(id=trainer.id).exists():
        messages.error(request, "You are not authorized to process this leave.")
        return redirect("trainer:leave-dashboard")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "approve":
            leave.status = LeaveApplication.LeaveStatus.APPROVED
            leave.approved_by = trainer
            leave.approval_date = timezone.now()
            leave.save()
            
            # Notify student
            Notification.objects.create(
                recipient=leave.student.user,
                notification_type=Notification.NotificationType.GENERAL,
                title="Leave Approved ✓",
                message=f"Your leave from {leave.from_date} to {leave.to_date} has been approved.",
                link_url=f"/student/leaves/{leave.id}/",
            )
            messages.success(request, f"Leave approved for {leave.student.full_name}")

        elif action == "reject":
            reason = request.POST.get("rejection_reason", "").strip()
            if not reason:
                messages.error(request, "Rejection reason is required.")
                return redirect("trainer:leave-dashboard")

            leave.status = LeaveApplication.LeaveStatus.REJECTED
            leave.rejection_reason = reason
            leave.approved_by = trainer
            leave.approval_date = timezone.now()
            leave.save()
            
            # Notify student
            Notification.objects.create(
                recipient=leave.student.user,
                notification_type=Notification.NotificationType.GENERAL,
                title="Leave Rejected",
                message=f"Your leave from {leave.start_date} to {leave.end_date} was rejected. Reason: {leave.rejection_reason}",
                link_url=f"/student/leaves/{leave.id}/",
            )
            
            messages.success(request, f"Leave rejected for {leave.student.full_name}")

    return redirect("trainer:leave-dashboard")

@login_required
def leave_reapprove(request, leave_id):
    """
    Allow trainer to re-open a leave for approval (Approved/Rejected -> Pending)
    """
    leave = get_object_or_404(LeaveApplication, id=leave_id)
    trainer = request.user.trainer

    if not leave.batch.trainers.filter(id=trainer.id).exists():
        messages.error(request, "You are not authorized to re-approve this leave.")
        return redirect("trainer:leave-dashboard")

    if request.method == "POST":
        leave.status = LeaveApplication.LeaveStatus.PENDING
        leave.rejection_reason = ""  # clear previous rejection reason
        leave.approved_by = None
        leave.approval_date = None
        leave.save()
        messages.success(request, f"Leave for {leave.student.full_name} is now pending again.")
    
    return redirect("trainer:leave-dashboard")

#task
@login_required
def task_dashboard(request):
    trainer = request.user.trainer

    tasks = Task.objects.filter(created_by=trainer)
    submissions = TaskSubmission.objects.filter(task__created_by=trainer)

    total_tasks = tasks.count()
    active_tasks = tasks.filter(due_date__gte=timezone.now().date()).count()
    overdue_tasks = tasks.filter(due_date__lt=timezone.now().date()).count()

    pending_evaluations = submissions.filter(
        status=TaskSubmission.SubmissionStatus.SUBMITTED
    ).count()

    context = {
        "total_tasks": total_tasks,
        "active_tasks": active_tasks,
        "overdue_tasks": overdue_tasks,
        "pending_evaluations": pending_evaluations,
        "active_tab": "dashboard",
    }

    return render(request, "trainer/tasks/dashboard.html", context)

@login_required
def task_create(request):
    trainer = request.user.trainer

    if request.method == "POST":
        form = TaskForm(request.POST, request.FILES)
        # Limit lesson_session choices dynamically
        form.fields["lesson_session"].queryset = LessonSession.objects.filter(
            trainer=trainer,
            batch__in=trainer.batches.all(),
            status=LessonSession.SessionStatus.COMPLETED
        )

        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = trainer
            task.batch = task.lesson_session.batch
            task.save()
            
            # Notify students
            Notification.objects.bulk_create([
                Notification(
                    recipient=student.user,
                    notification_type=Notification.NotificationType.GENERAL,
                    title="New Task Assigned",
                    message=f"Task '{task.title}' assigned for batch '{task.batch.name}'. Due: {task.due_date}.",
                    link_url=f"/student/tasks/{task.id}/",
                )
                for student in task.batch.students.select_related("user").all()
            ])
            messages.success(request, "Task created successfully.")
            return redirect("trainer:task-list")
    else:
        form = TaskForm()
        form.fields["lesson_session"].queryset = LessonSession.objects.filter(
            trainer=trainer,
            batch__in=trainer.batches.all(),
            status=LessonSession.SessionStatus.COMPLETED
        )

    return render(request, "trainer/tasks/create.html", {
        "form": form,
        "active_tab": "create"
    })

@login_required
def task_list(request):
    trainer = getattr(request.user, 'trainer', None)
    if not trainer:
        tasks = Task.objects.none()
    else:
        # Only tasks created by this trainer AND in batches assigned to this trainer
        tasks = Task.objects.filter(
            created_by=trainer,
            batch__in=trainer.batches.all()
        ).order_by('-created_at')

    # Filters from GET params
    batch_id = request.GET.get('batch')
    status = request.GET.get('status')
    deadline = request.GET.get('deadline')

    if batch_id:
        tasks = tasks.filter(batch_id=batch_id)

    if status:
        if status == 'overdue':
            tasks = tasks.filter(due_date__lt=timezone.now().date())
        elif status == 'active':
            tasks = tasks.filter(due_date__gte=timezone.now().date())

    if deadline:
        try:
            date_obj = timezone.datetime.strptime(deadline, "%Y-%m-%d").date()
            tasks = tasks.filter(due_date=date_obj)
        except ValueError:
            pass

    # Trainer-assigned batches for filter dropdown
    batches = trainer.batches.all() if trainer else []

    return render(request, "trainer/tasks/list.html", {
        "tasks": tasks,
        "batches": batches,
        "active_tab": "list",
        "selected_batch": batch_id,
        "selected_status": status,
        "selected_deadline": deadline,
    })

@login_required
def task_submissions(request):
    trainer = getattr(request.user, 'trainer', None)
    if not trainer:
        submissions = TaskSubmission.objects.none()
    else:
        submissions = TaskSubmission.objects.filter(
            task__created_by=trainer,
            task__batch__in=trainer.batches.all()  # only trainer’s batches
        ).select_related("student", "task", "task__batch")

    # Get filters from GET
    batch_id = request.GET.get('batch')
    task_id = request.GET.get('task')
    status = request.GET.get('status')

    if batch_id:
        submissions = submissions.filter(task__batch_id=batch_id)

    if task_id:
        submissions = submissions.filter(task_id=task_id)

    if status:
        submissions = submissions.filter(status=status)

    # Dropdowns for filter form
    batches = trainer.batches.all() if trainer else []
    tasks = Task.objects.filter(
        created_by=trainer,
        batch__in=trainer.batches.all()
    )

    return render(request, "trainer/tasks/submissions.html", {
        "submissions": submissions,
        "batches": batches,
        "tasks": tasks,
        "selected_batch": batch_id,
        "selected_task": task_id,
        "selected_status": status,
        "active_tab": "submissions"
    })
  

@login_required
def evaluate_submission(request, submission_id):
    trainer = getattr(request.user, "trainer", None)

    submission = get_object_or_404(
        TaskSubmission,
        id=submission_id,
        task__created_by=trainer,
        task__batch__in=trainer.batches.all()
    )

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "evaluate":
            marks_input = request.POST.get("marks")
            feedback = request.POST.get("feedback", "").strip()

            try:
                marks = Decimal(marks_input)
            except (TypeError, ValueError):
                messages.error(request, "Invalid marks value.")
                return redirect("trainer:task-evaluate", submission_id=submission.id)

            if marks > submission.task.total_marks:
                messages.error(request, "Marks cannot exceed total marks.")
                return redirect("trainer:task-evaluate", submission_id=submission.id)

            # Update submission
            submission.marks_obtained = marks
            submission.feedback = feedback
            submission.evaluator = trainer
            submission.evaluated_at = timezone.now()
            submission.status = TaskSubmission.SubmissionStatus.EVALUATED
            submission.needs_revision = False
            submission.revision_count += 1
            submission.is_pass = marks >= submission.task.passing_marks

            submission.save()
            
            # Notify student
            Notification.objects.create(
                recipient=submission.student.user,
                notification_type=Notification.NotificationType.GENERAL,
                title="Task Evaluated",
                message=f"Your submission for '{submission.task.title}' evaluated. Marks: {submission.marks_obtained}/{submission.task.total_marks}.",
                link_url=f"/student/tasks/{submission.task.id}/",
            )

            messages.success(request, "Submission evaluated successfully.")
            return redirect("trainer:task-submissions")
        
        elif action == "resubmit":
            feedback = request.POST.get("feedback", "").strip()

            submission.status = TaskSubmission.SubmissionStatus.RESUBMIT
            submission.needs_revision = True
            submission.feedback = feedback
            submission.revision_count += 1
            submission.save()
            
            # Notify student
            Notification.objects.create(
                recipient=submission.student.user,
                notification_type=Notification.NotificationType.GENERAL,
                title="Task Resubmission Requested",
                message=f"Your submission for '{submission.task.title}' needs revision. Feedback: {submission.feedback}",
                link_url=f"/student/tasks/{submission.task.id}/",
            )

            messages.warning(request, "Resubmission requested.")
            return redirect("trainer:task-submissions")

    return render(request, "trainer/tasks/evaluate.html", {
        "submission": submission,
        "active_tab": "submissions"
    })
    

@login_required
def task_view(request, task_id):
    trainer = request.user.trainer

    task = get_object_or_404(
        Task,
        id=task_id,
        created_by=trainer,
        batch__in=trainer.batches.all()
    )

    stats = task.get_completion_stats()

    return render(request, "trainer/tasks/view.html", {
        "task": task,
        "stats": stats,
        "active_tab": "list"
    })
    
@login_required
def task_edit(request, task_id):
    trainer = request.user.trainer

    task = get_object_or_404(
        Task,
        id=task_id,
        created_by=trainer,
        batch__in=trainer.batches.all()
    )

    if request.method == "POST":
        form = TaskForm(request.POST, request.FILES, instance=task)
        form.fields["lesson_session"].queryset = LessonSession.objects.filter(
            trainer=trainer,
            batch__in=trainer.batches.all(),
            status=LessonSession.SessionStatus.COMPLETED
        )

        if form.is_valid():
            
            if not form.has_changed():
                messages.info(request, "No changes were made.")
                return redirect("trainer:task-list")
            
            edited_task = form.save(commit=False)
            edited_task.batch = edited_task.lesson_session.batch
            edited_task.save()
            messages.success(request, "Task updated successfully.")
            return redirect("trainer:task-list")
    else:
        form = TaskForm(instance=task)
        form.fields["lesson_session"].queryset = LessonSession.objects.filter(
            trainer=trainer,
            batch__in=trainer.batches.all(),
            status=LessonSession.SessionStatus.COMPLETED
        )

    return render(request, "trainer/tasks/create.html", {
        "form": form,
        "active_tab": "list",
        "is_edit": True
    })
    

@login_required
@require_POST
def task_delete(request, task_id):
    trainer = request.user.trainer

    task = get_object_or_404(
        Task,
        id=task_id,
        created_by=trainer,
        batch__in=trainer.batches.all()
    )

    if request.method == "POST":
        if task.submissions.exists():
            messages.error(request, "Cannot delete task with submissions.")
            return redirect("trainer:task-list")

        task.delete()
        messages.success(request, "Task deleted successfully.")
        return redirect("trainer:task-list")

    return redirect("trainer:task-list")
# my batches - lessonsessions    
@login_required
def batch_lesson_sessions(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)

    # Separate sessions by status for CSS-only tabs
    planned_sessions = LessonSession.objects.filter(
        batch=batch,
        status=LessonSession.SessionStatus.PLANNED
    ).select_related('lesson_plan').order_by('planned_date')

    completed_sessions = LessonSession.objects.filter(
        batch=batch, status=LessonSession.SessionStatus.COMPLETED
    ).select_related('lesson_plan').order_by('planned_date')

    skipped_sessions = LessonSession.objects.filter(
        batch=batch, status=LessonSession.SessionStatus.SKIPPED
    ).select_related('lesson_plan').order_by('planned_date')

    context = {
        'batch': batch,
        'planned_sessions': planned_sessions,
        'completed_sessions': completed_sessions,
        'skipped_sessions': skipped_sessions,
        'active_tab': 'lesson_sessions'
    }
    return render(request, 'trainer/mybatches/lesson_sessions.html', context)

@login_required
def mark_session_skipped(request, session_id):
    session = get_object_or_404(LessonSession, id=session_id)
    if request.method == "POST":
        session.status = LessonSession.SessionStatus.SKIPPED
        session.save()
        messages.info(request, f"Session {session.lesson_plan.session_number} marked as skipped.")
    return redirect('trainer:batch-sessions', batch_id=session.batch.id)
 

@login_required
def completed_session_detail(request, session_id):
    session = get_object_or_404(LessonSession, id=session_id)

    if request.method == "POST":
        form = CompletedSessionForm(request.POST, instance=session)
        if form.is_valid():

            if not form.has_changed():
                messages.warning(request, "No changes were made.")
                return redirect(
                    'trainer:completed-session-detail',
                    session_id=session.id
                )

            updated_session = form.save(commit=False)

            if (
                updated_session.actual_date and
                session.status != LessonSession.SessionStatus.COMPLETED
            ):
                updated_session.status = LessonSession.SessionStatus.COMPLETED
                updated_session.completed_at = timezone.now()
                
            updated_session.save()

            messages.success(request, "Session details updated successfully.")
            return redirect('trainer:batch-sessions', batch_id=session.batch.id)
    else:
        form = CompletedSessionForm(instance=session)

    context = {
        'session': session,
        'form': form,
        'batch': session.batch,
        'active_tab': 'lesson_sessions',
    }

    return render(request,'trainer/mybatches/completed_session_detail.html',context)

@login_required
def add_session_material(request, session_id):
    session = get_object_or_404(LessonSession, id=session_id)

    #  Prevent upload if not completed
    if session.status != LessonSession.SessionStatus.COMPLETED:
        messages.error(request, "Materials can only be added to completed sessions.")
        return redirect('trainer:completed-session-detail', session.id)

    if request.method == "POST":
        form = SessionMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.lesson_session = session
            material.uploaded_by = request.user.trainer
            material.save()

            messages.success(request, "Material uploaded successfully.")
            return redirect('trainer:completed-session-detail', session_id=session.id)
    else:
        form = SessionMaterialForm()

    return render(request, 'trainer/mybatches/add_session_material.html', {
        'form': form,
        'session': session,
        'batch': session.batch,
        'active_tab': 'lesson_sessions',
    })
    
@login_required
def session_material_detail(request, material_id):
    material = get_object_or_404(SessionMaterial, id=material_id)
    
    session = material.lesson_session
    batch = session.batch

    return render(request, 'trainer/mybatches/session_material_detail.html', {
        'material': material,
        'session': session,
        'batch': batch,
        'active_tab': 'lesson_sessions',
    })
    
@login_required
def edit_session_material(request, material_id):
    material = get_object_or_404(SessionMaterial, id=material_id)

    session = material.lesson_session
    batch = session.batch

    if material.uploaded_by != request.user.trainer:
        messages.error(request, "You are not allowed to edit this material.")
        return redirect('trainer:batch-overview', batch_id=batch.id)

    if request.method == "POST":
        form = SessionMaterialForm(request.POST, request.FILES, instance=material)

        if form.is_valid():

            # ✅ CHECK IF CHANGED
            if not form.has_changed():
                messages.info(request, "No changes were made.")
                return redirect('trainer:edit-session-material', material_id=material.id)

            form.save()
            messages.success(request, "Material updated successfully.")
            return redirect('trainer:session-material-detail', material_id=material.id)

    else:
        form = SessionMaterialForm(instance=material)

    return render(request, 'trainer/mybatches/edit_session_material.html', {
        'form': form,
        'material': material,
        'session': session,
        'batch': batch,
        'active_tab': 'lesson_sessions',
    })
# // student lssue 

@login_required
def trainer_issues_list_view(request):
    """
    List all trainer-related issues assigned to the logged-in trainer.
    """
    trainer = request.user
    issues = StudentIssue.objects.filter(
        issue_type=StudentIssue.IssueType.TRAINER,
        assigned_to=trainer
    ).order_by('-created_at')
    
    return render(request, 'trainer/issues/trainer_issues_list.html', {'issues': issues})

@login_required
def trainer_issue_detail_view(request, pk):
    """
    Show trainer issue details and allow the trainer to add Resolution Notes.
    After submitting, mark the issue as resolved and redirect to the issues list.
    """
    trainer = request.user
    issue = get_object_or_404(
        StudentIssue,
        pk=pk,
        issue_type=StudentIssue.IssueType.TRAINER,
        assigned_to=trainer
    )

    if request.method == "POST":
        form = TrainerIssueResolveForm(request.POST, instance=issue)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.status = StudentIssue.Status.RESOLVED
            issue.resolved_by = trainer
            issue.resolved_at = timezone.now()
            issue.save()
            return redirect('trainer:trainer_assigned_issues')
    else:
        form = TrainerIssueResolveForm(instance=issue)

    return render(request, 'trainer/issues/trainer_issue_detail.html', {
        'issue': issue,
        'form': form
    })
    
# announcements

@login_required
def all_announcements(request):
    trainer = request.user

    selected_audience = request.GET.get('audience', '')
    selected_publish_date = request.GET.get('publish_date', '')
    selected_created_by = request.GET.get('created_by', '')

    # Trainer announcements (apply filters)
    trainer_announcements = Announcement.objects.filter(
        created_by=trainer,
        audience='students'
    )

    # Admin/BDM announcements
    admin_announcements = Announcement.objects.filter(
        created_by__is_staff=True,
        audience__in=['trainers', 'both']
    )

    # Apply filters individually
    if selected_audience:
        trainer_announcements = trainer_announcements.filter(audience=selected_audience)
        admin_announcements = admin_announcements.filter(audience=selected_audience)

    if selected_publish_date:
        trainer_announcements = trainer_announcements.filter(publish_date__date=selected_publish_date)
        admin_announcements = admin_announcements.filter(publish_date__date=selected_publish_date)

    if selected_created_by:
        if selected_created_by == 'trainer':
            admin_announcements = admin_announcements.none()  # remove admin if filtering trainer
        elif selected_created_by == 'bdm':
            trainer_announcements = trainer_announcements.none()  # remove trainer if filtering BDM

    # Combine final querysets
    announcements = trainer_announcements.union(admin_announcements).order_by('-publish_date')

    return render(request, "trainer/announcements/list.html", {
        "announcements": announcements,
        "active_tab": "announcements",
        "selected_audience": selected_audience,
        "selected_publish_date": selected_publish_date,
        "selected_created_by": selected_created_by,
    })
    
@login_required
def create_announcement(request):
    """Trainer can create an announcement for students"""
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.audience = 'students'  # fixed audience
            announcement.save()
            messages.success(request, "Announcement created successfully!")
            return redirect('trainer:all_announcements')
    else:
        form = AnnouncementForm()

    return render(request, "trainer/announcements/create.html", {
        "form": form,
    })
    
@login_required
def view_announcement(request, announcement_id):
    """
    View an announcement.
    Trainers can view their own announcements and announcements created by BDM/admin.
    """
    trainer = request.user

    # Fetch announcement by ID only
    announcement = get_object_or_404(Announcement, id=announcement_id)

    # Permission check: trainer can view if they created it OR it was created by staff/admin
    if announcement.created_by != trainer and not announcement.created_by.is_staff:
        messages.error(request, "You do not have permission to view this announcement.")
        return redirect('trainer:all_announcements')

    return render(request, "trainer/announcements/view.html", {
        "announcement": announcement,
    })


@login_required
def edit_announcement(request, announcement_id):
    """
    Edit an announcement.
    Trainers can only edit their own announcements (not BDM/admin announcements).
    """
    trainer = request.user

    # Only allow editing of announcements created by this trainer
    announcement = get_object_or_404(
        Announcement,
        id=announcement_id,
        created_by=trainer,
        audience='students'
    )

    if request.method == "POST":
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():

            # Check if any changes were made
            if not form.has_changed():
                messages.warning(request, "No changes were made.")
                return redirect('trainer:edit_announcement', announcement_id=announcement.id)

            updated = form.save(commit=False)
            updated.audience = 'students'
            updated.save()
            messages.success(request, "Announcement updated successfully!")
            return redirect('trainer:all_announcements')
    else:
        form = AnnouncementForm(instance=announcement)

    return render(request, "trainer/announcements/edit.html", {
        "form": form,
        "announcement": announcement,
    })
@login_required
@require_POST
def delete_announcement(request, announcement_id):
    """
    Delete an announcement.
    Trainers can only delete their own announcements.
    """
    trainer = request.user

    announcement = get_object_or_404(
        Announcement,
        id=announcement_id,
        created_by=trainer,
        audience='students'
    )

    announcement.delete()
    messages.success(request, "Announcement deleted successfully.")
    return redirect('trainer:all_announcements')



# @login_required
# def final_exam_batchlist(request):
#     """
#     List only batches with completed sessions for creating Final Exam
#     """
#     trainer = request.user.trainer
#     batches = Batch.objects.filter(trainers=trainer, is_active=True).prefetch_related("lesson_sessions", "exams")

#     batch_list = []
#     for batch in batches:
#         completed_sessions = batch.lesson_sessions.filter(status=LessonSession.SessionStatus.COMPLETED).count()
#         if completed_sessions > 0:
#             # Get final exam if exists
#             final_exam = batch.exams.filter(exam_type=Exam.ExamType.FINAL).first()
#             batch_list.append({
#                 "id": batch.id,
#                 "name": batch.name,
#                 "completed_sessions": completed_sessions,
#                 "final_exam_exists": bool(final_exam),
#                 "final_exam_id": final_exam.id if final_exam else None,
#             })

#     return render(request, "trainer/exams/batch_list.html", {"batches": batch_list})

# Replace your existing final_exam_batchlist view in apps/trainer/views.py

# trainer leave
@login_required
def trainer_leave_dashboard(request):
    """List all leave applications of the logged-in trainer"""
    trainer = request.user.trainer
    leaves = TrainerLeave.objects.filter(trainer=trainer).order_by('-applied_at')

    return render(request, "trainer/trainerleave/trainer_leave_dashboard.html", {
        "leaves": leaves
    })


@login_required
def trainer_leave_apply(request):
    """Trainer applies for leave"""
    trainer = request.user.trainer

    if request.method == "POST":
        form = TrainerLeaveForm(request.POST, request.FILES)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.trainer = trainer
            leave.save()
            
            # Notify BDM
            for bdm_user in User.objects.filter(role="admin"):
                Notification.objects.create(
                    recipient=bdm_user,
                    notification_type=Notification.NotificationType.GENERAL,
                    title="Trainer Leave Application",
                    message=f"{leave.trainer.full_name} applied for leave from {leave.start_date} to {leave.end_date}.",
                    link_url=f"/bdm/trainer-leaves/{leave.id}/",
                )

            messages.success(request, "Leave application submitted successfully!")
            return redirect("trainer:trainer-leave-dashboard")
    else:
        form = TrainerLeaveForm()

    return render(request, "trainer/trainerleave/trainer_leave_apply.html", {
        "form": form
    })


@login_required
def trainer_leave_detail(request, leave_id):
    """View single leave details"""
    trainer = request.user.trainer
    leave = get_object_or_404(TrainerLeave, id=leave_id, trainer=trainer)

    return render(request, "trainer/trainerleave/trainer_leave_detail.html", {
        "leave": leave
    })


@login_required
def trainer_leave_edit(request, leave_id):
    """Edit a leave application"""
    trainer = request.user.trainer
    leave = get_object_or_404(TrainerLeave, id=leave_id, trainer=trainer)

    if leave.status != TrainerLeave.LeaveStatus.PENDING:
        messages.error(request, "Only pending leaves can be edited.")
        return redirect("trainer:trainer-leave-dashboard")

    if request.method == "POST":
        form = TrainerLeaveForm(request.POST, request.FILES, instance=leave)
        if form.is_valid():
            form.save()
            messages.success(request, "Leave application updated successfully.")
            return redirect("trainer:trainer-leave-dashboard")
    else:
        form = TrainerLeaveForm(instance=leave)

    return render(request, "trainer/trainerleave/trainer_leave_apply.html", {
        "form": form,
        "is_edit": True
    })


@login_required
def trainer_leave_delete(request, leave_id):
    """Delete a leave application"""
    trainer = request.user.trainer
    leave = get_object_or_404(TrainerLeave, id=leave_id, trainer=trainer)

    if leave.status != TrainerLeave.LeaveStatus.PENDING:
        messages.error(request, "Only pending leaves can be deleted.")
    else:
        leave.delete()
        messages.success(request, "Leave application deleted successfully.")

    return redirect("trainer:trainer-leave-dashboard")




IST = ZoneInfo("Asia/Kolkata")

def auto_publish_exam(exam):
    if exam.exam_type != Exam.ExamType.FINAL:
        return
    if exam.is_published:
        return

    exam_time = exam.exam_time if exam.exam_time else datetime.time(0, 0)
    
    # Treat entered time as IST, make it timezone-aware
    naive_dt = datetime.datetime.combine(exam.scheduled_date, exam_time)
    scheduled_ist = naive_dt.replace(tzinfo=IST)  # mark as IST

    if timezone.now() >= scheduled_ist:
        Exam.objects.filter(pk=exam.pk).update(is_published=True)
        exam.is_published = True
        
LATE_GRACE_MINUTES = 30  # configurable

def auto_complete_exam(exam):
    """Mark exam completed only after end time + grace period."""
    if exam.exam_type != Exam.ExamType.FINAL:
        return
    if exam.is_completed:
        return

    exam_time = exam.exam_time if exam.exam_time else datetime.time(0, 0)
    naive_dt = datetime.datetime.combine(exam.scheduled_date, exam_time)
    scheduled_ist = naive_dt.replace(tzinfo=IST)

    exam_end_ist = scheduled_ist + datetime.timedelta(minutes=exam.duration_minutes)
    grace_end_ist = exam_end_ist + datetime.timedelta(minutes=LATE_GRACE_MINUTES)

    if timezone.now() >= grace_end_ist:
        Exam.objects.filter(pk=exam.pk).update(is_completed=True, is_published=True)
        exam.is_completed = True
        exam.is_published = True
        
        # Notify BDM
        for bdm_user in User.objects.filter(is_staff=True):
            Notification.objects.create(
                recipient=bdm_user,
                notification_type=Notification.NotificationType.GENERAL,
                title="Final Exam Completed",
                message=f"Exam '{exam.title}' for batch '{exam.batch.name}' is completed. Results ready.",
                link_url=f"/trainer/exams/{exam.id}/results/",
            )


def auto_mark_late_submissions(exam):
    """Mark submissions as LATE if submitted after exam end but within grace period."""
    if not exam.is_published:
        return

    exam_time = exam.exam_time if exam.exam_time else datetime.time(0, 0)
    naive_dt = datetime.datetime.combine(exam.scheduled_date, exam_time)
    scheduled_ist = naive_dt.replace(tzinfo=IST)

    exam_end_ist = scheduled_ist + datetime.timedelta(minutes=exam.duration_minutes)

    # Submitted after exam end time = late
    late_submissions = ExamSubmission.objects.filter(
        exam=exam,
        status=ExamSubmission.SubmissionStatus.SUBMITTED,
        submitted_at__gt=exam_end_ist,
    )
    late_submissions.update(status=ExamSubmission.SubmissionStatus.LATE)

@login_required
def final_exam_batchlist(request):
    """
    List batches with completed sessions.
    Each row shows quick-access buttons for Submissions and Results
    if a Final Exam already exists for that batch.
    """
    trainer = request.user.trainer
    batches = (
        Batch.objects
        .filter(trainers=trainer, is_active=True)
        .prefetch_related("lesson_sessions", "exams")
    )

    batch_list = []
    for batch in batches:
        completed_sessions = batch.lesson_sessions.filter(
            status=LessonSession.SessionStatus.COMPLETED
        ).count()

        if completed_sessions == 0:
            continue  # skip batches with no completed sessions

        final_exam = batch.exams.filter(exam_type=Exam.ExamType.FINAL).first()
        

        # Submission & result counts (only if exam exists)
        submission_count   = 0
        pending_count      = 0
        evaluated_count    = 0
        result_count       = 0
        passed_count       = 0

        if final_exam:
            auto_publish_exam(final_exam)
            auto_complete_exam(final_exam)
            auto_mark_late_submissions(final_exam)
            submission_count  = ExamSubmission.objects.filter(exam=final_exam).count()
            pending_count     = ExamSubmission.objects.filter(
                exam=final_exam,
                status=ExamSubmission.SubmissionStatus.SUBMITTED
            ).count()
            evaluated_count   = ExamSubmission.objects.filter(
                exam=final_exam,
                status=ExamSubmission.SubmissionStatus.EVALUATED
            ).count()
            result_count      = ExamResult.objects.filter(exam=final_exam).count()
            passed_count      = ExamResult.objects.filter(exam=final_exam, is_pass=True).count()

        batch_list.append({
            "id":                  batch.id,
            "name":                batch.name,
            "completed_sessions":  completed_sessions,
            "total_students":      batch.students.count(),
            # exam
            "final_exam_exists":   bool(final_exam),
            "final_exam_id":       final_exam.id if final_exam else None,
            "is_published":        final_exam.is_published if final_exam else False,
            # submission stats
            "submission_count":    submission_count,
            "pending_count":       pending_count,
            "evaluated_count":     evaluated_count,
            # result stats
            "result_count":        result_count,
            "passed_count":        passed_count,
            "is_completed":        final_exam.is_completed if final_exam else False,
        })

    return render(request, "trainer/exams/batch_list.html", {"batches": batch_list})


@login_required
def final_exam_create(request, batch_id):
    """
    Create a Final Exam for a batch
    """
    trainer = request.user.trainer
    batch = get_object_or_404(Batch.objects.filter(trainers=trainer, is_active=True), id=batch_id)

    if not batch.lesson_sessions.filter(status=LessonSession.SessionStatus.COMPLETED).exists():
        messages.error(request, "Cannot create exam: batch has no completed sessions.")
        return redirect("trainer:exam-final-batchlist")

    # Prevent duplicate final exam
    if batch.exams.filter(exam_type=Exam.ExamType.FINAL).exists():
        messages.error(request, "Final Exam already exists for this batch.")
        return redirect("trainer:exam-final-batchlist")

    if request.method == "POST":
        form = ExamForm(request.POST, request.FILES)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.batch = batch
            exam.exam_type = Exam.ExamType.FINAL
            exam.created_by = trainer
            exam.save()
            messages.success(request, f"Final Exam created for batch {batch.name}.")
            return redirect("trainer:exam-final-view", exam_id=exam.id)
    else:
        form = ExamForm()

    return render(request, "trainer/exams/create_final.html", {"form": form, "batch": batch})


@login_required
def final_exam_view(request, exam_id):
    """
    View Final Exam details
    """
    trainer = request.user.trainer
    exam = get_object_or_404(Exam, id=exam_id, created_by=trainer)
    
    auto_publish_exam(exam)
    auto_complete_exam(exam)
    auto_mark_late_submissions(exam)
    
    return render(request, "trainer/exams/view_final.html", {"exam": exam})


@login_required
def final_exam_edit(request, exam_id):
    trainer = request.user.trainer
    exam = get_object_or_404(Exam, id=exam_id, created_by=trainer)
    auto_publish_exam(exam)
    auto_complete_exam(exam)
    
    # Prevent editing if published
    if exam.is_published:
        messages.error(request, "Cannot edit. Exam is already published.")
        return redirect("trainer:exam-final-view", exam_id=exam.id)

    if request.method == "POST":
        form = ExamForm(request.POST, request.FILES, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, "Final Exam updated successfully.")
            return redirect("trainer:exam-final-view", exam_id=exam.id)
    else:
        form = ExamForm(instance=exam)

    return render(request, "trainer/exams/edit_final.html", {"form": form, "exam": exam})

@login_required
@require_POST
def final_exam_publish(request, exam_id):
    trainer = request.user.trainer
    exam = get_object_or_404(Exam, id=exam_id, created_by=trainer)

    if exam.is_published:
        messages.info(request, "Exam is already published.")
    else:
        exam.is_published = True
        exam.save()
        
        # Notify students
        Notification.objects.bulk_create([
            Notification(
                recipient=student.user,
                notification_type=Notification.NotificationType.GENERAL,
                title="Final Exam Published",
                message=f"Exam '{exam.title}' is now live. Scheduled: {exam.scheduled_date} at {exam.exam_time}. Duration: {exam.duration_minutes} mins.",
                link_url=f"/student/exams/{exam.id}/",
            )
            for student in exam.batch.students.select_related("user").all()
        ])
        messages.success(request, f"Exam '{exam.title}' is now published and visible to students.")

    return redirect("trainer:exam-final-view", exam_id=exam.id)

# exam evaluation 
@login_required
def exam_submissions_list(request, exam_id):
    """
    Show every student submission for a particular exam.
    Trainer can see status, download files, and jump to evaluate.
    """
    trainer = request.user.trainer
    exam = get_object_or_404(Exam, id=exam_id, created_by=trainer)
    auto_publish_exam(exam)
    auto_complete_exam(exam)
    auto_mark_late_submissions(exam)
    
    if not exam.is_published:
        messages.error(request, "Exam is not published yet.")
        return redirect("trainer:exam-final-view", exam_id=exam.id)

    submissions = (
        ExamSubmission.objects
        .filter(exam=exam)
        .select_related("student", "student__user", "evaluated_by")
        .order_by("-submitted_at")
    )

    # Quick stats
    total        = submissions.count()
    evaluated    = submissions.filter(status=ExamSubmission.SubmissionStatus.EVALUATED).count()
    pending      = submissions.filter(status=ExamSubmission.SubmissionStatus.SUBMITTED).count()
    late         = submissions.filter(status=ExamSubmission.SubmissionStatus.LATE).count()
    rejected     = submissions.filter(status=ExamSubmission.SubmissionStatus.REJECTED).count()

    context = {
        "exam": exam,
        "submissions": submissions,
        "total": total,
        "evaluated": evaluated,
        "pending": pending,
        "late": late,
        "rejected": rejected,
    }
    return render(request, "trainer/exams/submissions_list.html", context)


# Evaluate a single submission
@login_required
def exam_evaluate_submission(request, submission_id):
    """
    Trainer evaluates (marks + feedback) a student's exam submission.
    """
    trainer = request.user.trainer
    submission = get_object_or_404(
        ExamSubmission,
        id=submission_id,
        exam__created_by=trainer,
    )
    exam = submission.exam
    

    if request.method == "POST":
        action = request.POST.get("action")

        # EVALUATE
        if action == "evaluate":
            marks_str = request.POST.get("marks", "").strip()
            feedback  = request.POST.get("feedback", "").strip()

            try:
                marks = int(marks_str)
            except (ValueError, TypeError):
                messages.error(request, "Please enter a valid integer for marks.")
                return redirect("trainer:exam-evaluate-submission", submission_id=submission.id)

            if marks < 0 or marks > exam.total_marks:
                messages.error(request, f"Marks must be between 0 and {exam.total_marks}.")
                return redirect("trainer:exam-evaluate-submission", submission_id=submission.id)

            # Update submission
            submission.marks_obtained  = marks
            submission.feedback        = feedback
            submission.evaluated_by    = trainer
            submission.evaluated_at    = timezone.now()
            submission.status          = ExamSubmission.SubmissionStatus.EVALUATED
            submission.save()

            # Create / update ExamResult (triggers grade calculation via save())
            result, created = ExamResult.objects.get_or_create(
                exam=exam,
                student=submission.student,
                defaults={"evaluator": trainer},
            )
            result.marks_obtained = marks
            result.evaluator      = trainer
            result.remarks        = feedback
            result.save()  # triggers auto-grade in ExamResult.save()

            messages.success(request, f"Submission evaluated. Grade: {result.grade}")
            return redirect("trainer:exam-submissions-list", exam_id=exam.id)

        # REJECT 
        elif action == "reject":
            reason = request.POST.get("feedback", "").strip()
            submission.status   = ExamSubmission.SubmissionStatus.REJECTED
            submission.feedback = reason
            submission.save()
            messages.warning(request, "Submission rejected.")
            return redirect("trainer:exam-submissions-list", exam_id=exam.id)

    context = {
        "submission": submission,
        "exam": exam,
    }
    return render(request, "trainer/exams/exam_evaluation.html", context)


#Results list for an exam
@login_required
def exam_results_list(request, exam_id):
    """
    Show pass/fail grade breakdown for all students in an exam.
    """
    trainer = request.user.trainer
    exam = get_object_or_404(Exam, id=exam_id, created_by=trainer)
    auto_publish_exam(exam)
    auto_complete_exam(exam)
    auto_mark_late_submissions(exam)
    
    if not exam.is_published:
        messages.error(request, "Results unavailable. Exam not published.")
        return redirect("trainer:exam-final-view", exam_id=exam.id)

    results = (
        ExamResult.objects
        .filter(exam=exam)
        .select_related("student", "evaluator")
        .order_by("-marks_obtained")
    )

    total   = results.count()
    passed  = results.filter(is_pass=True).count()
    failed  = results.filter(is_pass=False).count()
    pending = results.filter(marks_obtained__isnull=True).count()

    context = {
        "exam": exam,
        "results": results,
        "total": total,
        "passed": passed,
        "failed": failed,
        "pending": pending,
    }
    return render(request, "trainer/exams/results_list.html", context)


# Single result detail
@login_required
def exam_result_detail(request, result_id):
    trainer = request.user.trainer
    result  = get_object_or_404(ExamResult, id=result_id, exam__created_by=trainer)
    auto_publish_exam(result.exam)
    auto_complete_exam(result.exam)
    auto_mark_late_submissions(result.exam)
    
    if not result.exam.is_published:
        messages.error(request, "Result unavailable. Exam not published.")
        return redirect("trainer:exam-final-view", exam_id=result.exam.id)

    return render(request, "trainer/exams/result_detail.html", {"result": result})


@login_required
def certificate_batch_list(request):
    """
    Show only batches where final exam is completed.
    Eligibility count derived from ExamResult — no Certificate DB touch.
    """
    trainer = request.user.trainer
    batches = (
        Batch.objects
        .filter(trainers=trainer, is_active=True)
        .prefetch_related("exams", "students")
    )

    batch_list = []
    for batch in batches:
        final_exam = batch.exams.filter(exam_type=Exam.ExamType.FINAL).first()

        if not final_exam or not final_exam.is_completed:
            continue

        total_students = batch.students.count()

        # Count eligible from ExamResult only — no Certificate DB touch
        eligible_count = ExamResult.objects.filter(
            exam=final_exam,
            is_pass=True,
        ).count()

        batch_list.append({
            "id":             batch.id,
            "name":           batch.name,
            "total_students": total_students,
            "eligible_count": eligible_count,
            "not_eligible":   total_students - eligible_count,
            "exam_title":     final_exam.title,
        })

    return render(request, "trainer/certificate/batch_list.html", {"batches": batch_list})


@login_required
def certificate_students_list(request, batch_id):
    """
    List all students with eligibility status.
    Derived from ExamResult only — no Certificate DB touch.
    """
    trainer = request.user.trainer
    batch   = get_object_or_404(Batch, id=batch_id, trainers=trainer, is_active=True)

    final_exam = batch.exams.filter(exam_type=Exam.ExamType.FINAL).first()
    if not final_exam or not final_exam.is_completed:
        messages.error(request, "Certificate can only be checked after final exam is completed.")
        return redirect("trainer:certificate-batch-list")

    students = batch.students.all().select_related("user")

    student_list = []
    for student in students:

        # Only fetch exam result — no Certificate DB lookup
        exam_result = ExamResult.objects.filter(
            student=student,
            exam=final_exam,
        ).first()

        student_list.append({
            "student":     student,
            "exam_result": exam_result,
            "is_eligible": bool(exam_result and exam_result.is_pass),
        })

    return render(request, "trainer/certificate/students_list.html", {
        "batch":        batch,
        "student_list": student_list,
        "final_exam":   final_exam,
    })


@login_required
def certificate_check_eligibility(request, batch_id, student_id):
    """
    Trainer checks eligibility on screen only.
    Nothing saved to DB — admin handles Certificate creation.
    """
    trainer = request.user.trainer
    batch   = get_object_or_404(Batch, id=batch_id, trainers=trainer, is_active=True)
    student = get_object_or_404(Student, id=student_id)

    final_exam = batch.exams.filter(exam_type=Exam.ExamType.FINAL).first()
    if not final_exam or not final_exam.is_completed:
        messages.error(request, "Exam not completed yet.")
        return redirect("trainer:certificate-batch-list")

    # Check exam result — NO DB touch at all
    exam_result = ExamResult.objects.filter(
        student=student,
        exam=final_exam,
    ).first()

    if not exam_result:
        messages.warning(
            request,
            f"{student.full_name} — No final exam result found."
        )
    elif not exam_result.is_pass:
        messages.warning(
            request,
            f"{student.full_name} — Did not pass "
            f"(Marks: {exam_result.marks_obtained} / {final_exam.total_marks})"
        )
    else:
        messages.success(
            request,
            f"{student.full_name} — Eligible ✓ "
            f"(Marks: {exam_result.marks_obtained} / {final_exam.total_marks})"
        )

    return redirect("trainer:certificate-students-list", batch_id=batch.id)




@login_required
@require_POST
def mark_notification_read(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notif.mark_as_read()
    return redirect(request.POST.get('next', 'trainer:dashboard'))


@login_required
@require_POST
def mark_all_notifications_read(request):
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())
    return redirect('trainer:dashboard')


@login_required
def substitute_list(request):
    trainer = request.user.trainer

    already_requested_session_ids = SubstituteTeaching.objects.filter(
        original_trainer=trainer
    ).values_list("lesson_session_id", flat=True)

    sessions = LessonSession.objects.filter(
        trainer=trainer,
        status=LessonSession.SessionStatus.PLANNED
    ).exclude(
        id__in=already_requested_session_ids
    ).order_by("planned_date")

    return render(request, "trainer/substitute/substitute_list.html", {
        "sessions": sessions,
    })


@login_required
def my_substitute_requests(request):
    trainer = request.user.trainer

    requests = SubstituteTeaching.objects.filter(
        original_trainer=trainer
    ).select_related("batch", "lesson_session", "substitute_trainer")

    return render(request, "trainer/substitute/my_substitute_requests.html", {
        "requests": requests,
    })


@login_required
def request_substitute(request, session_id):
    trainer = request.user.trainer
    session = get_object_or_404(LessonSession, id=session_id)

    if SubstituteTeaching.objects.filter(
        lesson_session=session,
        original_trainer=trainer
    ).exists():
        messages.warning(request, "Substitute already requested for this session.")
        return redirect("trainer:substitute-list")

    if request.method == "POST":
        reason = request.POST.get("reason", "").strip()

        if not reason:
            messages.error(request, "Reason is required.")
            return render(request, "trainer/substitute/request_substitute.html", {"session": session})

        substitute = SubstituteTeaching.objects.create(
            batch=session.batch,
            lesson_session=session,
            original_trainer=trainer,
            substitute_trainer=trainer,
            date=session.planned_date,
            reason_for_substitution=reason,
            notes="pending"
        )

        # Notify BDM
        for bdm_user in User.objects.filter(is_staff=True):
            Notification.objects.create(
                recipient=bdm_user,
                notification_type=Notification.NotificationType.GENERAL,
                title="Substitute Request Raised",
                message=(
                    f"{trainer.full_name} requested a substitute for "
                    f"batch '{session.batch.name}' on {session.planned_date}. "
                    f"Reason: {reason}"
                ),
                link_url=f"/bdm/substitute/{substitute.id}/",
            )

        messages.success(request, "Substitute request submitted successfully.")
        return redirect("trainer:my-substitute-requests")

    return render(request, "trainer/substitute/request_substitute.html", {"session": session})