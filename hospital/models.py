from django.db import models
class Patient(models.Model):
    patient_id = models.AutoField(primary_key=True)  #auto increments
    full_name = models.CharField(max_length=120)
    phone = models.CharField(
        max_length=15,
        unique=True,                  
    )
    dob = models.DateField(
        null=False, blank=False
    )
    age = models.PositiveSmallIntegerField(
        null=False, blank=False
    )   
    gender = models.CharField(
        max_length=10,
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        null=False, blank=False
    )
    address = models.TextField(
        null=False, blank=False
    )
    nationality = models.CharField(
        max_length=50,
        null=False, blank=False
    )
    occupation = models.CharField(
        max_length=100,
        null=False, blank=False
    )
    date_of_registration = models.DateTimeField(auto_now_add=True)
    medical_history = models.TextField(
        null=True, blank=True
    )
    blood_group = models.CharField(
        max_length=3,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
            ('O+', 'O+'), ('O-', 'O-'),
        ],
        null=False, blank=False
    )

class Staff(models.Model):
    staff_id = models.AutoField(primary_key=True)   
    full_name = models.CharField(
        max_length=120
    )
    phone = models.CharField(
        max_length=15,
        unique=True                 
    )
    role = models.CharField(
        max_length=20,
        choices=[
            ('manager', 'Manager'),
            ('receptionist', 'Receptionist'),
            ('doctor', 'Doctor'),
            ('nurse', 'Nurse'),
        ]
    )
    department = models.CharField(max_length=20, null=True, blank=True, choices=[
        ('Cardiology', 'Cardiology'),
        ('Orthopedics','Orthopedics'),
        ('Pediatrics', 'Pediatrics'),
        ('ENT', 'ENT'),
        ('Neurology', 'Neurology')
    ])
    salary = models.DecimalField(
        max_digits=10,              
        decimal_places=2,
        null=False, blank=False       
    )
    email = models.EmailField(
        unique=True,
        null=False, blank=False       
    )
    address = models.TextField(
        null=False, blank=False
    )
    date_joined = models.DateTimeField(
        auto_now_add=True           
    )

class Appointment(models.Model):
    appt_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=120)
    phone = models.CharField(
        max_length=15,
        unique=True,                  
    )
    email = models.EmailField(
        unique=True,
        null=False, blank=False       
    )
    department = models.CharField(
        max_length=100
    )
    doctor = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 'doctor'}
    )
    preferred_date = models.DateField()
    preferred_time = models.TimeField()

    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('cancelled', 'Cancelled'),
            ('visited', 'Visited'),
            ('no_show', 'No Show'),
        ],
        default='pending'
    )

class StaffAuth(models.Model):
    staff = models.OneToOneField(
        Staff,
        on_delete=models.CASCADE,
        primary_key=True           
    )
    username = models.CharField(
        max_length=50,
        unique=True
    )
    password_hash = models.CharField(
        max_length=128             
    )
    last_login = models.DateTimeField(
        null=True, blank=True
    )

class Consultation(models.Model):
    visit_id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='consultations'
    )
    doctor = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 'doctor'},
        related_name='consultations'
    )
    visit_datetime = models.DateTimeField(auto_now_add=True)
    symptoms = models.TextField(
        null=False, blank=False
    )
    diagnosis = models.TextField(
        null=False, blank=False
    )
    prescription = models.TextField(
        null=False, blank=False
    )
    notes = models.TextField(
        null=True, blank=True
    )

class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount_original = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    payment_method = models.CharField(
        max_length=10,
        choices=[
            ('cash', 'Cash'),
            ('card', 'Card'),
            ('upi', 'UPI'),
        ]
    )
    payment_datetime = models.DateTimeField(auto_now_add=True)

class InsurancePolicy(models.Model):
    insurance_id = models.AutoField(primary_key=True)
    company_and_policy_name = models.CharField(
        max_length=100
    )
    discount_percent = models.PositiveSmallIntegerField(
        help_text="Enter % value like 10, 20, 50"
    )
    def __str__(self):
        return self.company_and_policy_name

class PatientInsuranceMap(models.Model):
    id = models.AutoField(primary_key=True)
    patient = models.ForeignKey( #patient_id
        Patient,
        on_delete=models.CASCADE,
        related_name='insurance_records'
    )
    insurance = models.ForeignKey( #insurance_id
        InsurancePolicy,
        on_delete=models.PROTECT,     
        related_name='covered_patients'
    )
    policy_number_from_card = models.CharField(   
        max_length=40,
        null=True, blank=True
    )
    valid_to = models.DateField(
        null=True, blank=True
    )
    added_on = models.DateTimeField(auto_now_add=True)


