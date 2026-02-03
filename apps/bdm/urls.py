from django.urls import path

from . import views

# app_name='bdm'



urlpatterns = [path('',views.dashboard,name='home_page'),
                
              
                path('leads/', views.leads, name='leads'),
                path('leads/<int:lead_id>/', views.lead_details, name='lead_details'),
                path('leads/bulk-actions/', views.bulk_leads, name='bulk_leads'),
                path('leads/create/', views.create_lead, name='create_lead'),
                path('leads/assign/', views.assign_lead, name='assign_lead'),
                path('leads/bulk-action/', views.bulk_action, name='bulk_action'),

             ]