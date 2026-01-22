from django.urls import path

from . import views





urlpatterns = [path('dashboard/',views.dashboard,name='stud_dashboard'),
               path('index/',views.index,name='stud_index'),
               
]