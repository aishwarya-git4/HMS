"""
URL configuration for hms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from hospital import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.index,name='index'),
    path('user_booking/',views.user_booking,name='user_booking'),
    path('cancel_booking/',views.cancel_booking,name='cancel_booking'),
    path('patient/',views.patient,name='patient'),
    path('doctor/',views.doctor,name='doctor'),
    path('receptionist/',views.receptionist,name='receptionist'),
    path('staff_login/',views.staff_login,name='staff_login'),
    path('get-doctors/', views.get_doctors, name='get_doctors'),
    path("register_or_edit_patient/",views.register_or_edit_patient, name="register_or_edit_patient"),
    path("complete-payment/<int:appt_id>/", views.complete_payment, name="complete-payment")
    
    



]
