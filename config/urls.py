from django.contrib import admin
from django.urls import path

from core import views

urlpatterns = [
    path("admin/", admin.site.urls),
    # Organization
    path("api/v1/organizations/", views.organization_list, name="organization-list"),
    path("api/v1/organizations/create/", views.organization_create, name="organization-create"),
    path(
        "api/v1/organizations/<uuid:organization_id>/",
        views.organization_retrieve,
        name="organization-retrieve",
    ),
    path(
        "api/v1/organizations/<uuid:organization_id>/update/",
        views.organization_update,
        name="organization-update",
    ),
    path(
        "api/v1/organizations/<uuid:organization_id>/delete/",
        views.organization_delete,
        name="organization-delete",
    ),
    # UserProfile
    path("api/v1/profiles/", views.profile_list, name="profile-list"),
    path("api/v1/profiles/create/", views.profile_create, name="profile-create"),
    path(
        "api/v1/profiles/<uuid:profile_id>/",
        views.profile_retrieve,
        name="profile-retrieve",
    ),
    path(
        "api/v1/profiles/<uuid:profile_id>/update/",
        views.profile_update,
        name="profile-update",
    ),
    path(
        "api/v1/profiles/<uuid:profile_id>/delete/",
        views.profile_delete,
        name="profile-delete",
    ),
    # OrganizationMembershipRole
    path("api/v1/roles/", views.role_list, name="role-list"),
    path("api/v1/roles/create/", views.role_create, name="role-create"),
    path("api/v1/roles/<uuid:role_id>/", views.role_retrieve, name="role-retrieve"),
    path(
        "api/v1/roles/<uuid:role_id>/update/",
        views.role_update,
        name="role-update",
    ),
    path(
        "api/v1/roles/<uuid:role_id>/delete/",
        views.role_delete,
        name="role-delete",
    ),
    # SubscriptionLicense
    path("api/v1/licenses/", views.license_list, name="license-list"),
    path("api/v1/licenses/create/", views.license_create, name="license-create"),
    path(
        "api/v1/licenses/<uuid:license_id>/",
        views.license_retrieve,
        name="license-retrieve",
    ),
    path(
        "api/v1/licenses/<uuid:license_id>/update/",
        views.license_update,
        name="license-update",
    ),
    path(
        "api/v1/licenses/<uuid:license_id>/delete/",
        views.license_delete,
        name="license-delete",
    ),
    # Payment webhook
    path(
        "api/v1/payments/webhook/",
        views.payment_webhook,
        name="payment-webhook",
    ),
    # Individual registration
    path(
        "api/v1/register/",
        views.individual_register,
        name="individual-register",
    ),
    # Institutional registration
    path(
        "api/v1/register/institutional/",
        views.institutional_register,
        name="institutional-register",
    ),
    # Parent-child mapping
    path(
        "api/v1/parent-children/",
        views.parent_child_list,
        name="parent-child-list",
    ),
    path(
        "api/v1/parent-children/create/",
        views.parent_child_create,
        name="parent-child-create",
    ),
    path(
        "api/v1/parent-children/<uuid:link_id>/delete/",
        views.parent_child_delete,
        name="parent-child-delete",
    ),
]