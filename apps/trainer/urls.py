from django.urls import path
from . import views

app_name = "trainer"

urlpatterns = [
    path("test/", views.test_view, name="trainer-test")
]