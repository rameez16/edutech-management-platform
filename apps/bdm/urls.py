from django.urls import path

from . import views

# app_name='test_app'



urlpatterns = [ path('',views.dashboard,name='home_page'),
                path('lead/<int:lead_id>/', views.lead_detail, name='lead_detail'),
                path('lead/<int:lead_id>/assign/', views.assign_lead, name='assign_lead'),]


