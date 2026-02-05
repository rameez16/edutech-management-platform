from django.shortcuts import redirect

def redirect_after_login(user):
    if user.role == "admin":
        return redirect("bdm/dashboard/dashboard.html")
    
    if user.role == "trainer":
        return redirect("trainer:dashboard")
    
    if user.role == "student":
        return redirect("student:stud_dashboard")
    
    return redirect("/")