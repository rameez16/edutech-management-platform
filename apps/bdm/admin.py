from django.contrib import admin

from .models import Lead,Course,Student,Trainer,Batch,TeleCallerProfile
# Register your models here.


admin.site.register(Lead)
admin.site.register(Course)
admin.site.register(Student)
admin.site.register(Trainer)
admin.site.register(Batch)
admin.site.register(TeleCallerProfile)
