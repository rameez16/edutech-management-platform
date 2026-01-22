from django.urls import path
from . import views

app_name = "trainer"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("profile/", views.trainer_profile, name="profile"),
    path("mybatches/", views.my_batches, name="my_batches"),
]