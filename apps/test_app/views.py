from django.shortcuts import render

from django.http import HttpResponse

# Create your views here.

def test(request):
    
    return render (request,'test_app/base.html')

def home_page(request):
    
    return render (request,'home.html')