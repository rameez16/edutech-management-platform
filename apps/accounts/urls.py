from django.urls import path
from apps.accounts import views

app_name='accounts'

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    # path("users/create/", views.create_user, name="create_user"),
    
    path("lms/login/", views.lms_login, name="lms_login"),
    path("lms/dashboard/", views.lms_dashboard, name="lms_dashboard"),
    path("lms/logout/", views.lms_logout, name="lms_logout"),
]