from django.shortcuts import redirect

def redirect_after_login(user):
    if user.role == "admin":
        return redirect("bdm:bdm_dashboard")
    if user.role == "trainer":
        return redirect("trainer:dashboard")
    if user.role == "student":
        return redirect("student:stud_dashboard")
    if user.role == "counselor":
        return redirect("bdm:leads")          # ← add this
    return redirect("/")