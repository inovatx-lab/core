from functools import wraps

from django.http import JsonResponse
from django.contrib.auth import get_user_model
from .models import (
    Organization,
    UserProfile,
    OrganizationMembershipRole,
    SubscriptionLicense,
    ParentChildLink,
    Payment,
    PaymentEvent,
)


RESOURCE_MODEL_MAP = {
    "Organization": Organization,
    "UserProfile": UserProfile,
    "OrganizationMembershipRole": OrganizationMembershipRole,
    "SubscriptionLicense": SubscriptionLicense,
    "ParentChildLink": ParentChildLink,
    "Payment": Payment,
    "PaymentEvent": PaymentEvent,
}


ORG_ADMIN_ACTIONS = {"view", "create", "update"}
VIEW_ONLY_ACTIONS = {"view"}
FULL_ACTIONS = {"view", "create", "update", "delete"}
PARENT_CHILD_ACTIONS = {"view", "create", "delete"}

ORG_ADMIN_RESOURCES = {
    "Organization": ORG_ADMIN_ACTIONS,
    "UserProfile": ORG_ADMIN_ACTIONS,
    "OrganizationMembershipRole": ORG_ADMIN_ACTIONS,
    "SubscriptionLicense": ORG_ADMIN_ACTIONS,
    "ParentChildLink": PARENT_CHILD_ACTIONS,
    "Payment": VIEW_ONLY_ACTIONS,
    "PaymentEvent": VIEW_ONLY_ACTIONS,
}

VIEW_ONLY_RESOURCES = {
    "Organization": VIEW_ONLY_ACTIONS,
    "UserProfile": VIEW_ONLY_ACTIONS,
    "OrganizationMembershipRole": VIEW_ONLY_ACTIONS,
    "SubscriptionLicense": VIEW_ONLY_ACTIONS,
    "ParentChildLink": VIEW_ONLY_ACTIONS,
    "Payment": VIEW_ONLY_ACTIONS,
    "PaymentEvent": VIEW_ONLY_ACTIONS,
}

FULL_RESOURCES = {
    "Organization": FULL_ACTIONS,
    "UserProfile": FULL_ACTIONS,
    "OrganizationMembershipRole": FULL_ACTIONS,
    "SubscriptionLicense": FULL_ACTIONS,
    "ParentChildLink": PARENT_CHILD_ACTIONS,
    "Payment": FULL_ACTIONS,
    "PaymentEvent": VIEW_ONLY_ACTIONS,
}

PARENT_RESOURCES = {
    "Organization": VIEW_ONLY_ACTIONS,
    "UserProfile": VIEW_ONLY_ACTIONS,
    "OrganizationMembershipRole": VIEW_ONLY_ACTIONS,
    "SubscriptionLicense": VIEW_ONLY_ACTIONS,
    "ParentChildLink": PARENT_CHILD_ACTIONS,
    "Payment": VIEW_ONLY_ACTIONS,
    "PaymentEvent": VIEW_ONLY_ACTIONS,
}

ROLE_PERMISSIONS = {
    "org_admin": ORG_ADMIN_RESOURCES,
    "instructor": VIEW_ONLY_RESOURCES,
    "student": VIEW_ONLY_RESOURCES,
    "parent": PARENT_RESOURCES,
    "sme_staff": VIEW_ONLY_RESOURCES,
}


def _error_response(status, code, message, correlation_id=None, field=None):
    body = {
        "errors": [
            {
                "code": code,
                "message": message,
            }
        ]
    }
    if field:
        body["errors"][0]["field"] = field
    if correlation_id:
        body["correlation_id"] = str(correlation_id)
    return JsonResponse(body, status=status)


def _extract_correlation_id(request):
    return request.META.get("HTTP_X_CORRELATION_ID")


def _extract_organization_id(request):
    raw = request.META.get("HTTP_X_INOVATX_ORGANIZATION_ID")
    if not raw:
        return None
    try:
        import uuid

        return uuid.UUID(raw)
    except (ValueError, AttributeError):
        return "malformed"


def _validate_membership(auth_user, organization_id):
    """Return the UserProfile for (user, organization) or None."""
    try:
        return UserProfile.objects.select_related("organization").get(
            user=auth_user,
            organization_id=organization_id,
        )
    except UserProfile.DoesNotExist:
        return None


def _user_role_codes(user_profile):
    if user_profile is None:
        return set()
    return set(
        user_profile.role_assignments.values_list("role_code", flat=True)
    )


def _user_has_permission(user_profile, resource, action):
    """Check role-based permission for a non-superuser user profile."""
    if user_profile is None:
        return False

    role_codes = _user_role_codes(user_profile)
    resource_permissions = ROLE_PERMISSIONS.keys()

    for role_code in role_codes:
        perms = ROLE_PERMISSIONS.get(role_code, {})
        allowed_actions = perms.get(resource, set())
        if action in allowed_actions:
            return True

    return False


def _is_system_admin(auth_user):
    return auth_user is not None and getattr(auth_user, "is_superuser", False)


def require_tenant_context(view_func):
    """Decorator: authenticate, extract org selector, validate membership.

    Sets request.tenant_context with:
      - organization: the Organization instance
      - user_profile: the UserProfile for (user, organization)
      - is_system_admin: bool
      - correlation_id: UUID or None

    Returns error responses for 401, 400, 404 per P1.2.3-D1.
    """

    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        correlation_id = _extract_correlation_id(request)

        if not request.user or not request.user.is_authenticated:
            return _error_response(
                401, "unauthenticated", "Authentication required", correlation_id
            )

        org_id_raw = _extract_organization_id(request)
        if org_id_raw is None:
            return _error_response(
                400,
                "missing_organization_selector",
                "X-INOVATX-Organization-Id header is required",
                correlation_id,
            )
        if org_id_raw == "malformed":
            return _error_response(
                400,
                "invalid_organization_selector",
                "X-INOVATX-Organization-Id must be a valid UUID",
                correlation_id,
            )

        try:
            organization = Organization.objects.get(pk=org_id_raw)
        except Organization.DoesNotExist:
            return _error_response(
                404,
                "organization_not_found",
                "Organization not found or access denied",
                correlation_id,
            )

        user_profile = _validate_membership(request.user, organization.id)
        if user_profile is None:
            return _error_response(
                404,
                "membership_not_found",
                "Organization not found or access denied",
                correlation_id,
            )

        request.tenant_context = {
            "organization": organization,
            "user_profile": user_profile,
            "is_system_admin": _is_system_admin(request.user),
            "correlation_id": correlation_id,
        }

        return view_func(request, *args, **kwargs)

    return wrapped


def require_permission(resource, action):
    """Decorator: enforce role-based permission on the current tenant context.

    Must be stacked below require_tenant_context.
    system_admin (is_superuser) gets FULL_ACTIONS on all resources.
    Non-superusers are checked against ROLE_PERMISSIONS.
    Returns 403 on denial per P1.2.3-D1.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            ctx = getattr(request, "tenant_context", None)
            if ctx is None:
                return _error_response(
                    500,
                    "internal_context_missing",
                    "Tenant context not established",
                    getattr(request, "correlation_id", None),
                )

            correlation_id = ctx["correlation_id"]

            if ctx["is_system_admin"]:
                return view_func(request, *args, **kwargs)

            user_profile = ctx["user_profile"]
            if not _user_has_permission(user_profile, resource, action):
                return _error_response(
                    403,
                    "permission_denied",
                    f"Insufficient permission for {action} on {resource}",
                    correlation_id,
                    field=resource,
                )

            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator