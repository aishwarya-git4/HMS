from django.contrib import admin

from .models import (
    Patient, Staff, Appointment, StaffAuth,
    Consultation, Payment, InsurancePolicy,
    PatientInsuranceMap
)

admin.site.register(Patient)
admin.site.register(Staff)
admin.site.register(Appointment)
admin.site.register(StaffAuth)
admin.site.register(Consultation)
admin.site.register(Payment)
admin.site.register(InsurancePolicy)
admin.site.register(PatientInsuranceMap)