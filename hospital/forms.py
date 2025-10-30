from django.forms import ModelForm
from django import forms
from hospital.models import *
from datetime import datetime

class AppointmentForm(ModelForm):
    class Meta:
        model = Appointment
        fields = ['full_name','phone','email','department','doctor','preferred_date','preferred_time']
    def clean(self): #runs when form.is_valid() is called
        super().clean()
        return self.cleaned_data

class RegistrationForm(forms.Form):
    # --- Patient fields ---
    full_name = forms.CharField(max_length=120, label="Full Name")
    phone = forms.CharField(max_length=15, label="Phone")
    dob = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    age = forms.IntegerField(required=True)
    gender = forms.ChoiceField(
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        required=False
    )
    address = forms.CharField(widget=forms.Textarea, required=True)
    nationality = forms.CharField(max_length=50, required=True)
    occupation = forms.CharField(max_length=100, required=True)
    medical_history = forms.CharField(widget=forms.Textarea, required=False)
    blood_group = forms.ChoiceField(
        choices=[
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
            ('O+', 'O+'), ('O-', 'O-'),
        ],
        required=True
    )

    # --- Insurance fields ---
    insurance_policy = forms.ModelChoiceField(
        queryset=InsurancePolicy.objects.all(),
        required=False,
        empty_label="No insurance"
    )
    policy_number_from_card = forms.CharField(max_length=40, required=False)
    valid_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    def save(self):
        """Save or update Patient and PatientInsuranceMap."""
        cd = self.cleaned_data

        # --- Save or update Patient ---
        patient, created = Patient.objects.update_or_create(
            phone=cd['phone'],
            defaults={
                'full_name': cd['full_name'],
                'dob': cd.get('dob'),
                'age': cd.get('age'),
                'gender': cd.get('gender'),
                'address': cd.get('address'),
                'nationality': cd.get('nationality'),
                'occupation': cd.get('occupation'),
                'medical_history': cd.get('medical_history'),
                'blood_group': cd.get('blood_group'),
            }
        )

        # --- If insurance is provided ---
        insurance_policy = cd.get('insurance_policy')
        if insurance_policy:
            PatientInsuranceMap.objects.update_or_create(
                patient=patient,
                defaults={
                    'insurance': insurance_policy,
                    'policy_number_from_card': cd.get('policy_number_from_card'),
                    'valid_to': cd.get('valid_to'),
                }
            )
        else:
            # No insurance selected → delete any existing record
            PatientInsuranceMap.objects.filter(patient=patient).delete()

        return patient

    @classmethod
    def from_patient(cls, patient):
        """Pre-fill form fields from existing patient data."""
        try:
            ins_map = patient.insurance_records.select_related('insurance').first()
        except PatientInsuranceMap.DoesNotExist:
            ins_map = None

        initial = {
            "full_name": patient.full_name,
            "phone": patient.phone,
            "dob": patient.dob,
            "age": patient.age,
            "gender": patient.gender,
            "address": patient.address,
            "nationality": patient.nationality,
            "occupation": patient.occupation,
            "medical_history": patient.medical_history,
            "blood_group": patient.blood_group,
        }

        if ins_map:
            initial.update({
                "insurance_policy": ins_map.insurance,
                "policy_number_from_card": ins_map.policy_number_from_card,
                "valid_to": ins_map.valid_to,
            })

        return cls(initial=initial)