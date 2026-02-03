from django.urls import path
from . import views

app_name = "trainer"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("profile/", views.trainer_profile, name="profile"),
    path("mybatches/", views.my_batches, name="my_batches"),
    path("batches/<int:batch_id>/overview/", views.batch_overview_view, name="batch-overview"),
    path("batches/<int:batch_id>/students/", views.batch_students_view, name="batch-students"),
    
    path(
    "batches/<int:batch_id>/students/<int:student_id>/",
    views.student_detail_view,
    name="student-detail",
),

]