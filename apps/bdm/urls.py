from django.urls import path

from . import views

app_name='bdm'



             
urlpatterns = [ path('',views.dashboard,name='bdm_dashboard'),
               
                path('leads/', views.leads, name='leads'),
                path('leads/<int:lead_id>/', views.lead_details, name='lead_details'),
                path('leads/bulk-actions/', views.bulk_leads, name='bulk_leads'),
                path('leads/create/', views.create_lead, name='create_lead'),
                path('leads/assign/', views.assign_lead, name='assign_lead'),
                path('leads/bulk-action/', views.bulk_action, name='bulk_action'),
              
               
               
               
                path('create_user/' ,views.create_user,name='create_user' ),
                path("users/", views.user_list, name="user_list"),
                
                
                path("trainer-admin/create/",views.create_trainer_admin_profile,name="trainer_admin_create" ),
                
                path("student_onboarding", views.onboarding_view, name="student_onboarding"),
                path("dashboard/trainers/", views.trainers_tab, name="document_verification"),
                path("dashboard/students/", views.students_tab, name="enrollment_letter_generation"),
                path("dashboard/trainers/", views.trainers_tab, name="id_card_generation"),
                ]


