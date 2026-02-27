from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Max
from decimal import Decimal

from apps.trainer.forms import TrainerProfileForm, TaskForm, EvaluationForm , CompletedSessionForm, SessionMaterialForm,TrainerIssueResolveForm,AnnouncementForm

from apps.bdm.models import Trainer, Batch, Student, StudentIssue, Announcement
from apps.trainer.models import Module, Attendance, LessonSession, Task, TaskSubmission, SessionMaterial
from apps.student.models import StudentFeedback, LeaveApplication




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

    today = timezone.now().date()

    # Progress calculation
    total_days = (batch.expected_finish_date - batch.start_date).days
    completed_days = max((today - batch.start_date).days, 0)

    progress = 0
    if total_days > 0:
        progress = min(round((completed_days / total_days) * 100), 100)

    # Student stats
    total_students = batch.students.count()
    active_students = batch.students.filter(user__is_active=True).count()
    inactive_students = batch.students.filter(user__is_active=False).count()

    context = {
        "batch": batch,
        "progress": progress,
        "classes_completed": completed_days,
        "total_students": total_students,
        "active_students": active_students,
        "inactive_students": inactive_students,
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

            messages.success(request, "Submission evaluated successfully.")
            return redirect("trainer:task-submissions")
        
        elif action == "resubmit":
            feedback = request.POST.get("feedback", "").strip()

            submission.status = TaskSubmission.SubmissionStatus.RESUBMIT
            submission.needs_revision = True
            submission.feedback = feedback
            submission.revision_count += 1
            submission.save()

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