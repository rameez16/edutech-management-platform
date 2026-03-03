from django.contrib import admin

# Register your models here.

from .models import Module,LessonPlan,LessonSession,Task,TaskSubmission,SubstituteTeaching,Exam,Certificate,ExamResult,ExtensionRequest,Attendance,SessionMaterial,TrainerLeave,ExamSubmission

admin.site.register(Module)
admin.site.register(LessonPlan)
admin.site.register(LessonSession)
admin.site.register(Task)
admin.site.register(TaskSubmission)
admin.site.register(SubstituteTeaching)
admin.site.register(Exam)
admin.site.register(Certificate)
admin.site.register(ExamResult)
admin.site.register(ExtensionRequest)
admin.site.register(Attendance)
admin.site.register(SessionMaterial)
admin.site.register(ExamSubmission)

admin.site.register(TrainerLeave)