from django.urls import path
from . import views
from .views import stud_feedback
app_name='student'

#rinta
urlpatterns = [path('stud_dashboard/',views.dashboard,name='stud_dashboard'),
               path('payment/',views.payment,name='payment'),
               path('pdc/',views.pdc,name='pdc'),
               path('emi/', views.emi, name='emi'),
               path("installments/<int:student_id>/",views.installments, name="installments"),
               path('onetime_view/', views.onetime_view, name='onetime_view'),
               path('stud_profile/', views.stud_profile, name='stud_profile'),
               path('overview/', views.overview, name='overview'),
               path('password/', views.password, name='password'),
               path('QR_pay/', views.QR_pay, name='QR_pay'),
               path('installment/qr/<int:student_id>/<int:installment_number>/',views.install_qr,name='install_qr'),
               path('admission/',views.admission,name='admission'),
               path('stud_feedback/', views.stud_feedback, name='stud_feedback'),
               path("fees/", views.payment_gateway, name="payment_gateway"),
               path("student_attendance/", views.student_attendance, name="student_attendance"),
               path("student_leave/", views.student_leave, name="student_leave"),
               path("student_evaluation/",views.student_evaluation, name="student_evaluation"),
               path('student_issues/', views.student_issues, name='student_issues'),
               path('announcement_view/', views.announcement_view, name='announcement_view'),
               path('notification_view/', views.notification_view, name='notification_view'),
              
               
               path('payment_portal/',views.payment_portal,name='payment_portal'),
               
               
               
               
               
               
                #niranjana
                path('stud_onboard/',views.onboard,name='stud_onboard'),
                path('stud_upload/',views.upload,name='stud_upload'),
                path('stud_lessonplan/',views.lessonplan,name='stud_lessonplan'),
                path("upload-signed-enrollment-letter/",views.upload_signed_enrollment_letter,name="upload_signed_enrollment_letter"),
                path("download-id-card/",views.download_id_card,name="id_card_download"),
                path('onboarding/id-card/',views.view_id_card, name='view_id_card'),
                path('stud_syllabus/',views.syllabus,name='stud_syllabus'),
                #only for checking logic delete later for merge
                path("download-enrollment-letter/",views.download_enrollment_letter,name="download_enrollment_letter"),
                path('batch_details/', views.batch_details, name='batch_details'),
                path('stud_tasks/', views.student_tasks, name='student_tasks'),
                path("stud_tasks/<int:task_id>/", views.task_detail, name="task_detail"),
                path("stud_task/<int:task_id>/do/", views.do_task, name="do_task"),
                path('lms_dashboard/', views.lmsdashboard, name='lms_dashboard'),
                path('lms/material/<int:pk>/view/', views.lms_view_material, name='lms_view_material'),
                path('lms/material/<int:pk>/download/', views.lms_download_material, name='lms_download_material'),
                path('stud_exam/', views.exam, name='student_exam'),
                path('stud_exam/<int:exam_id>/attend/', views.attend_exam, name='attend_exam'),
                path('exam/<int:exam_id>/submit/', views.submit_exam, name='submit_exam'),


            

               
               
]



