from django.urls import path
from . import views

app_name = "trainer"

urlpatterns = [
    
    # Dashboard
    path("trainer_dashboard", views.dashboard, name="dashboard"),
    
    #my_profile
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile-edit"),
    
    # my_batches
    path("mybatches/", views.my_batches, name="batches"),
    path("batches/<int:batch_id>/overview/", views.batch_overview_view, name="batch-overview"),
    path("batches/<int:batch_id>/students/", views.batch_students_view, name="batch-students"),
    path("batches/<int:batch_id>/students/<int:student_id>/",views.student_details_view,name="batch-student-details"),
    path('batch/<int:batch_id>/lesson-plan/',views.batch_lesson_plan,name='batch-lesson-plan'),
    path("batches/<int:batch_id>/feedback/",views.batch_feedback_view,name="batch-feedback"),
    
    path('batch/<int:batch_id>/sessions/', views.batch_lesson_sessions, name='batch-sessions'),
    path('lesson-session/complete/<int:session_id>/', views.mark_session_complete, name='mark-session-complete'),
    path('lesson-session/skip/<int:session_id>/', views.mark_session_skipped, name='mark-session-skipped'),
    path('lesson-session/completed/<int:session_id>/', views.completed_session_detail, name='completed-session-detail'),
    path('lesson-session/<int:session_id>/add-material/',views.add_session_material,name='add-session-material'),

    # attendance
    path("attendance/", views.attendance_batch_list, name="attendance-batch-list"),
    path("attendance/batch/<int:batch_id>/", views.attendance_session_list, name="attendance-sessions"),
    path("attendance/session/<int:session_id>/mark/", views.attendance_mark, name="attendance-mark"),
    path("attendance/session/<int:session_id>/view/",views.attendance_view,name="attendance-view"),
    
    # student_leave
    path("leaves/", views.leave_dashboard, name="leave-dashboard"),
    path("leaves/<int:leave_id>/", views.leave_detail, name="leave-detail"),
    path("leaves/<int:leave_id>/process/", views.process_leave, name="leave-process"),
    path('leave/<int:leave_id>/reapprove/', views.leave_reapprove, name='leave-reapprove'),
    
    # Task Management
    path("tasks/", views.task_dashboard, name="task-dashboard"),
    path("tasks/create/", views.task_create, name="task-create"),
    path("tasks/list/", views.task_list, name="task-list"),
    path("tasks/submissions/", views.task_submissions, name="task-submissions"),
    path("tasks/evaluate/<int:submission_id>/",views.evaluate_submission,name="task-evaluate"),

]