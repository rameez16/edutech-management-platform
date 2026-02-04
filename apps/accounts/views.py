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


# from django.contrib.auth.decorators import login_required
# from django.shortcuts import render, redirect
# from django.contrib import messages

# from accounts.forms import TrainerStudentUserCreationForm
# from accounts.decorators import role_required
# from trainer.forms import TrainerAdminProfileForm
# from student.forms import StudentAdminProfileForm

# @login_required
# @role_required("admin")
# def create_trainer_student(request):
#     user_form = TrainerStudentUserCreationForm(request.POST or None)

#     trainer_form = TrainerAdminProfileForm(prefix="trainer")
#     student_form = StudentAdminProfileForm(prefix="student")

#     if request.method == "POST" and user_form.is_valid():
#         user = user_form.save()

#         if user.role == "trainer":
#             trainer_form = TrainerAdminProfileForm(
#                 request.POST, prefix="trainer", instance=user.trainer
#             )
#             if trainer_form.is_valid():
#                 trainer_form.save()

#         elif user.role == "student":
#             student_form = StudentAdminProfileForm(
#                 request.POST, prefix="student", instance=user.student
#             )
#             if student_form.is_valid():
#                 student_form.save()

#         messages.success(request, f"{user.role.title()} user created successfully.")
#         return redirect("admin_dashboard")

#     return render(request, "accounts/create_trainer_student.html", {
#         "user_form": user_form,
#         "trainer_form": trainer_form,
#         "student_form": student_form,
#     })
