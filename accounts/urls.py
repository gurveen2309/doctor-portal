from django.urls import path

from accounts import views

urlpatterns = [
    path("login/", views.patient_login, name="patient-login"),
    path("verify/", views.verify_code, name="verify-code"),
    path("doctor-login/", views.doctor_login, name="doctor-login"),
    path("logout/", views.sign_out, name="logout"),
]
