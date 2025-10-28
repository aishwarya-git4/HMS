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
    
def register_or_edit_patient(request):
    # Handles both new registration and editing existing patient
    phone = request.GET.get("phone")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Save Patient and Insurance Map
            patient = form.save()

            # STEP 1: Get latest appointment for this patient
            appointment = (
                Appointment.objects
                .filter(phone=patient.phone)
                .order_by('-preferred_date', '-preferred_time')
                .first()
            )

            if not appointment:
                # No appointment found → you can show a message
                return HttpResponse("<h3 style='text-align:center; margin-top:40px;'>No appointments found for this phone number.</h3>")

            # STEP 2: Determine base fee from department
            dept = appointment.department.lower()
            if dept == 'cardiology':
                fees = 750
            elif dept == 'ent':
                fees = 650
            elif dept == 'neurology':
                fees = 550
            elif dept == 'orthopedics':
                fees = 450
            elif dept == 'pediatrics':
                fees = 350
            else:
                fees = 300

            # STEP 3: Find insurance info (if any)
            insurance_map = PatientInsuranceMap.objects.filter(patient=patient).first()

            discount = 0
            insurance_name = None

            if insurance_map:
                policy = insurance_map.insurance
                discount = policy.discount_percent
                insurance_name = policy.company_and_policy_name

            discount_amount = fees * discount / 100
            final_amount = fees - discount_amount

            # STEP 4: Render payments page
            return render(request, 'payments.html', {
                'appointment': appointment,
                'fees': fees,
                'insurance_name': insurance_name,
                'discount': discount,
                'discount_amount': round(discount_amount, 2),
                'final_amount': round(final_amount, 2),
            })
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

def complete_payment(request, appt_id):
    """Handles payment completion and updates appointment + payment tables."""
    if request.method == "POST":
        try:
            appointment = Appointment.objects.get(pk=appt_id)
        except Appointment.DoesNotExist:
            return HttpResponse("<h3 style='text-align:center; margin-top:40px;'>Invalid appointment ID.</h3>")

        amount_original = float(request.POST.get("amount_original", 0))
        discount_amount = float(request.POST.get("discount_amount", 0))
        amount_paid = float(request.POST.get("amount_paid", 0))
        payment_method = request.POST.get("payment_method")

        # ✅ Save payment record
        Payment.objects.create(
            appointment=appointment,
            amount_original=amount_original,
            discount_amount=discount_amount,
            amount_paid=amount_paid,
            payment_method=payment_method,
        )

        # ✅ Update appointment status
        appointment.status = "confirmed"
        appointment.save()

        return HttpResponse("<h3 style='text-align:center; margin-top:40px;'>Payment successful!</h3>")

    return HttpResponse("<h3 style='text-align:center; margin-top:40px;'>Invalid request method.</h3>")

