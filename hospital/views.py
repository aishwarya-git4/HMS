from django.shortcuts import render,HttpResponse, redirect
from .forms import *
from .import views
from .models import *
from django.http import JsonResponse
from .models import *

def index(request):
    return render(request,'index.html')

def manager(request):
    return render(request,'manager.html')
def doctor(request):
    return render(request,'doctor.html')
def receptionist(request):
    return render(request,'receptionist.html')
def staff_login(request):
    role = request.GET.get("user")   

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # authenticate only among staff with selected role
        try:
            staff_auth = StaffAuth.objects.select_related("staff").get( #When you get a StaffAuth row, also fetch the related Staff row in the same query
                username=username,
                staff__role=role     
            )
        except StaffAuth.DoesNotExist: #this is raised when The .get() query could not find any row matching the filter you gave.
            return render(request, "staff_login.html", {
                "error": "Invalid credentials or role mismatch",
                "role": role,
            })

        # check password manually (you'll hash later)
        if password != staff_auth.password_hash:
            return render(request, "staff_login.html", {
                "error": "Incorrect password",
                "role": role,
            })

        
        if role == "doctor":
            return redirect("doctor")
        elif role == "manager":
            return redirect("manager")
        else:
            return redirect("receptionist")

    return render(request, "staff_login.html", {"role": role})


def user_booking(request):
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            form.save()          # saves to database
            return HttpResponse('Appointment booked')  # or render a thank-you page
    else:
        form = AppointmentForm()

    return render(request, 'user_booking.html', {'form': form})

def get_doctors(request):
    department = request.GET.get("department")
    doctors = Staff.objects.filter(role='doctor', department=department)
    data = list(doctors.values('staff_id','full_name'))   # adjust field names as per model
    return JsonResponse(data, safe=False)

def patient_by_phone(request):
    phone_number = request.GET.get("phone")
    if not phone_number:
        return JsonResponse({"error": "Phone number required"}, status=400)
    try:
        patient = (
            Patient.objects
            .prefetch_related(
                'insurance_records__insurance'
            )
            .get(phone=phone_number)
        )
        ins_map = patient.insurance_records.first()
        insurance_data = None
        if ins_map:
            insurance_data = {
                "policy_number_from_card": ins_map.policy_number_from_card,
                "valid_to": ins_map.valid_to.strftime("%Y-%m-%d") if ins_map.valid_to else None,
                "company_and_policy_name": ins_map.insurance.company_and_policy_name,
                "discount_percent": ins_map.insurance.discount_percent,
            }

        return JsonResponse({
            "exists": True,
            "patient": {
                "id": patient.patient_id,
                "full_name": patient.full_name,
                "phone": patient.phone,
                "dob": patient.dob.strftime("%Y-%m-%d") if patient.dob else None,
                "age": patient.age,
                "gender": patient.gender,
                "address": patient.address,
                "nationality": patient.nationality,
                "occupation": patient.occupation,
                "date_of_registration": patient.date_of_registration.strftime("%Y-%m-%d"),
                "medical_history": patient.medical_history,
                "blood_group": patient.blood_group,
            },
            "insurance": insurance_data
        })
    
    except Patient.DoesNotExist:
        return JsonResponse({"exists": False})
    
def register_or_edit_patient(request):
    """Handles both new registration and editing existing patient."""
    phone = request.GET.get("phone")  # for pre-filling, if any

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            patient = form.save()
            return redirect('success_page')  # or render a success message
    else:
        # Prefill form if phone exists
        form = None
        if phone:
            try:
                patient = Patient.objects.prefetch_related('insurance_records__insurance').get(phone=phone)
                form = RegistrationForm.from_patient(patient)
            except Patient.DoesNotExist:
                form = RegistrationForm()
        else:
            form = RegistrationForm()

    return render(request, 'receptionist.html', {"form": form})


