from django.urls import path

from . import views

app_name='landing_page'



urlpatterns = [
               path('',views.landing,name='landing'),
               path('course/<int:course_id>/', views.course_detail, name='course_detail'),]