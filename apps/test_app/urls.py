from django.urls import path

from . import views

# app_name='test_app'



urlpatterns = [path('test2',views.home_page,name='home_page'),
              path('test',views.test,name='test')]