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
               path('installment/qr/<int:installment_id>/', views.install_qr, name='install_qr'),
               path('admission/',views.admission,name='admission'),
               path('stud_feedback/', views.stud_feedback, name='stud_feedback'),
               path('lms_login/',views.lms_login,name='lms_login'),
               path("fees/", views.payment_gateway, name="payment_gateway"),
               path("student_attendance/", views.student_attendance, name="student_attendance"),
               path("student_leave/", views.student_leave, name="student_leave"),
               path("student_evaluation/",views.student_evaluation, name="student_evaluation"),
              
               
               
               
               
               
               
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

               
               
]



