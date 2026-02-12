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
                
                
                # path("trainer-admin/create/",views.create_trainer_admin_profile,name="trainer_admin_create" ),
                
                path("student_onboarding", views.onboarding_view, name="student_onboarding"),
                path("dashboard/trainers/", views.trainers_tab, name="document_verification"),
                path("dashboard/students/", views.students_tab, name="enrollment_letter_generation"),
                path("dashboard/trainers/", views.trainers_tab, name="id_card_generation"),
                
                path("users/<int:user_id>/", views.user_detail, name="user_profile"),
                path("users/<int:user_id>/student-admin-profile/",views.student_admin_profile_form,name="student_admin_profile_form"),
                path("users/<int:user_id>/trainer-admin-profile/",views.trainer_admin_profile_form,name="trainer_admin_profile_form"),

                path('batches/', views.batch_list, name='batch_list'),
                path('batches/<int:pk>/', views.batch_detail, name='batch_detail'),
                path("batches/<int:pk>/toggle-extension/",views.toggle_batch_extension,name="toggle_batch_extension"),
                path('batches/create/', views.batch_create, name='batch_create'),
                
                path("payments/",views.payments_dashboard,name="payments_dashboard"),
                path("payments/<int:pk>/",views.payment_detail,name="payment_detail"),
                path('course-fee/', views.course_fee, name='course_fee'),



                ]


