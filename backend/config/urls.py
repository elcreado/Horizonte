from django.urls import path

from apps.accounts.onboarding import add_company
from apps.accounts.profile import profile
from apps.accounts.recovery import recover_password, reset_password
from apps.accounts.registration import register
from apps.accounts.team import change_member, rename_company, team
from apps.accounts.views import companies, csrf, login_view, logout_view, me
from apps.banking.views import accounts, imports
from apps.classify.views import correct, delete_rule, movements, rules
from apps.forecast.history import history
from apps.forecast.obligations import (
    edit_obligation,
    obligation_history,
    obligations,
    reverse_settlement,
    settlement_candidates,
    settlements,
)
from apps.forecast.recurrences import recurrences, unlink_occurrence
from apps.forecast.views import dashboard
from apps.invoices.views import confirm_invoice, invoice_imports, invoices, link_obligation

urlpatterns = [
    path("api/auth/profile/", profile),
    path("api/companies/create/", add_company),
    path("api/companies/<int:company_id>/classification-rules/", rules),
    path("api/companies/<int:company_id>/classification-rules/<int:rule_id>/", delete_rule),
    path("api/companies/<int:company_id>/history/", history),
    path(
        "api/companies/<int:company_id>/recurrence-occurrences/<int:occurrence_id>/unlink/",
        unlink_occurrence,
    ),
    path("api/companies/<int:company_id>/recurrences/", recurrences),
    path("api/companies/<int:company_id>/team/", team),
    path("api/companies/<int:company_id>/team/<int:member_id>/", change_member),
    path("api/companies/<int:company_id>/name/", rename_company),
    path("api/auth/recover-password/", recover_password),
    path("api/auth/reset-password/", reset_password),
    path("api/auth/register/", register),
    path(
        "api/companies/<int:company_id>/invoices/<int:invoice_id>/obligation-link/", link_obligation
    ),
    path("api/companies/<int:company_id>/invoices/", invoices),
    path("api/companies/<int:company_id>/invoices/imports/", invoice_imports),
    path("api/companies/<int:company_id>/invoices/<int:invoice_id>/confirm/", confirm_invoice),
    path(
        "api/companies/<int:company_id>/obligations/<int:obligation_id>/candidates/",
        settlement_candidates,
    ),
    path("api/companies/<int:company_id>/obligations/", obligations),
    path("api/companies/<int:company_id>/obligations/<int:obligation_id>/", edit_obligation),
    path(
        "api/companies/<int:company_id>/obligations/<int:obligation_id>/settlements/", settlements
    ),
    path(
        "api/companies/<int:company_id>/obligations/<int:obligation_id>/settlements/<int:settlement_id>/reverse/",
        reverse_settlement,
    ),
    path(
        "api/companies/<int:company_id>/obligations/<int:obligation_id>/history/",
        obligation_history,
    ),
    path("api/companies/<int:company_id>/movements/", movements),
    path("api/companies/<int:company_id>/movements/<int:transaction_id>/category/", correct),
    path("api/companies/<int:company_id>/accounts/", accounts),
    path("api/companies/<int:company_id>/imports/", imports),
    path("api/auth/csrf/", csrf),
    path("api/auth/login/", login_view),
    path("api/auth/logout/", logout_view),
    path("api/auth/me/", me),
    path("api/companies/", companies),
    path("api/companies/<int:company_id>/dashboard/", dashboard),
]
