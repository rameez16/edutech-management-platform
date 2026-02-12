from django.urls import path
from . import views
from .views import stud_feedback
app_name='student'

urlpatterns = [path('stud_dashboard/',views.dashboard,name='stud_dashboard'),
               path('payment/',views.payment,name='payment'),
               path('pdc/',views.pdc,name='pdc'),
               path('emi/', views.emi, name='emi'),
               path("installments/<int:student_id>/",views.installments, name="installments"),
               path("installments_view/",views.installments_view,name="installments_view"),
               path('pdc_view/', views.pdc_view, name='pdc_view'),
               path('onetime_view/', views.onetime_view, name='onetime_view'),
               path('emi_view/', views.emi_view, name='emi_view'),
               path('stud_profile/', views.stud_profile, name='stud_profile'),
               path('overview/', views.overview, name='overview'),
               path('password/', views.password, name='password'),
               path('QR_pay/', views.QR_pay, name='QR_pay'),
               path('installment/qr/<int:installment_id>/', views.install_qr, name='install_qr'),
               path('admission/',views.admission,name='admission'),
               path('stud_onboard/',views.onboard,name='stud_onboard'),
               path('stud_upload/',views.upload,name='stud_upload'),
               path('stud_feedback/', views.stud_feedback, name='stud_feedback'),
               path('lms_login/',views.lms_login,name='lms_login'),
               path('lms_dashboard/',views.lms_dashboard,name='lms_dashboard'),
               path("fees/", views.payment_gateway, name="payment_gateway"),

               
               
]