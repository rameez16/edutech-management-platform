from django.contrib import admin

# Register your models here.


from .models import FeePayment,StudentDocument,EnrollmentAgreement,StudentIDCard,LeaveApplication,StudentFeedback,CertificationRequest,PlacementProfile,PlacementDrive,PlacementApplication

admin.site.register(FeePayment)

admin.site.register(StudentDocument)

admin.site.register(EnrollmentAgreement)

admin.site.register(StudentIDCard)

admin.site.register(LeaveApplication)

admin.site.register(StudentFeedback)

admin.site.register(CertificationRequest)

admin.site.register(PlacementProfile)

admin.site.register(PlacementDrive)

admin.site.register(PlacementApplication)