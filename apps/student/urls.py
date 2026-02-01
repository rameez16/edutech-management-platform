from django.urls import path

from . import views





urlpatterns = [path('stud_dashboard/',views.dashboard,name='stud_dashboard'),
               path('stud_onboard/',views.onboard,name='stud_onboard'),
               path('stud_upload/',views.upload,name='stud_upload'),
               
               
]