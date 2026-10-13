from uuid import UUID

from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST
from django_otp import login as otp_login
from django_otp.plugins.otp_static.models import StaticDevice
from django_otp.plugins.otp_totp.models import TOTPDevice

from accounts.forms import CodeForm, DoctorForm, PhoneForm
from accounts.models import Account, OTPChallenge
from accounts.services import request_otp, throttle, verify_otp
from audit.services import record


@require_http_methods(["GET", "POST"])
def patient_login(request: HttpRequest) -> HttpResponse:
    form = PhoneForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            challenge = request_otp(form.cleaned_data["phone"], request.META.get("REMOTE_ADDR", "unknown"))
        except ImproperlyConfigured:
            form.add_error(None, "OTP delivery is unavailable. Contact the clinic using the phone/paper fallback.")
        except (ValidationError, OSError):
            form.add_error(None, "Unable to send a code. Wait before retrying or contact the clinic.")
        else:
            request.session["patient_challenge"] = str(challenge.pk)
            return redirect("verify-code")
    return render(request, "accounts/form.html", {"form": form, "title": "Patient sign-in"})


@require_http_methods(["GET", "POST"])
def verify_code(request: HttpRequest) -> HttpResponse:
    form = CodeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            account = verify_otp(UUID(request.session.get("patient_challenge", "")), form.cleaned_data["code"])
        except (ValueError, OTPChallenge.DoesNotExist, ValidationError):
            form.add_error(None, "Code is invalid, expired or exhausted. Request another code.")
        else:
            login(request, account, backend="django.contrib.auth.backends.ModelBackend")
            request.session.pop("patient_challenge", None)
            return redirect("/portal/")
    return render(request, "accounts/form.html", {"form": form, "title": "Verify code"})


@require_http_methods(["GET", "POST"])
def doctor_login(request: HttpRequest) -> HttpResponse:
    form = DoctorForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            throttle("doctor-source:" + request.META.get("REMOTE_ADDR", "unknown"), limit=20, seconds=600)
            throttle("doctor-user:" + form.cleaned_data["username"], limit=10, seconds=600)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            account = authenticate(
                request, username=form.cleaned_data["username"], password=form.cleaned_data["password"]
            )
            valid = False
            device = None
            if isinstance(account, Account) and account.is_doctor and account.is_active:
                with transaction.atomic():
                    model = StaticDevice if form.cleaned_data["recovery"] else TOTPDevice
                    device = model.objects.select_for_update().filter(user=account, confirmed=True).first()
                    valid = bool(device and device.verify_token(form.cleaned_data["token"]))
                    if valid:
                        record(
                            account,
                            "doctor.recovery_used" if form.cleaned_data["recovery"] else "doctor.signed_in",
                            account,
                        )
                if valid:
                    login(request, account)
                    otp_login(request, device)
                    return redirect("/doctor/")
            form.add_error(None, "Password and authenticator/recovery verification are required.")
    return render(request, "accounts/form.html", {"form": form, "title": "Doctor MFA sign-in"})


@require_POST
def sign_out(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("/")
