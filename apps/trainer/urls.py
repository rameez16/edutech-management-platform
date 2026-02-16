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

    path("attendance/", views.attendance_batch_list, name="attendance-batch-list"),
    path("attendance/batch/<int:batch_id>/", views.attendance_session_list, name="attendance-sessions"),
    path("attendance/session/<int:session_id>/mark/", views.attendance_mark, name="attendance-mark"),
    path("attendance/session/<int:session_id>/view/",views.attendance_view,name="attendance-view"),
]