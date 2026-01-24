from django.urls import path

from . import views





urlpatterns = [path('stud_dashboard/',views.dashboard,name='stud_dashboard'),
               
               
]