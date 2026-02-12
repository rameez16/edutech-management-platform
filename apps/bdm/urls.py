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
                path("student_onboarding/verification/", views.students_with_uploaded_documents, name="document_verification"),
                path("student_onboarding/verification/review/<int:student_id>",views.student_document_review,name="student_document_review"),
                path("student_onboarding/verification/verify/<int:doc_id>/",views.verify_document,name="verify_document"),
                
                path("student_onboarding/enrollment_letter/", views.download_enrollment_letter, name="download_enrollment_letter"),
                path(   'bdm/enrollments/pending-verification/', views.enrollment_verification_list, name='enrollment_verification_list'),
                path("student_onboarding/enrollment_letter/<int:student_id>/", views.approve_enrollment_agreement, name="approve_enrollment_agreement"),
                
                path('bdm/student/<int:student_id>',views.view_student_id_card,name='view_student_id_card'),
                 
                path('document/<int:document_id>/reject/', views.reject_document, name='reject_document'),
                ]




