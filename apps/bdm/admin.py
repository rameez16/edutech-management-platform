from django.contrib import admin


from .models import Lead,Course,Student,Trainer,Batch,TeleCallerProfile,TrainerAdminProfile,StudentAdminProfile,PaymentDocument,OnboardingChecklist,Notification,StudentIssue,Announcement,Admission
# Register your models here.


admin.site.register(Lead)
admin.site.register(Course)


admin.site.register(Student)
admin.site.register(StudentAdminProfile)


admin.site.register(Trainer)
admin.site.register(TrainerAdminProfile)


admin.site.register(Batch)
admin.site.register(TeleCallerProfile)

admin.site.register(PaymentDocument)
admin.site.register(OnboardingChecklist)
admin.site.register(Notification)
admin.site.register(StudentIssue)
admin.site.register(Announcement)
admin.site.register(Admission)
<<<<<<< HEAD
=======


>>>>>>> 82e73366d11bc7ae1f59bb22f762453491f071be
