from django.urls import path
from apps.accounts import views


urlpatterns = [
    path("login/", views.login_view, name="login"),
    # path("logout/", views.logout_view, name="logout"),
    # path("users/create/", views.create_user, name="create_user"),
]