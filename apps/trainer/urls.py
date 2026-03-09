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
    path('lesson-session/skip/<int:session_id>/', views.mark_session_skipped, name='mark-session-skipped'),
    path('lesson-session/completed/<int:session_id>/', views.completed_session_detail, name='completed-session-detail'),
    path('lesson-session/<int:session_id>/add-material/',views.add_session_material,name='add-session-material'),
    path('session-material/<int:material_id>/',views.session_material_detail,name='session-material-detail'),
    path('session-material/<int:material_id>/edit/',views.edit_session_material,name='edit-session-material'),

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
    path("tasks/<int:task_id>/", views.task_view, name="task-view"),
    path("tasks/<int:task_id>/edit/", views.task_edit, name="task-edit"),
    path("task/<int:task_id>/delete/",views.task_delete,name="task-delete"),
    path("tasks/submissions/", views.task_submissions, name="task-submissions"),
    path("tasks/evaluate/<int:submission_id>/",views.evaluate_submission,name="task-evaluate"),
    
    # Student Issues
    path('assigned-issues/', views.trainer_issues_list_view, name='trainer_assigned_issues'),
    path('assigned-issues/<int:pk>/', views.trainer_issue_detail_view, name='trainer_issue_detail'),
    
    # announcements
    path("trainerannouncements/", views.all_announcements, name="all_announcements"),
    path("trainerannouncements/create/", views.create_announcement, name="create_announcement"),
    path("trainerannouncements/<int:announcement_id>/view/", views.view_announcement, name="view_announcement"),
    path("trainerannouncements/<int:announcement_id>/edit/", views.edit_announcement, name="edit_announcement"),
    path("trainerannouncements/<int:announcement_id>/delete/",views.delete_announcement,name="delete_announcement"),
    
    # exam 
    path("exams/final/", views.final_exam_batchlist, name="exam-final-batchlist"),
    path("exams/final/<int:batch_id>/create/", views.final_exam_create, name="exam-final-create"),
    path("exams/final/<int:exam_id>/view/", views.final_exam_view, name="exam-final-view"),
    path("exams/final/<int:exam_id>/edit/", views.final_exam_edit, name="exam-final-edit"),
    path("exams/final/<int:exam_id>/publish/", views.final_exam_publish, name="exam-final-publish"),
    
    # exam submissions
    path("exams/final/<int:exam_id>/submissions/", views.exam_submissions_list, name="exam-submissions-list"),
    path("exams/final/submissions/<int:submission_id>/evaluate/", views.exam_evaluate_submission, name="exam-evaluate-submission"),

    # exam results
    path("exams/final/<int:exam_id>/results/", views.exam_results_list, name="exam-results-list"),
    path("exams/final/results/<int:result_id>/", views.exam_result_detail, name="exam-result-detail"),
    
    
    # trainer leave updates 
    path('trainerleave/', views.trainer_leave_dashboard, name='trainer-leave-dashboard'),
    path('trainerleave/apply/', views.trainer_leave_apply, name='trainer-leave-apply'),
    path('trainerleave/<int:leave_id>/', views.trainer_leave_detail, name='trainer-leave-detail'),
    path('trainerleave/<int:leave_id>/edit/', views.trainer_leave_edit, name='trainer-leave-edit'),
    path('trainerleave/<int:leave_id>/delete/', views.trainer_leave_delete, name='trainer-leave-delete'),
    
    # certificates 
    path("certificates/", views.certificate_batch_list, name="certificate-batch-list"),
    path("certificates/<int:batch_id>/students/", views.certificate_students_list, name="certificate-students-list"),
    path("certificates/<int:batch_id>/check/<int:student_id>/", views.certificate_check_eligibility, name="certificate-check-eligibility"),
    
    #notifications
    path('trainernotifications/mark-read/<int:notif_id>/', views.mark_notification_read, name='mark-notif-read'),
    path('trainernotifications/mark-all-read/', views.mark_all_notifications_read, name='mark-all-notif-read'),
    
    #substitute trainer
    path("substitute/", views.substitute_list, name="substitute-list"),
    path("substitute/requests/", views.my_substitute_requests, name="my-substitute-requests"),
    path("substitute/request/<int:session_id>/", views.request_substitute, name="request-substitute"),
   
]