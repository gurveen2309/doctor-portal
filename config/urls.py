from django.urls import include, path

from clinic import views as clinic_views
from clinical import views as clinical_views
from intake import views as intake_views
from intake.doctor_views import doctor_request, priority
from operations.views import payments
from patients.views import manage

urlpatterns = [
    path("accounts/", include("accounts.urls")),
    path("patients/manage/", manage, name="manage-patients"),
    path("", clinic_views.public, name="clinic-public"),
    path("doctor/", clinic_views.workspace, name="doctor-workspace"),
    path("doctor/intake/", clinic_views.doctor_intake, name="doctor-intake"),
    path("clinic/settings/", clinic_views.settings_view, name="clinic-settings"),
    path("portal/", intake_views.portal, name="portal"),
    path("patients/<int:patient_id>/", intake_views.patient_home, name="patient-home"),
    path("patients/<int:patient_id>/request/", intake_views.new_request, name="new-request"),
    path("patients/<int:patient_id>/history/", clinical_views.history, name="clinical-history"),
    path("patients/<int:patient_id>/visits/new/", clinical_views.visit_entry, name="visit-entry"),
    path("patients/<int:patient_id>/visits/<int:visit_id>/", clinical_views.visit_entry, name="visit-revision"),
    path("patients/<int:patient_id>/payments/", payments, name="patient-payments"),
    path("requests/<int:request_id>/", intake_views.request_detail, name="request-detail"),
    path("requests/<int:request_id>/doctor/", doctor_request, name="doctor-request"),
    path("requests/<int:request_id>/priority/", priority, name="request-priority"),
    path("requests/<int:request_id>/change/", intake_views.change, name="request-change"),
    path("requests/<int:request_id>/cancel/", intake_views.cancel, name="cancel-request"),
    path("requests/<int:request_id>/information/", intake_views.information, name="add-information"),
    path("proposals/<int:proposal_id>/accept/", intake_views.accept, name="accept-proposal"),
]
