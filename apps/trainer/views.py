from django.shortcuts import render

def dashboard(request):
    """Dashboard view"""
    context = {
        'page_title': 'Dashboard',
    }
    return render(request, 'trainer/dashboard.html', context)

