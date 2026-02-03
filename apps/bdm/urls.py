from django.urls import path

from . import views

# app_name='test_app'



urlpatterns = [ path('',views.dashboard,name='bdm_dashboard'),
                path('lead/<int:lead_id>/', views.lead_detail, name='lead_detail'),
                path('lead/<int:lead_id>/assign/', views.assign_lead, name='assign_lead'),
               
               
               
                path('create_user/' ,views.create_user,name='create_user' ),
                path("users/", views.user_list, name="user_list"),
                
                
                path("trainer-admin/create/",views.create_trainer_admin_profile,name="trainer_admin_create" ),
                
                path("student_onboarding", views.onboarding_view, name="student_onboarding"),
                path("dashboard/trainers/", views.trainers_tab, name="trainers_tab"),
                path("dashboard/students/", views.students_tab, name="students_tab"),
                path("dashboard/trainers/", views.trainers_tab, name="trainers_tab"),
                ]


