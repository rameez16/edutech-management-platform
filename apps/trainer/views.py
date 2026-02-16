from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from apps.trainer.forms import TrainerProfileForm

from apps.bdm.models import Trainer, Batch, Student
from apps.trainer.models import Module, Attendance, LessonSession
from apps.student.models import StudentFeedback



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


    
def attendance_session_list(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)

    sessions = LessonSession.objects.filter(
        batch=batch,
        status=LessonSession.SessionStatus.COMPLETED
    ).select_related("lesson_plan").order_by("-lesson_plan__session_number")

    return render(request, "trainer/attendance/session_list.html", {
        "batch": batch,
        "sessions": sessions
    })
    
@login_required
def attendance_mark(request, session_id):
    session = get_object_or_404(LessonSession, id=session_id)
    batch = session.batch

    # Only allow completed sessions
    if session.status != LessonSession.SessionStatus.COMPLETED:
        messages.error(
            request,
            "Attendance can only be marked for completed sessions."
        )
        return redirect("trainer:attendance-sessions", batch_id=batch.id)

    students = batch.students.all()

    if request.method == "POST":
        for student in students:
            is_checked = request.POST.get(f"student_{student.id}") == "on"

            Attendance.objects.update_or_create(
                student=student,
                batch=batch,
                date=session.actual_date,
                defaults={
                    "lesson_session": session,
                    "status": "present" if is_checked else "absent",
                    "marked_by": session.trainer,
                    "remarks": ""
                }
            )

        messages.success(request, "Attendance saved successfully.")
        return redirect("trainer:attendance-sessions", batch_id=batch.id)

    # Prefill existing attendance: list of student IDs marked present
    existing_attendance_students = Attendance.objects.filter(
        batch=batch,
        date=session.actual_date,
        status='present'
    ).values_list('student_id', flat=True)

    return render(request, "trainer/attendance/mark_attendance.html", {
        "session": session,
        "students": students,
        "existing_attendance_students": existing_attendance_students
    })


def attendance_view(request, session_id):
    session = get_object_or_404(LessonSession, id=session_id)
    batch = session.batch

    attendance_records = Attendance.objects.filter(
        batch=batch,
        date=session.actual_date
    ).select_related("student")

    total_students = batch.students.count()
    present_count = attendance_records.filter(status="present").count()
    absent_count = attendance_records.filter(status="absent").count()

    return render(request, "trainer/attendance/view_attendance.html", {
        "session": session,
        "attendance_records": attendance_records,
        "total_students": total_students,
        "present_count": present_count,
        "absent_count": absent_count,
    })


