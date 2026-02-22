from django.shortcuts import render

# Create your views here.
from django.contrib.auth import authenticate, login,logout
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect

from apps.accounts.utils import redirect_after_login



@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect_after_login(request.user)

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_active:
            login(request, user)
            return redirect_after_login(user)

        return render(request, "accounts/login.html", {
            "error": "Invalid username or password"
        })

    return render(request, "accounts/login.html")



def logout_view(request):
    logout(request)
    return redirect("accounts:login")


from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from apps.student.models import LMSAccess

def lms_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        lms_user_id = request.POST.get("lms_user_id")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                student = user.student
                lms_access = student.lms_access

                # ✅ Verify LMS User ID
                if lms_access.lms_user_id != lms_user_id:
                    messages.error(request, "Invalid LMS User ID.")
                    return redirect("lms_login")

                # ✅ Check active
                if not lms_access.is_active:
                    messages.error(request, "LMS access is inactive.")
                    return redirect("lms_login")

                # ✅ Check expiry
                if lms_access.expiry_date and lms_access.expiry_date < timezone.now().date():
                    messages.error(request, "LMS access has expired.")
                    return redirect("lms_login")

                # ✅ Update tracking
                lms_access.last_login = timezone.now()
                lms_access.total_login_count += 1
                lms_access.save()

                login(request, user)
                return redirect("accounts:lms_dashboard")

            except LMSAccess.DoesNotExist:
                messages.error(request, "No LMS access found.")
                return redirect("accounts:lms_login")

        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "accounts/lms/login.html")




from django.contrib.auth.decorators import login_required

@login_required
def lms_dashboard(request):
    try:
        lms_access = request.user.student.lms_access
    except:
        return redirect("lms_login")

    return render(request, "accounts/lms/lms_dashboard.html", {
        "lms_access": lms_access
    })
    
    
def lms_logout(request):
    logout(request)
    return redirect("accounts:lms_login")    
    