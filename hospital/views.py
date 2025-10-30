from django.shortcuts import render,HttpResponse, redirect
from .forms import *
from .import views
from .models import *
from django.http import JsonResponse
from .models import *

def index(request):
    return render(request,'index.html')

def patient(request):
    return render(request,'patient.html')

def cancel_booking(request):
    apptid=request.GET.get('apptid')
    if apptid:
        deleted, _ = Appointment.objects.filter(appt_id=apptid).delete()
        if deleted:
            return HttpResponse(f"Appointment ID {apptid} deleted successfully.")
        else:
            return HttpResponse("No appointment found with that ID.", status=404)        
    else:
        return render(request,'cancel_booking.html')

def manager(request):
    return render(request,'manager.html')
def doctor(request):
    """Doctor dashboard with consultation form"""
    staff_id = request.session.get("staff_id")

    if not staff_id:
        return redirect("staff_login")

    doctor = Staff.objects.get(staff_id=staff_id)

    if request.method == "POST":
        patient_id = request.POST.get("patient_id")
        symptoms = request.POST.get("symptoms")
        diagnosis = request.POST.get("diagnosis")
        prescription = request.POST.get("prescription")
        notes = request.POST.get("notes")

        try:
            # ✅ Get the patient by ID
            patient = Patient.objects.get(patient_id=patient_id)
        except Patient.DoesNotExist:
            return HttpResponse("<h3 style='text-align:center;'>Invalid patient ID</h3>")

        # ✅ Create Consultation record
        Consultation.objects.create(
            patient=patient,
            doctor=doctor,
            symptoms=symptoms,
            diagnosis=diagnosis,
            prescription=prescription,
            notes=notes,
        )

        # ✅ Find the latest appointment using the phone number (since no FK exists)
        latest_appointment = Appointment.objects.filter(
            phone=patient.phone
        ).order_by('-preferred_date').first()

        if latest_appointment:
            latest_appointment.status = "visited"
            latest_appointment.save()

        return HttpResponse("<h3 style='text-align:center;'>Consultation saved successfully!</h3>")

    return render(request, "doctor.html", {"doctor": doctor})

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
        
        request.session["staff_id"] = staff_auth.staff.staff_id
        request.session["staff_role"] = staff_auth.staff.role

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
            appointment = form.save()  # save and get the created object
            return HttpResponse(f"Appointment booked successfully! Your Appointment ID is {appointment.appt_id}.")
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
                .filter(phone=patient.phone, status='pending')
                .order_by('-preferred_date', '-preferred_time')
                .first()
            )

            if not appointment:#just an extra check
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
            appointment = (
                Appointment.objects
                .filter(phone=phone, status='pending')
                .order_by('-preferred_date', '-preferred_time')
                .first()
            )

            if not appointment:
                # No appointment found → you can show a message
                return HttpResponse("<h3 style='text-align:center; margin-top:40px;'>No appointments found for this phone number.</h3>")
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

