from django.urls import path
from . import views

app_name = "trainer"

urlpatterns = [
    
    # Dashboard
    path("trainer_dashboard", views.dashboard, name="dashboard"),
    
    # my_batches
    path("mybatches/", views.my_batches, name="my_batches"),
    path("batches/<int:batch_id>/overview/", views.batch_overview_view, name="batch-overview"),
    path("batches/<int:batch_id>/students/", views.batch_students_view, name="batch-students"),
    path("batches/<int:batch_id>/students/<int:student_id>/",views.student_detail_view,name="student-detail",),

    #my_profile
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile-edit"),
]