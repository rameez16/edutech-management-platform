from django.shortcuts import render

def dashboard(request):
    """Dashboard view"""
    context = {
        'page_title': 'Dashboard',
    }
    return render(request, 'trainer/dashboard.html', context)

def trainer_profile(request):
    return render(request, "trainer/profile.html")


def my_batches(request):
    return render(request, "trainer/mybatches.html")


