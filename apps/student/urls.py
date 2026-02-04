from django.urls import path

from . import views





urlpatterns = [path('stud_dashboard/',views.dashboard,name='stud_dashboard'),
               path('payment/',views.payment,name='payment'),
               path('pdc/',views.pdc,name='pdc'),
               path('emi/', views.emi, name='emi'),
               path('installments/', views.installments, name='installments'),
               path('installments_view/', views.installments_view, name='installments_view'),
               path('pdc_view/', views.pdc_view, name='pdc_view'),
               path('onetime_view/', views.onetime_view, name='onetime_view'),
               path('emi_view/', views.emi_view, name='emi_view'),
               path('profile/', views.profile, name='profile'),
               path('overview/', views.overview, name='overview'),
               path('password/', views.password, name='password'),
               path('QR_pay/', views.QR_pay, name='QR_pay'),
               path('installments_qr/', views.installments_qr, name='installments_qr'),
               
]