from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from apps.trainer.forms import TrainerProfileForm, TaskForm, EvaluationForm

from apps.bdm.models import Trainer, Batch, Student
from apps.trainer.models import Module, Attendance, LessonSession, Task, TaskSubmission
from apps.student.models import StudentFeedback, LeaveApplication




# dashboard
def dashboard(request):
    """Dashboard view"""
    context = {
        'page_title': 'Dashboard',
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
        .prefetch_related("students")
        .order_by("-start_date")
    )

    today = timezone.now().date()
    batch_list = []

    for batch in batches:
        total_days = (batch.expected_finish_date - batch.start_date).days
        completed_days = max((today - batch.start_date).days, 0)

        progress = 0
        if total_days > 0:
            progress = min(round((completed_days / total_days) * 100), 100)
            
        if progress >= 100:
            status = "Completed"
        elif today < batch.start_date:
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
            "classes_completed": completed_days,
            "total_students": batch.students.count(),
            "progress": progress,
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
    ).select_related("lesson_plan").order_by("-lesson_plan__session_number","-planned_date")


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
        form.fields["lesson_session"].queryset = LessonSession.objects.filter(
            trainer=trainer
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
            trainer=trainer
        )

    return render(request, "trainer/tasks/create.html", {
        "form": form,
        "active_tab": "create"
    })

@login_required
def task_list(request):
    tasks = Task.objects.filter(created_by=request.user.trainer)

    return render(request, "trainer/tasks/list.html", {
        "tasks": tasks,
        "active_tab": "list"
    })


@login_required
def task_submissions(request):
    submissions = TaskSubmission.objects.filter(
        task__created_by=request.user.trainer
    ).select_related("student", "task")

    return render(request, "trainer/tasks/submissions.html", {
        "submissions": submissions,
        "active_tab": "submissions"
    })
    
    
def evaluate_submission(request, submission_id):
    submission = get_object_or_404(TaskSubmission, id=submission_id)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "evaluate":
            marks = request.POST.get("marks")
            feedback = request.POST.get("feedback")

            submission.marks_obtained = marks
            submission.feedback = feedback
            submission.status = TaskSubmission.SubmissionStatus.EVALUATED
            submission.needs_revision = False
            submission.save()

        elif action == "resubmit":
            feedback = request.POST.get("feedback")
            submission.request_resubmission(feedback)

        return redirect("trainer:task-submissions")

    return render(request, "trainer/tasks/evaluate.html", {
        "submission": submission,
        "active_tab": "submissions"
    })
    
    
