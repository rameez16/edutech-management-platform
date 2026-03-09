from django.urls import path

from . import views

app_name='bdm'



             
urlpatterns = [ path('',views.dashboard,name='bdm_dashboard'),
               
                path('leads/', views.leads, name='leads'),
                path('leads/<int:pk>/', views.lead_details, name='lead_details'),
                path('leads/bulk-actions/', views.bulk_leads, name='bulk_leads'),
                path('leads/create/', views.create_lead, name='create_lead'),
                path('leads/assign/', views.assign_lead, name='assign_lead'),
                path('leads/bulk-action/', views.bulk_action, name='bulk_action'),
                
                path(
    "lead/<int:pk>/update-followup/",
    views.update_lead_followup,
    name="update_lead_followup"
),
              
              path(
    "lead/<int:pk>/convert/",
    views.convert_lead_to_admission,
    name="convert_lead_to_admission"
),
               
               
               
                path('create_user/' ,views.create_user,name='create_user' ),
                path("users/", views.user_list, name="user_list"),
                
                
                # path("trainer-admin/create/",views.create_trainer_admin_profile,name="trainer_admin_create" ),
                
                path("student_onboarding", views.onboarding_view, name="student_onboarding"),
                # path("dashboard/trainers/", views.trainers_tab, name="document_verification"),
                # path("dashboard/students/", views.students_tab, name="enrollment_letter_generation"),
                # path("dashboard/trainers/", views.trainers_tab, name="id_card_generation"),
                
                path("users/<int:user_id>/", views.user_detail, name="user_profile"),
                path("users/<int:user_id>/student-admin-profile/",views.student_admin_profile_form,name="student_admin_profile_form"),
                path("users/<int:user_id>/trainer-admin-profile/",views.trainer_admin_profile_form,name="trainer_admin_profile_form"),
                


                path('batches/', views.batch_list, name='batch_list'),
                path('batches/<int:pk>/', views.batch_detail, name='batch_detail'),
                path("batches/<int:pk>/toggle-extension/",views.toggle_batch_extension,name="toggle_batch_extension"),
                path('batches/create/', views.batch_create, name='batch_create'),
                path('batch/<int:pk>/add_schedule/',views.add_batch_schedule,name='add_batch_schedule'),
                
                
                
                path("payments/",views.payments_dashboard,name="payments_dashboard"),
                path("payments/<int:pk>/",views.payment_detail,name="payment_detail"),
                path('course-fee/', views.course_fee, name='course_fee'),
                path("payment-history/<int:student_id>/", views.payment_history, name="payment_history"),



                path("student_onboarding/verification/", views.students_with_uploaded_documents, name="document_verification"),
                path("student_onboarding/verification/review/<int:student_id>",views.student_document_review,name="student_document_review"),
                path("student_onboarding/verification/verify/<int:doc_id>/",views.verify_document,name="verify_document"),
                
                path("student_onboarding/enrollment_letter/", views.download_enrollment_letter, name="download_enrollment_letter"),
                path(   'bdm/enrollments/pending-verification/', views.enrollment_verification_list, name='enrollment_verification_list'),
                path("student_onboarding/enrollment_letter/<int:student_id>/", views.approve_enrollment_agreement, name="approve_enrollment_agreement"),
                
                path('bdm/student/<int:student_id>',views.view_student_id_card,name='view_student_id_card'),      
                path('document/<int:document_id>/reject/', views.reject_document, name='reject_document'),
                
                
                #ramees-lession-plan
                
                path('academics/batches/', views.BatchListView.as_view(), name='batch_list_manage') ,
                path('academics/batch/<int:pk>/', views.BatchAcademicDashboardView.as_view(), name='batch_academic_dashboard'),
                path("academics/batch/<int:batch_id>/module/<int:pk>/",views.ModuleDetailView.as_view(),name="module_detail"),          
                path("academics/batch/<int:batch_id>/lesson-plan/<int:plan_id>/assign/",views.AssignLessonSessionView.as_view(),name="assign_lesson_session"),
                path("academics/session/<int:pk>/edit/",views.LessonSessionUpdateView.as_view(), name="edit_lesson_session"),
                path("academics/session/<int:pk>/delete/",views.LessonSessionDeleteView.as_view(),name="delete_lesson_session"),
                

                
                path('leave/', views.leave_view, name='leave'),
                path('leave/<int:pk>/', views.leave_detail, name='leave_detail'),
                
                
                path('student_feedback/', views.student_feedback, name='student_feedback'),
                
                path('courses/', views.course_list_view, name='course_list'),
                path('courses/<int:pk>/', views.course_detail_view, name='course_detail'),
                path('module/<int:pk>/', views.module_detail_view, name='module_detail'),
                path('courses/create/', views.course_create, name='course_create'),
                
                
                path("trainers/", views.trainer_list_view, name="trainer_list"),
                path("trainers/<int:pk>/", views.trainer_detail_view, name="trainer_detail"),
                
                
                path('issues/', views.student_issue_list, name='student_issue_list'),
                path('issues/<int:pk>/', views.student_issue_detail, name='student_issue_detail'),
                
                path("students/", views.StudentListView.as_view(), name="student_list"),
                path("students/<int:pk>/", views.StudentDashboardView.as_view(), name="student_dashboard"),
                
                
                path("announcements/", views.announcement_list, name="announcement_list"),
                path("announcements/create/", views.announcement_create, name="announcement_create"),
                
                path("trainer-leave/", views.trainer_leave_list, name="trainer_leave_list"),
                path("trainer-leave/<int:pk>/", views.trainer_leave_detail, name="trainer_leave_detail"),
                path("trainer-leave/<int:pk>/update/", views.update_trainer_leave_status, name="update_trainer_leave_status"),
                 
                path("exams/", views.exam_list, name="exam_list"),
                path("exams/<int:pk>/results/", views.exam_results, name="exam_results"),
                path("certificate/issue/<int:result_id>/",views.issue_certificate_single,name="issue_certificate_single"),
                path("exams/results/published/",views.published_exam_results,name="published_exam_results"),
                path("eligible-certificates/", views.eligible_certificate_list, name="eligible_certificate_list"),
               
                path('analytics/', views.analytics_report, name='analytics_report'),
                path("users/<int:user_id>/edit/",views.edit_user,name="edit_user"),
                path("users/<int:user_id>/deactivate/",views.deactivate_user,name="deactivate_user"),
                
                path("notifications/mark-all-read/",views.mark_all_notifications_read,name="mark_all_notifications_read"),
                
                path("substitute-requests/",views.substitute_request_list,name="substitute_request_list"),
                ]




