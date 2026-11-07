import json

from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils.decorators import method_decorator
from functools import wraps

from .models import (
    Organization,
    UserProfile,
    OrganizationMembershipRole,
    SubscriptionLicense,
    ParentChildLink,
    OrganizationType,
    OrganizationStatus,
    MembershipRoleCode,
    SubscriptionProductCode,
    LicenseStatus,
)
from .permissions import (
    require_tenant_context,
    require_permission,
    _error_response,
    _extract_correlation_id,
    _extract_organization_id,
    _validate_membership,
    _is_system_admin,
    ROLE_PERMISSIONS,
)


def _model_to_dict(instance, fields):
    data = {}
    for field in fields:
        value = getattr(instance, field)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        elif hasattr(value, "hex"):
            value = str(value)
        elif hasattr(value, "pk"):
            value = value.pk
        data[field] = value
    return data


ORG_FIELDS = ("id", "name", "org_type", "status", "created_at", "updated_at")
PROFILE_FIELDS = ("id", "user", "organization", "phone_number", "created_at", "updated_at")
ROLE_FIELDS = ("id", "user_profile", "role_code", "created_at", "updated_at")
LICENSE_FIELDS = (
    "id",
    "organization",
    "product_code",
    "seat_capacity",
    "moodle_cohort_id",
    "status",
    "ai_monthly_interaction_allowance_per_learner_seat",
    "ai_daily_interaction_cap_per_learner_seat",
    "valid_until",
    "created_at",
    "updated_at",
)


def _parse_body(request):
    try:
        return json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------- Organization

@require_http_methods(["GET"])
@require_tenant_context
@require_permission("Organization", "view")
def organization_list(request):
    ctx = request.tenant_context
    orgs = Organization.objects.filter(id=ctx["organization"].id)
    data = [_model_to_dict(o, ORG_FIELDS) for o in orgs]
    return JsonResponse(
        {"data": data, "correlation_id": str(ctx["correlation_id"])},
        status=200,
    )


@require_http_methods(["POST"])
@require_tenant_context
@require_permission("Organization", "create")
def organization_create(request):
    ctx = request.tenant_context
    correlation_id = ctx["correlation_id"]
    body = _parse_body(request)
    if body is None:
        return _error_response(400, "invalid_json", "Request body must be valid JSON", correlation_id)

    name = body.get("name")
    org_type = body.get("org_type")
    status = body.get("status")

    if not name or not org_type or not status:
        return _error_response(
            400, "missing_fields", "name, org_type, and status are required", correlation_id
        )

    try:
        organization = Organization.objects.create(
            name=name,
            org_type=org_type,
            status=status,
        )
    except (ValidationError, IntegrityError) as exc:
        return _error_response(400, "creation_failed", str(exc), correlation_id)

    return JsonResponse(
        {
            "data": _model_to_dict(organization, ORG_FIELDS),
            "correlation_id": str(correlation_id),
        },
        status=201,
    )


@require_http_methods(["GET"])
@require_tenant_context
@require_permission("Organization", "view")
def organization_retrieve(request, organization_id):
    ctx = request.tenant_context
    correlation_id = ctx["correlation_id"]

    try:
        organization = Organization.objects.get(pk=organization_id)
    except Organization.DoesNotExist:
        return _error_response(404, "organization_not_found", "Organization not found", correlation_id)

    if str(organization.id) != str(ctx["organization"].id):
        return _error_response(403, "permission_denied", "Access to another organization is denied", correlation_id)

    return JsonResponse(
        {
            "data": _model_to_dict(organization, ORG_FIELDS),
            "correlation_id": str(correlation_id),
        },
        status=200,
    )


@require_http_methods(["PUT", "PATCH"])
@require_tenant_context
@require_permission("Organization", "update")
def organization_update(request, organization_id):
    ctx = request.tenant_context
    correlation_id = ctx["correlation_id"]

    try:
        organization = Organization.objects.get(pk=organization_id)
    except Organization.DoesNotExist:
        return _error_response(404, "organization_not_found", "Organization not found", correlation_id)

    if str(organization.id) != str(ctx["organization"].id):
        return _error_response(403, "permission_denied", "Access to another organization is denied", correlation_id)

    body = _parse_body(request)
    if body is None:
        return _error_response(400, "invalid_json", "Request body must be valid JSON", correlation_id)

    if "name" in body:
        organization.name = body["name"]
    if "org_type" in body:
        organization.org_type = body["org_type"]
    if "status" in body:
        organization.status = body["status"]

    try:
        organization.full_clean()
        organization.save()
    except (ValidationError, IntegrityError) as exc:
        return _error_response(400, "update_failed", str(exc), correlation_id)

    return JsonResponse(
        {
            "data": _model_to_dict(organization, ORG_FIELDS),
            "correlation_id": str(correlation_id),
        },
        status=200,
    )


@require_http_methods(["DELETE"])
@require_tenant_context
@require_permission("Organization", "delete")
def organization_delete(request, organization_id):
    ctx = request.tenant_context
    correlation_id = ctx["correlation_id"]

    try:
        organization = Organization.objects.get(pk=organization_id)
    except Organization.DoesNotExist:
        return _error_response(404, "organization_not_found", "Organization not found", correlation_id)

    if str(organization.id) != str(ctx["organization"].id):
        return _error_response(403, "permission_denied", "Access to another organization is denied", correlation_id)

    organization.delete()
    return JsonResponse(
        {"data": None, "correlation_id": str(correlation_id)},
        status=204,
    )


# ---------------------------------------------------------------- UserProfile

@require_http_methods(["GET"])
@require_tenant_context
@require_permission("UserProfile", "view")
def profile_list(request):
    ctx = request.tenant_context
    profiles = UserProfile.objects.filter(organization=ctx["organization"]).select_related("user")
    data = [_model_to_dict(p, PROFILE_FIELDS) for p in profiles]
    return JsonResponse(
        {"data": data, "correlation_id": str(ctx["correlation_id"])},
        status=200,
    )


@require_http_methods(["POST"])
@require_tenant_context
@require_permission("UserProfile", "create")
def profile_create(request):
    ctx = request.tenant_context
    correlation_id = ctx["correlation_id"]
    body = _parse_body(request)
    if body is None:
        return _error_response(400, "invalid_json", "Request body must be valid JSON", correlation_id)

    user_id = body.get("user")
    phone_number = body.get("phone_number")

    if not user_id or not phone_number:
        return _error_response(
            400, "missing_fields", "user and phone_number are required", correlation_id
        )

    User = get_user_model()
    try:
        auth_user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return _error_response(404, "user_not_found", "User not found", correlation_id)

    try:
        profile = UserProfile.objects.create(
            user=auth_user,
            organization=ctx["organization"],
            phone_number=phone_number,
        )
    except (ValidationError, IntegrityError) as exc:
        return _error_response(400, "creation_failed", str(exc), correlation_id)

    return JsonResponse(
        {
            "data": _model_to_dict(profile, PROFILE_FIELDS),
            "correlation_id": str(correlation_id),
        },
        status=201,
    )


@require_http_methods(["GET"])
@require_tenant_context
@require_permission("UserProfile", "view")
def profile_retrieve(request, profile_id):
    ctx = request.tenant_context
    correlation_id = ctx["correlation_id"]

    try:
        profile = UserProfile.objects.select_related("user").get(pk=profile_id)
    except UserProfile.DoesNotExist:
        return _error_response(404, "profile_not_found", "User profile not found", correlation_id)

    if str(profile.organization_id) != str(ctx["organization"].id):
        return _error_response(403, "permission_denied", "Access to another organization's profile is denied", correlation_id)

    return JsonResponse(
        {
            "data": _model_to_dict(profile, PROFILE_FIELDS),
            "correlation_id": str(correlation_id),
        },
        status=200,
    )


@require_http_methods(["PUT", "PATCH"])
@require_tenant_context
@require_permission("UserProfile", "update")
def profile_update(request, profile_id):
    ctx = request.tenant_context
    correlation_id = ctx["correlation_id"]

    try:
        profile = UserProfile.objects.get(pk=profile_id)
    except UserProfile.DoesNotExist:
        return _error_response(404, "profile_not_found", "User profile not found", correlation_id)

    if str(profile.organization_id) != str(ctx["organization"].id):
        return _error_response(403, "permission_denied", "Access to another organization's profile is denied", correlation_id)

    body = _parse_body(request)
    if body is None:
        return _error_response(400, "invalid_json", "Request body must be valid JSON", correlation_id)

    if "phone_number" in body:
        profile.phone_number = body["phone_number"]

    try:
        profile.full_clean()
        profile.save()
    except (ValidationError, IntegrityError) as exc:
        return _error_response(400, "update_failed", str(exc), correlation_id)

    return JsonResponse(
        {
            "data": _model_to_dict(profile, PROFILE_FIELDS),
            "correlation_id": str(correlation_id),
        },
        status=200,
    )


@require_http_methods(["DELETE"])
@require_tenant_context
@require_permission("UserProfile", "delete")
def profile_delete(request, profile_id):
    ctx = request.tenant_context
    correlation_id = ctx["correlation_id"]

    try:
        profile = UserProfile.objects.get(pk=profile_id)
    except UserProfile.DoesNotExist:
        return _error_response(404, "profile_not_found", "User profile not found", correlation_id)

    if str(profile.organization_id) != str(ctx["organization"].id):
        return _error_response(403, "permission_denied", "Access to another organization's profile is denied", correlation_id)

    profile.delete()
    return JsonResponse(
        {"data": None, "correlation_id": str(correlation_id)},
        status=204,
    )


# ------------------------------------------------- OrganizationMembershipRole

@require_http_methods(["GET"])
@require_tenant_context
@require_permission("OrganizationMembershipRole", "view")
def role_list(request):
    ctx = request.tenant_context
    roles = (
        OrganizationMembershipRole.objects.filter(
            user_profile__organization=ctx["organization"]
        )
        .select_related("user_profile", "user_profile__user")
    )
    data = [_model_to_dict(r, ROLE_FIELDS) for r in roles]
    return JsonResponse(
        {"data": data, "correlation_id": str(ctx["correlation_id"])},
        status=200,
    )


@require_http_methods(["POST"])
@require_tenant_context
@require_permission("OrganizationMembershipRole", "create")
def role_create(request):
    ctx = request.tenant_context
    correlation_id = ctx["correlation_id"]
    body = _parse_body(request)
    if body is None:
        return _error_response(400, "invalid_json", "Request body must be valid JSON", correlation_id)

    user_profile_id = body.get("user_profile")
    role_code = body.get("role_code")

    if not user_profile_id or not role_code:
        return _error_response(
            400, "missing_fields", "user_profile and role_code are required", correlation_id
        )

    try:
        user_profile = UserProfile.objects.get(
            pk=user_profile_id, organization=ctx["organization"]
        )
    except UserProfile.DoesNotExist:
        return _error_response(
            404, "profile_not_found", "User profile not found in this organization", correlation_id
        )

    try:
        role = OrganizationMembershipRole.objects.create(
            user_profile=user_profile,
            role_code=role_code,
        )
    except (ValidationError, IntegrityError) as exc:
        return _error_response(400, "creation_failed", str(exc), correlation_id)

    return JsonResponse(
        {
            "data": _model_to_dict(role, ROLE_FIELDS),
            "correlation_id": str(correlation_id),
        },
        status=201,
    )


@require_http_methods(["GET"])
@require_tenant_context
@require_permission("OrganizationMembershipRole", "view")
def role_retrieve(request, role_id):
    ctx = request.tenant_context
    correlation_id = ctx["correlation_id"]

    try:
        role = OrganizationMembershipRole.objects.select_related(
            "user_profile", "user_profile__user"
        ).get(pk=role_id)
    except OrganizationMembershipRole.DoesNotExist:
        return _error_response(404, "role_not_found", "Membership role not found", correlation_id)

    if str(role.user_profile.organization_id) != str(ctx["organization"].id):
        return _error_response(
            403, "permission_denied", "Access to another organization's role is denied", correlation_id
        )

    return JsonResponse(
        {
            "data": _model_to_dict(role, ROLE_FIELDS),
            "correlation_id": str(correlation_id),
        },
        status=200,
    )


@require_http_methods(["PUT", "PATCH"])
@require_tenant_context
@require_permission("OrganizationMembershipRole", "update")
def role_update(request, role_id):
    ctx = request.tenant_context
    correlation_id = ctx["correlation_id"]

    try:
        role = OrganizationMembershipRole.objects.get(pk=role_id)
    except OrganizationMembershipRole.DoesNotExist:
        return _error_response(404, "role_not_found", "Membership role not found", correlation_id)

    if str(role.user_profile.organization_id) != str(ctx["organization"].id):
        return _error_response(
            403, "permission_denied", "Access to another organization's role is denied", correlation_id
        )

    body = _parse_body(request)
    if body is None:
        return _error_response(400, "invalid_json", "Request body must be valid JSON", correlation_id)

    if "role_code" in body:
        role.role_code = body["role_code"]

    try:
        role.full_clean()
        role.save()
    except (ValidationError, IntegrityError) as exc:
        return _error_response(400, "update_failed", str(exc), correlation_id)

    return JsonResponse(
        {
            "data": _model_to_dict(role, ROLE_FIELDS),
            "correlation_id": str(correlation_id),
        },
        status=200,
    )


@require_http_methods(["DELETE"])
@require_tenant_context
@require_permission("OrganizationMembershipRole", "delete")
def role_delete(request, role_id):
    ctx = request.tenant_context
    correlation_id = ctx["correlation_id"]

    try:
        role = OrganizationMembershipRole.objects.get(pk=role_id)
    except OrganizationMembershipRole.DoesNotExist:
        return _error_response(404, "role_not_found", "Membership role not found", correlation_id)

    if str(role.user_profile.organization_id) != str(ctx["organization"].id):
        return _error_response(
            403, "permission_denied", "Access to another organization's role is denied", correlation_id
        )

    role.delete()
    return JsonResponse(
        {"data": None, "correlation_id": str(correlation_id)},
        status=204,
    )


# ---------------------------------------------------------------- SubscriptionLicense

@require_http_methods(["GET"])
@require_tenant_context
@require_permission("SubscriptionLicense", "view")
def license_list(request):
    ctx = request.tenant_context
    licenses = SubscriptionLicense.objects.filter(organization=ctx["organization"])
    data = [_model_to_dict(l, LICENSE_FIELDS) for l in licenses]
    return JsonResponse(
        {"data": data, "correlation_id": str(ctx["correlation_id"])},
        status=200,
    )


@require_http_methods(["POST"])
@require_tenant_context
@require_permission("SubscriptionLicense", "create")
def license_create(request):
    ctx = request.tenant_context
    correlation_id = ctx["correlation_id"]
    body = _parse_body(request)
    if body is None:
        return _error_response(400, "invalid_json", "Request body must be valid JSON", correlation_id)

    product_code = body.get("product_code")
    seat_capacity = body.get("seat_capacity")
    status = body.get("status")

    if not product_code or seat_capacity is None or not status:
        return _error_response(
            400, "missing_fields", "product_code, seat_capacity, and status are required", correlation_id
        )

    try:
        license_record = SubscriptionLicense.objects.create(
            organization=ctx["organization"],
            product_code=product_code,
            seat_capacity=seat_capacity,
            status=status,
            moodle_cohort_id=body.get("moodle_cohort_id"),
            ai_monthly_interaction_allowance_per_learner_seat=body.get(
                "ai_monthly_interaction_allowance_per_learner_seat"
            ),
            ai_daily_interaction_cap_per_learner_seat=body.get(
                "ai_daily_interaction_cap_per_learner_seat"
            ),
            valid_until=body.get("valid_until"),
        )
    except (ValidationError, IntegrityError) as exc:
        return _error_response(400, "creation_failed", str(exc), correlation_id)

    return JsonResponse(
        {
            "data": _model_to_dict(license_record, LICENSE_FIELDS),
            "correlation_id": str(correlation_id),
        },
        status=201,
    )


@require_http_methods(["GET"])
@require_tenant_context
@require_permission("SubscriptionLicense", "view")
def license_retrieve(request, license_id):
    ctx = request.tenant_context
    correlation_id = ctx["correlation_id"]

    try:
        license_record = SubscriptionLicense.objects.get(pk=license_id)
    except SubscriptionLicense.DoesNotExist:
        return _error_response(404, "license_not_found", "Subscription license not found", correlation_id)

    if str(license_record.organization_id) != str(ctx["organization"].id):
        return _error_response(
            403, "permission_denied", "Access to another organization's license is denied", correlation_id
        )

    return JsonResponse(
        {
            "data": _model_to_dict(license_record, LICENSE_FIELDS),
            "correlation_id": str(correlation_id),
        },
        status=200,
    )


@require_http_methods(["PUT", "PATCH"])
@require_tenant_context
@require_permission("SubscriptionLicense", "update")
def license_update(request, license_id):
    ctx = request.tenant_context
    correlation_id = ctx["correlation_id"]

    try:
        license_record = SubscriptionLicense.objects.get(pk=license_id)
    except SubscriptionLicense.DoesNotExist:
        return _error_response(404, "license_not_found", "Subscription license not found", correlation_id)

    if str(license_record.organization_id) != str(ctx["organization"].id):
        return _error_response(
            403, "permission_denied", "Access to another organization's license is denied", correlation_id
        )

    body = _parse_body(request)
    if body is None:
        return _error_response(400, "invalid_json", "Request body must be valid JSON", correlation_id)

    updatable = (
        "product_code",
        "seat_capacity",
        "moodle_cohort_id",
        "status",
        "ai_monthly_interaction_allowance_per_learner_seat",
        "ai_daily_interaction_cap_per_learner_seat",
        "valid_until",
    )
    for field in updatable:
        if field in body:
            setattr(license_record, field, body[field])

    try:
        license_record.full_clean()
        license_record.save()
    except (ValidationError, IntegrityError) as exc:
        return _error_response(400, "update_failed", str(exc), correlation_id)

    return JsonResponse(
        {
            "data": _model_to_dict(license_record, LICENSE_FIELDS),
            "correlation_id": str(correlation_id),
        },
        status=200,
    )


@require_http_methods(["DELETE"])
@require_tenant_context
@require_permission("SubscriptionLicense", "delete")
def license_delete(request, license_id):
    ctx = request.tenant_context
    correlation_id = ctx["correlation_id"]

    try:
        license_record = SubscriptionLicense.objects.get(pk=license_id)
    except SubscriptionLicense.DoesNotExist:
        return _error_response(404, "license_not_found", "Subscription license not found", correlation_id)

    if str(license_record.organization_id) != str(ctx["organization"].id):
        return _error_response(
            403, "permission_denied", "Access to another organization's license is denied", correlation_id
        )

    license_record.delete()
    return JsonResponse(
        {"data": None, "correlation_id": str(correlation_id)},
        status=204,
    )


# ---------------------------------------------------------------- Payment webhook

import hmac
import hashlib

from django.views.decorators.csrf import csrf_exempt

from .models import (
    Payment,
    PaymentEvent,
    PaymentStatus,
    PaymentEventType,
    PaymentGatewayCode,
)


def _verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 webhook signature."""
    if not signature or not secret:
        return False
    try:
        scheme, _, hex_digest = signature.partition("=")
        if scheme.lower() not in ("hmac-sha256", "sha256"):
            return False
        expected = hmac.new(
            secret.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, hex_digest)
    except (ValueError, AttributeError):
        return False


@csrf_exempt
@require_http_methods(["POST"])
def payment_webhook(request):
    """Webhook endpoint for payment gateway receipts.

    Receives payment event notifications from external payment gateways.
    Validates signature, enforces idempotency, records Payment and
    PaymentEvent, and activates/suspends SubscriptionLicense per the
    license lifecycle policy (Task 2.2.1) and payment state model
    (Task 2.2.2).

    This endpoint is CSRF-exempt because it is called by external
    gateways, not by authenticated users. Security is provided by
    cryptographic signature verification.
    """
    correlation_id = _extract_correlation_id(request)

    # Signature verification
    signature = request.META.get("HTTP_X_INOVATX_SIGNATURE", "")
    secret = __import__("os").environ.get("INOVATX_WEBHOOK_SECRET", "")
    if not _verify_webhook_signature(request.body, signature, secret):
        return _error_response(
            401, "invalid_signature", "Webhook signature verification failed", correlation_id
        )

    # Parse JSON body
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return _error_response(400, "invalid_json", "Request body must be valid JSON", correlation_id)

    # Validate required fields
    required_fields = (
        "event_id",
        "event_type",
        "organization_id",
        "idempotency_key",
    )
    for field in required_fields:
        if field not in body:
            return _error_response(
                400, "missing_field", f"Required field missing: {field}", correlation_id
            )

    event_id = body["event_id"]
    event_type = body["event_type"]
    organization_id = body["organization_id"]
    license_id = body.get("license_id")
    idempotency_key = body["idempotency_key"]

    # Validate event type
    try:
        PaymentEventType(event_type)
    except ValueError:
        return _error_response(
            400, "invalid_event_type", f"Unknown event type: {event_type}", correlation_id
        )

    # Idempotency: reject duplicate event_id
    if PaymentEvent.objects.filter(event_id=event_id).exists():
        return JsonResponse(
            {
                "data": {"status": "duplicate", "event_id": str(event_id)},
            "correlation_id": str(correlation_id),
        },
        status=200,
    )

    # Validate organization exists
    try:
        organization = Organization.objects.get(pk=organization_id)
    except Organization.DoesNotExist:
        return _error_response(404, "organization_not_found", "Organization not found", correlation_id)

    # Validate license if provided
    license_record = None
    if license_id is not None:
        try:
            license_record = SubscriptionLicense.objects.get(
                pk=license_id, organization=organization
            )
        except SubscriptionLicense.DoesNotExist:
            return _error_response(
                404, "license_not_found", "License not found in this organization", correlation_id
            )

    # Determine payment status from event type
    status_map = {
        PaymentEventType.SUCCEEDED: PaymentStatus.SUCCEEDED,
        PaymentEventType.FAILED: PaymentStatus.FAILED,
        PaymentEventType.CANCELLED: PaymentStatus.CANCELLED,
        PaymentEventType.INITIATED: PaymentStatus.PENDING,
    }
    payment_status = status_map.get(event_type, PaymentStatus.PENDING)

    # Create or update Payment record (idempotent by idempotency_key)
    payment, created = Payment.objects.get_or_create(
        idempotency_key=idempotency_key,
        defaults={
            "organization": organization,
            "license": license_record,
            "amount": body.get("amount", 0),
            "currency": body.get("currency", "USD"),
            "gateway": body.get("gateway", PaymentGatewayCode.MOBILE_MONEY),
            "gateway_reference": body.get("gateway_reference"),
            "status": payment_status,
        },
    )

    if not created:
        # Payment already exists for this idempotency key; update status if needed
        payment.status = payment_status
        if license_record is not None:
            payment.license = license_record
        payment.save()

    # Create PaymentEvent record
    PaymentEvent.objects.create(
        payment=payment,
        event_type=event_type,
        event_id=event_id,
        payload=body,
    )

    # Activate or suspend license based on payment outcome
    if event_type == PaymentEventType.SUCCEEDED and license_record is not None:
        if license_record.status == LicenseStatus.PENDING:
            try:
                license_record.status = LicenseStatus.ACTIVE
                license_record.full_clean()
                license_record.save()
            except ValidationError as exc:
                return _error_response(
                    400, "activation_failed", str(exc), correlation_id
                )

    if event_type == PaymentEventType.FAILED and license_record is not None:
        if license_record.status == LicenseStatus.PENDING:
            license_record.status = LicenseStatus.SUSPENDED
            license_record.save()

    return JsonResponse(
        {
            "data": {
                "payment_id": str(payment.id),
                "payment_status": payment.status,
                "license_status": license_record.status if license_record else None,
                "event_id": str(event_id),
            },
            "correlation_id": str(correlation_id),
        },
        status=200,
    )


# ---------------------------------------------------------------- Institutional registration

@csrf_exempt
@require_http_methods(["POST"])
def institutional_register(request):
    """Institutional registration endpoint.

    Creates a new user, organization (school/sme/ngo/enterprise type, pending),
    user profile, organization membership role (org_admin), and a pending
    subscription license with institutional seat capacity.

    No tenant context is required — the user does not yet belong to an
    organization. The endpoint is open (no authentication required) and secured
    by input validation and unique constraints.

    Institutional org types: school, sme, ngo, enterprise.
    Individual org type is handled by individual_register (Task 2.3.1).
    """
    correlation_id = _extract_correlation_id(request)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return _error_response(400, "invalid_json", "Request body must be valid JSON", correlation_id)

    # Validate required fields
    required_fields = ("username", "password", "email", "phone_number",
                       "organization_name", "organization_type")
    for field in required_fields:
        if not body.get(field):
            return _error_response(
                400, "missing_field", f"Required field missing: {field}", correlation_id,
                field=field,
            )

    username = body["username"]
    password = body["password"]
    email = body["email"]
    phone_number = body["phone_number"]
    org_name = body["organization_name"]
    org_type = body["organization_type"]

    # Validate org_type is institutional (not individual)
    institutional_types = {
        OrganizationType.SCHOOL, OrganizationType.SME,
        OrganizationType.NGO, OrganizationType.ENTERPRISE,
    }
    if org_type not in institutional_types:
        return _error_response(
            400, "invalid_org_type",
            f"Organization type '{org_type}' is not institutional. "
            f"Use individual_register for individual accounts.",
            correlation_id, field="organization_type",
        )

    User = get_user_model()

    # Check for duplicate username/email
    if User.objects.filter(username=username).exists():
        return _error_response(409, "duplicate_username", "Username already taken", correlation_id, field="username")
    if User.objects.filter(email=email).exists():
        return _error_response(409, "duplicate_email", "Email already registered", correlation_id, field="email")

    try:
        with transaction.atomic():
            # Create Django user
            auth_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )

            # Create organization (institutional, pending)
            organization = Organization.objects.create(
                name=org_name,
                org_type=org_type,
                status=OrganizationStatus.PENDING,
            )

            # Create user profile
            profile = UserProfile.objects.create(
                user=auth_user,
                organization=organization,
                phone_number=phone_number,
            )

            # Create org_admin role assignment
            OrganizationMembershipRole.objects.create(
                user_profile=profile,
                role_code=MembershipRoleCode.ORG_ADMIN,
            )

            # Create pending subscription license (institutional seat capacity)
            seat_capacity = body.get("seat_capacity", 50)
            license_record = SubscriptionLicense.objects.create(
                organization=organization,
                product_code=SubscriptionProductCode.EDTECH_LMS,
                seat_capacity=seat_capacity,
                status=LicenseStatus.PENDING,
            )

    except (ValidationError, IntegrityError) as exc:
        return _error_response(400, "registration_failed", str(exc), correlation_id)

    return JsonResponse(
        {
            "data": {
                "user_id": str(auth_user.id),
                "username": auth_user.username,
                "email": auth_user.email,
                "organization_id": str(organization.id),
                "organization_name": organization.name,
                "organization_type": organization.org_type,
                "organization_status": organization.status,
                "profile_id": str(profile.id),
                "role_code": MembershipRoleCode.ORG_ADMIN,
                "license_id": str(license_record.id),
                "license_status": license_record.status,
                "seat_capacity": license_record.seat_capacity,
            },
            "correlation_id": str(correlation_id),
        },
        status=201,
    )


# ---------------------------------------------------------------- Parent-child mapping

@require_http_methods(["GET"])
@require_tenant_context
@require_permission("ParentChildLink", "view")
def parent_child_list(request):
    """List child links for the authenticated parent within the tenant context."""
    ctx = request.tenant_context
    correlation_id = ctx["correlation_id"]

    links = (
        ParentChildLink.objects.filter(parent_profile=ctx["user_profile"])
        .select_related("child_profile", "child_profile__user")
    )
    data = [
        {
            "link_id": str(link.id),
            "child_profile_id": str(link.child_profile.id),
            "child_user_id": str(link.child_profile.user.id),
            "child_username": link.child_profile.user.username,
            "child_email": link.child_profile.user.email,
            "child_phone_number": link.child_profile.phone_number,
            "created_at": link.created_at.isoformat(),
        }
        for link in links
    ]
    return JsonResponse(
        {"data": data, "correlation_id": str(correlation_id)},
        status=200,
    )


@require_http_methods(["POST"])
@require_tenant_context
@require_permission("ParentChildLink", "create")
def parent_child_create(request):
    """Create a parent-child link within the tenant context.

    Both parent_profile and child_profile must belong to the same organization.
    The authenticated user must be the parent_profile.
    """
    ctx = request.tenant_context
    correlation_id = ctx["correlation_id"]

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return _error_response(400, "invalid_json", "Request body must be valid JSON", correlation_id)

    child_profile_id = body.get("child_profile_id")

    if not child_profile_id:
        return _error_response(
            400, "missing_field", "Required field missing: child_profile_id", correlation_id,
            field="child_profile_id",
        )

    # Verify child profile exists in the same organization
    try:
        child_profile = UserProfile.objects.get(
            pk=child_profile_id, organization=ctx["organization"]
        )
    except UserProfile.DoesNotExist:
        return _error_response(
            404, "profile_not_found", "Child profile not found in this organization", correlation_id
        )

    # Parent cannot link to themselves
    if str(child_profile.id) == str(ctx["user_profile"].id):
        return _error_response(
            400, "self_link_not_allowed", "A parent cannot link to themselves", correlation_id,
            field="child_profile_id",
        )

    try:
        with transaction.atomic():
            link = ParentChildLink.objects.create(
                parent_profile=ctx["user_profile"],
                child_profile=child_profile,
            )
    except IntegrityError as exc:
        return _error_response(400, "link_already_exists", str(exc), correlation_id)

    return JsonResponse(
        {
            "data": {
                "link_id": str(link.id),
                "parent_profile_id": str(link.parent_profile.id),
                "child_profile_id": str(link.child_profile.id),
                "created_at": link.created_at.isoformat(),
            },
            "correlation_id": str(correlation_id),
        },
        status=201,
    )


@require_http_methods(["DELETE"])
@require_tenant_context
@require_permission("ParentChildLink", "delete")
def parent_child_delete(request, link_id):
    """Delete a parent-child link within the tenant context.

    Only the parent of the link can delete it.
    """
    ctx = request.tenant_context
    correlation_id = ctx["correlation_id"]

    try:
        link = ParentChildLink.objects.get(
            pk=link_id,
            parent_profile=ctx["user_profile"],
        )
    except ParentChildLink.DoesNotExist:
        return _error_response(
            404, "link_not_found", "Parent-child link not found", correlation_id
        )

    link.delete()
    return JsonResponse(
        {"data": None, "correlation_id": str(correlation_id)},
        status=204,
    )


# ---------------------------------------------------------------- Individual registration


# ---------------------------------------------------------------- Individual registration

@csrf_exempt
@require_http_methods(["POST"])
def individual_register(request):
    """Individual registration endpoint.

    Creates a new user, organization (individual type, pending), user profile,
    organization membership role (org_admin), and a pending subscription license.
    No tenant context is required — the user does not yet belong to an organization.

    This is an open endpoint (no authentication required). Security is provided by
    input validation and unique constraints.
    """
    correlation_id = _extract_correlation_id(request)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return _error_response(400, "invalid_json", "Request body must be valid JSON", correlation_id)

    # Validate required fields
    required_fields = ("username", "password", "email", "phone_number", "organization_name")
    for field in required_fields:
        if not body.get(field):
            return _error_response(
                400, "missing_field", f"Required field missing: {field}", correlation_id,
                field=field,
            )

    username = body["username"]
    password = body["password"]
    email = body["email"]
    phone_number = body["phone_number"]
    org_name = body["organization_name"]

    User = get_user_model()

    # Check for duplicate username/email
    if User.objects.filter(username=username).exists():
        return _error_response(409, "duplicate_username", "Username already taken", correlation_id, field="username")
    if User.objects.filter(email=email).exists():
        return _error_response(409, "duplicate_email", "Email already registered", correlation_id, field="email")

    try:
        with transaction.atomic():
            # Create Django user
            auth_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )

            # Create organization (individual, pending)
            organization = Organization.objects.create(
                name=org_name,
                org_type=OrganizationType.INDIVIDUAL,
                status=OrganizationStatus.PENDING,
            )

            # Create user profile
            profile = UserProfile.objects.create(
                user=auth_user,
                organization=organization,
                phone_number=phone_number,
            )

            # Create org_admin role assignment
            OrganizationMembershipRole.objects.create(
                user_profile=profile,
                role_code=MembershipRoleCode.ORG_ADMIN,
            )

            # Create pending subscription license
            license_record = SubscriptionLicense.objects.create(
                organization=organization,
                product_code=SubscriptionProductCode.EDTECH_LMS,
                seat_capacity=1,
                status=LicenseStatus.PENDING,
            )

    except (ValidationError, IntegrityError) as exc:
        return _error_response(400, "registration_failed", str(exc), correlation_id)

    return JsonResponse(
        {
            "data": {
                "user_id": str(auth_user.id),
                "username": auth_user.username,
                "email": auth_user.email,
                "organization_id": str(organization.id),
                "organization_name": organization.name,
                "organization_type": organization.org_type,
                "organization_status": organization.status,
                "profile_id": str(profile.id),
                "role_code": MembershipRoleCode.ORG_ADMIN,
                "license_id": str(license_record.id),
                "license_status": license_record.status,
            },
            "correlation_id": str(correlation_id),
        },
        status=201,
    )


# ---------------------------------------------------------------- Template UI views

def _extract_org_id(request):
    """Read org id from header, POST body, or GET query param."""
    if "HTTP_X_INOVATX_ORGANIZATION_ID" in request.META:
        return request.META["HTTP_X_INOVATX_ORGANIZATION_ID"]
    if request.method == "POST":
        return request.POST.get("org_id")
    return request.GET.get("org")


def ensure_org_header(view_func):
    """Outermost decorator: copy org id from POST/GET into META header
    so require_tenant_context can read it for template-rendered views.
    If no org id is provided and the user has memberships, redirect to
    ?org=<first_org> so the page loads with a valid tenant context."""
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        org_id = _extract_org_id(request)
        if org_id and "HTTP_X_INOVATX_ORGANIZATION_ID" not in request.META:
            request.META["HTTP_X_INOVATX_ORGANIZATION_ID"] = org_id
        elif not org_id and request.user.is_authenticated:
            orgs = (
                request.user.organization_memberships.select_related("organization").all()
            )
            if orgs:
                return redirect(f"{request.path}?org={orgs[0].organization.id}")
        return view_func(request, *args, **kwargs)
    return wrapped


def _role_label(role_code):
    labels = {
        "org_admin": "Org Admin",
        "instructor": "Instructor",
        "student": "Student",
        "parent": "Parent",
        "sme_staff": "SME Staff",
    }
    return labels.get(role_code, role_code)


def _status_badge_class(status):
    classes = {
        "pending": "badge-pending",
        "active": "badge-active",
        "suspended": "badge-suspended",
        "expired": "badge-expired",
        "cancelled": "badge-cancelled",
    }
    return classes.get(status, "badge-cancelled")


# ---------------------------------------------------------------- Dashboard

@require_http_methods(["GET"])
@ensure_org_header
def ui_dashboard(request):
    if not request.user.is_authenticated:
        return redirect("ui-login")

    org_id_raw = _extract_organization_id(request)
    if org_id_raw is None:
        orgs = (
            request.user.organization_memberships.select_related("organization").all()
        )
        if not orgs:
            messages.info(request, "No organizations found. Contact an administrator.")
            return render(request, "dashboard.html", {"orgs": [], "org_id": None})
        return redirect(f"{request.path}?org={orgs[0].organization.id}")
    if org_id_raw == "malformed":
        messages.error(request, "Invalid organization selector.")
        return redirect("ui-dashboard")

    try:
        organization = Organization.objects.get(pk=org_id_raw)
    except Organization.DoesNotExist:
        messages.error(request, "Organization not found.")
        return redirect("ui-dashboard")

    user_profile = _validate_membership(request.user, organization.id)
    if user_profile is None:
        messages.error(request, "You are not a member of this organization.")
        return redirect("ui-dashboard")

    is_system_admin = _is_system_admin(request.user)

    if not is_system_admin and not _user_has_permission_from_ctx_manual(
        user_profile, "Organization", "view"
    ):
        messages.error(request, "You do not have permission to view this organization.")
        return redirect("ui-login")

    profiles = UserProfile.objects.filter(organization=organization).select_related("user")
    roles = OrganizationMembershipRole.objects.filter(user_profile__organization=organization)
    licenses = SubscriptionLicense.objects.filter(organization=organization)

    license_record = licenses.first()
    license_status = license_record.status if license_record else None

    recent_profiles = profiles.order_by("-created_at")[:5]

    can_create_license = is_system_admin or _user_has_permission_from_ctx_manual(
        user_profile, "SubscriptionLicense", "create"
    )
    can_create_org = is_system_admin or _user_has_permission_from_ctx_manual(
        user_profile, "Organization", "create"
    )

    context = {
        "organization": organization,
        "user_profile": user_profile,
        "is_system_admin": is_system_admin,
        "profile_count": profiles.count(),
        "role_count": roles.count(),
        "license_count": licenses.count(),
        "license_status": license_status,
        "license_status_class": _status_badge_class(license_status) if license_status else None,
        "licenses": licenses,
        "recent_profiles": recent_profiles,
        "can_create_license": can_create_license,
        "can_create_org": can_create_org,
        "org_id": str(organization.id),
    }
    return render(request, "dashboard.html", context)


def _user_has_permission_from_ctx_manual(user_profile, resource, action):
    if user_profile is None:
        return False
    role_codes = set(
        user_profile.role_assignments.values_list("role_code", flat=True)
    )
    for role_code in role_codes:
        perms = ROLE_PERMISSIONS.get(role_code, {})
        allowed_actions = perms.get(resource, set())
        if action in allowed_actions:
            return True
    return False


# ---------------------------------------------------------------- Organizations

@require_http_methods(["GET", "POST"])
@ensure_org_header
@require_tenant_context
@require_permission("Organization", "view")
def ui_organization_list(request):
    ctx = request.tenant_context
    org = ctx["organization"]
    user_profile = ctx["user_profile"]
    is_system_admin = ctx["is_system_admin"]

    if request.method == "POST":
        if not is_system_admin and not _user_has_permission_from_ctx(
            ctx, "Organization", "create"
        ):
            messages.error(request, "You do not have permission to create organizations.")
            return redirect("ui-organization-list")

        name = request.POST.get("name")
        org_type = request.POST.get("org_type")
        status = request.POST.get("status")

        if not name or not org_type or not status:
            messages.error(request, "Name, organization type, and status are required.")
            return redirect("ui-organization-list")

        try:
            Organization.objects.create(name=name, org_type=org_type, status=status)
            messages.success(request, "Organization created successfully.")
        except (ValidationError, IntegrityError) as exc:
            messages.error(request, f"Failed to create organization: {exc}")

        return redirect("ui-organization-list")

    orgs = Organization.objects.all() if is_system_admin else Organization.objects.filter(id=org.id)
    can_create = is_system_admin or _user_has_permission_from_ctx(ctx, "Organization", "create")

    context = {
        "organization": org,
        "user_profile": user_profile,
        "is_system_admin": is_system_admin,
        "orgs": orgs,
        "can_create": can_create,
        "org_id": str(org.id),
    }
    return render(request, "organizations/list.html", context)


@require_http_methods(["GET", "POST"])
@ensure_org_header
@require_tenant_context
@require_permission("Organization", "view")
def ui_organization_detail(request, organization_id):
    ctx = request.tenant_context
    org = ctx["organization"]
    user_profile = ctx["user_profile"]
    is_system_admin = ctx["is_system_admin"]

    try:
        target = Organization.objects.get(pk=organization_id)
    except Organization.DoesNotExist:
        messages.error(request, "Organization not found.")
        return redirect("ui-organization-list")

    if str(target.id) != str(org.id) and not is_system_admin:
        messages.error(request, "Access to another organization is denied.")
        return redirect("ui-organization-list")

    if request.method == "POST":
        _method = request.POST.get("_method", "").upper()
        if _method == "DELETE":
            if not is_system_admin:
                messages.error(request, "Only system administrators can delete organizations.")
                return redirect("ui-organization-detail", organization_id=organization_id)
            target.delete()
            messages.success(request, "Organization deleted successfully.")
            return redirect("ui-organization-list")

        if not is_system_admin and not _user_has_permission_from_ctx(ctx, "Organization", "update"):
            messages.error(request, "You do not have permission to update this organization.")
            return redirect("ui-organization-detail", organization_id=organization_id)

        name = request.POST.get("name")
        org_type = request.POST.get("org_type")
        status = request.POST.get("status")

        if name:
            target.name = name
        if org_type:
            target.org_type = org_type
        if status:
            target.status = status

        try:
            target.full_clean()
            target.save()
            messages.success(request, "Organization updated successfully.")
        except (ValidationError, IntegrityError) as exc:
            messages.error(request, f"Failed to update organization: {exc}")

        return redirect("ui-organization-detail", organization_id=organization_id)

    can_update = is_system_admin or _user_has_permission_from_ctx(ctx, "Organization", "update")
    can_delete = is_system_admin

    context = {
        "organization": org,
        "user_profile": user_profile,
        "is_system_admin": is_system_admin,
        "org": target,
        "can_update": can_update,
        "can_delete": can_delete,
        "org_id": str(org.id),
        "org_types": OrganizationType.choices,
        "statuses": OrganizationStatus.choices,
    }
    return render(request, "organizations/detail.html", context)


# ---------------------------------------------------------------- Profiles

@require_http_methods(["GET"])
@ensure_org_header
@require_tenant_context
@require_permission("UserProfile", "view")
def ui_profile_list(request):
    ctx = request.tenant_context
    org = ctx["organization"]
    user_profile = ctx["user_profile"]
    is_system_admin = ctx["is_system_admin"]

    profiles = (
        UserProfile.objects.filter(organization=org)
        .select_related("user")
        .prefetch_related("role_assignments")
    )

    context = {
        "organization": org,
        "user_profile": user_profile,
        "is_system_admin": is_system_admin,
        "profiles": profiles,
        "org_id": str(org.id),
    }
    return render(request, "profiles/list.html", context)


@require_http_methods(["GET", "POST"])
@ensure_org_header
@require_tenant_context
@require_permission("UserProfile", "view")
def ui_profile_create(request):
    ctx = request.tenant_context
    org = ctx["organization"]
    user_profile = ctx["user_profile"]
    is_system_admin = ctx["is_system_admin"]

    if not is_system_admin and not _user_has_permission_from_ctx(ctx, "UserProfile", "create"):
        messages.error(request, "You do not have permission to create profiles.")
        return redirect("ui-profile-list")

    User = get_user_model()

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        phone_number = request.POST.get("phone_number")

        if not username or not password or not phone_number:
            messages.error(request, "Username, password, and phone number are required.")
            return redirect("ui-profile-create")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("ui-profile-create")

        if email and User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("ui-profile-create")

        try:
            auth_user = User.objects.create_user(username=username, email=email, password=password)
            profile = UserProfile.objects.create(
                user=auth_user, organization=org, phone_number=phone_number,
            )
            messages.success(request, f"Profile created for {username}.")
            return redirect("ui-profile-list")
        except (ValidationError, IntegrityError) as exc:
            messages.error(request, f"Failed to create profile: {exc}")
            return redirect("ui-profile-create")

    context = {
        "organization": org,
        "user_profile": user_profile,
        "is_system_admin": is_system_admin,
        "org_id": str(org.id),
    }
    return render(request, "profiles/create.html", context)


# ---------------------------------------------------------------- Roles

@require_http_methods(["GET", "POST"])
@ensure_org_header
@require_tenant_context
@require_permission("OrganizationMembershipRole", "view")
def ui_role_create(request):
    ctx = request.tenant_context
    org = ctx["organization"]
    user_profile = ctx["user_profile"]
    is_system_admin = ctx["is_system_admin"]

    if not is_system_admin and not _user_has_permission_from_ctx(
        ctx, "OrganizationMembershipRole", "create"
    ):
        messages.error(request, "You do not have permission to assign roles.")
        return redirect("ui-profile-list")

    profiles = UserProfile.objects.filter(organization=org).select_related("user")
    role_codes = MembershipRoleCode.choices

    if request.method == "POST":
        user_profile_id = request.POST.get("user_profile")
        role_code = request.POST.get("role_code")

        if not user_profile_id or not role_code:
            messages.error(request, "Profile and role are required.")
            return redirect("ui-role-create")

        try:
            target_profile = UserProfile.objects.get(pk=user_profile_id, organization=org)
        except UserProfile.DoesNotExist:
            messages.error(request, "Profile not found in this organization.")
            return redirect("ui-role-create")

        try:
            OrganizationMembershipRole.objects.create(
                user_profile=target_profile, role_code=role_code,
            )
            messages.success(request, f"Role {role_code} assigned.")
            return redirect("ui-profile-list")
        except (ValidationError, IntegrityError) as exc:
            messages.error(request, f"Failed to assign role: {exc}")
            return redirect("ui-role-create")

    context = {
        "organization": org,
        "user_profile": user_profile,
        "is_system_admin": is_system_admin,
        "profiles": profiles,
        "role_codes": role_codes,
        "org_id": str(org.id),
    }
    return render(request, "roles/create.html", context)


# ---------------------------------------------------------------- Licenses

@require_http_methods(["GET", "POST"])
@ensure_org_header
@require_tenant_context
@require_permission("SubscriptionLicense", "view")
def ui_license_list(request):
    ctx = request.tenant_context
    org = ctx["organization"]
    user_profile = ctx["user_profile"]
    is_system_admin = ctx["is_system_admin"]

    if request.method == "POST":
        if not is_system_admin and not _user_has_permission_from_ctx(
            ctx, "SubscriptionLicense", "create"
        ):
            messages.error(request, "You do not have permission to create licenses.")
            return redirect("ui-license-list")

        product_code = request.POST.get("product_code")
        seat_capacity = request.POST.get("seat_capacity")
        status = request.POST.get("status")
        moodle_cohort_id = request.POST.get("moodle_cohort_id") or None
        ai_monthly = request.POST.get("ai_monthly_interaction_allowance_per_learner_seat") or None
        ai_daily = request.POST.get("ai_daily_interaction_cap_per_learner_seat") or None
        valid_until = request.POST.get("valid_until") or None

        if not product_code or not seat_capacity or not status:
            messages.error(request, "Product code, seat capacity, and status are required.")
            return redirect("ui-license-list")

        try:
            seat_capacity = int(seat_capacity)
        except (TypeError, ValueError):
            messages.error(request, "Seat capacity must be a number.")
            return redirect("ui-license-list")

        try:
            SubscriptionLicense.objects.create(
                organization=org,
                product_code=product_code,
                seat_capacity=seat_capacity,
                status=status,
                moodle_cohort_id=moodle_cohort_id,
                ai_monthly_interaction_allowance_per_learner_seat=int(ai_monthly) if ai_monthly else None,
                ai_daily_interaction_cap_per_learner_seat=int(ai_daily) if ai_daily else None,
                valid_until=valid_until,
            )
            messages.success(request, "License created successfully.")
        except (ValidationError, IntegrityError) as exc:
            messages.error(request, f"Failed to create license: {exc}")

        return redirect("ui-license-list")

    licenses = SubscriptionLicense.objects.filter(organization=org)
    can_create = is_system_admin or _user_has_permission_from_ctx(ctx, "SubscriptionLicense", "create")

    context = {
        "organization": org,
        "user_profile": user_profile,
        "is_system_admin": is_system_admin,
        "licenses": licenses,
        "can_create": can_create,
        "product_codes": SubscriptionProductCode.choices,
        "statuses": LicenseStatus.choices,
        "org_id": str(org.id),
    }
    return render(request, "licenses/list.html", context)


@require_http_methods(["GET", "POST"])
@ensure_org_header
@require_tenant_context
@require_permission("SubscriptionLicense", "view")
def ui_license_detail(request, license_id):
    ctx = request.tenant_context
    org = ctx["organization"]
    user_profile = ctx["user_profile"]
    is_system_admin = ctx["is_system_admin"]

    try:
        license_record = SubscriptionLicense.objects.get(pk=license_id, organization=org)
    except SubscriptionLicense.DoesNotExist:
        messages.error(request, "License not found.")
        return redirect("ui-license-list")

    if request.method == "POST":
        _method = request.POST.get("_method", "").upper()
        if _method == "DELETE":
            if not is_system_admin:
                messages.error(request, "Only system administrators can delete licenses.")
                return redirect("ui-license-detail", license_id=license_id)
            license_record.delete()
            messages.success(request, "License deleted successfully.")
            return redirect("ui-license-list")

        if not is_system_admin and not _user_has_permission_from_ctx(
            ctx, "SubscriptionLicense", "update"
        ):
            messages.error(request, "You do not have permission to update this license.")
            return redirect("ui-license-detail", license_id=license_id)

        product_code = request.POST.get("product_code")
        seat_capacity = request.POST.get("seat_capacity")
        status = request.POST.get("status")
        moodle_cohort_id = request.POST.get("moodle_cohort_id") or None
        ai_monthly = request.POST.get("ai_monthly_interaction_allowance_per_learner_seat") or None
        ai_daily = request.POST.get("ai_daily_interaction_cap_per_learner_seat") or None
        valid_until = request.POST.get("valid_until") or None

        if product_code:
            license_record.product_code = product_code
        if seat_capacity:
            try:
                license_record.seat_capacity = int(seat_capacity)
            except (TypeError, ValueError):
                messages.error(request, "Seat capacity must be a number.")
                return redirect("ui-license-detail", license_id=license_id)
        if status:
            license_record.status = status
        license_record.moodle_cohort_id = moodle_cohort_id
        license_record.ai_monthly_interaction_allowance_per_learner_seat = (
            int(ai_monthly) if ai_monthly else None
        )
        license_record.ai_daily_interaction_cap_per_learner_seat = (
            int(ai_daily) if ai_daily else None
        )
        license_record.valid_until = valid_until

        try:
            license_record.full_clean()
            license_record.save()
            messages.success(request, "License updated successfully.")
        except (ValidationError, IntegrityError) as exc:
            messages.error(request, f"Failed to update license: {exc}")

        return redirect("ui-license-detail", license_id=license_id)

    can_update = is_system_admin or _user_has_permission_from_ctx(ctx, "SubscriptionLicense", "update")
    can_delete = is_system_admin

    context = {
        "organization": org,
        "user_profile": user_profile,
        "is_system_admin": is_system_admin,
        "license": license_record,
        "can_update": can_update,
        "can_delete": can_delete,
        "product_codes": SubscriptionProductCode.choices,
        "statuses": LicenseStatus.choices,
        "org_id": str(org.id),
    }
    return render(request, "licenses/detail.html", context)


# ---------------------------------------------------------------- Parent-Child

@require_http_methods(["GET"])
@ensure_org_header
@require_tenant_context
@require_permission("ParentChildLink", "view")
def ui_parent_child_list(request):
    ctx = request.tenant_context
    org = ctx["organization"]
    user_profile = ctx["user_profile"]
    is_system_admin = ctx["is_system_admin"]

    if is_system_admin or ctx["user_profile"].role_assignments.filter(role_code="parent").exists():
        links = (
            ParentChildLink.objects.filter(parent_profile=user_profile)
            .select_related("child_profile", "child_profile__user")
        )
    else:
        links = (
            ParentChildLink.objects.filter(child_profile=user_profile)
            .select_related("parent_profile", "parent_profile__user")
        )

    profiles = UserProfile.objects.filter(organization=org).select_related("user")
    can_create = is_system_admin or _user_has_permission_from_ctx(
        ctx, "ParentChildLink", "create"
    )
    can_delete = is_system_admin or _user_has_permission_from_ctx(
        ctx, "ParentChildLink", "delete"
    )

    context = {
        "organization": org,
        "user_profile": user_profile,
        "is_system_admin": is_system_admin,
        "links": links,
        "profiles": profiles,
        "can_create": can_create,
        "can_delete": can_delete,
        "org_id": str(org.id),
    }
    return render(request, "parent-children/list.html", context)


@require_http_methods(["GET", "POST"])
@ensure_org_header
@require_tenant_context
@require_permission("ParentChildLink", "create")
def ui_parent_child_create(request):
    ctx = request.tenant_context
    org = ctx["organization"]
    user_profile = ctx["user_profile"]
    is_system_admin = ctx["is_system_admin"]

    profiles = UserProfile.objects.filter(organization=org).select_related("user")

    if request.method == "POST":
        child_profile_id = request.POST.get("child_profile_id")

        if not child_profile_id:
            messages.error(request, "Child profile is required.")
            return redirect("ui-parent-child-create")

        try:
            child_profile = UserProfile.objects.get(
                pk=child_profile_id, organization=org,
            )
        except UserProfile.DoesNotExist:
            messages.error(request, "Child profile not found in this organization.")
            return redirect("ui-parent-child-create")

        if str(child_profile.id) == str(user_profile.id):
            messages.error(request, "You cannot link to yourself.")
            return redirect("ui-parent-child-create")

        try:
            ParentChildLink.objects.create(
                parent_profile=user_profile, child_profile=child_profile,
            )
            messages.success(request, "Parent-child link created.")
            return redirect("ui-parent-child-list")
        except IntegrityError:
            messages.error(request, "This link already exists.")
            return redirect("ui-parent-child-create")

    context = {
        "organization": org,
        "user_profile": user_profile,
        "is_system_admin": is_system_admin,
        "profiles": profiles,
        "org_id": str(org.id),
    }
    return render(request, "parent-children/create.html", context)


@require_http_methods(["POST"])
@ensure_org_header
@require_tenant_context
@require_permission("ParentChildLink", "delete")
def ui_parent_child_delete(request, link_id):
    ctx = request.tenant_context
    user_profile = ctx["user_profile"]
    is_system_admin = ctx["is_system_admin"]

    try:
        if is_system_admin:
            link = ParentChildLink.objects.get(pk=link_id)
        else:
            link = ParentChildLink.objects.get(pk=link_id, parent_profile=user_profile)
    except ParentChildLink.DoesNotExist:
        messages.error(request, "Link not found.")
        return redirect("ui-parent-child-list")

    link.delete()
    messages.success(request, "Parent-child link deleted.")
    return redirect("ui-parent-child-list")


# ---------------------------------------------------------------- Login / Logout

@require_http_methods(["GET", "POST"])
def ui_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        from django.contrib.auth import authenticate, login as auth_login
        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)
            next_url = request.POST.get("next") or "ui-dashboard"
            return redirect(next_url)
        messages.error(request, "Invalid username or password.")
    return render(request, "registration/login.html")


@require_http_methods(["GET", "POST"])
def ui_logout(request):
    from django.contrib.auth import logout as auth_logout
    auth_logout(request)
    request.session.flush()
    messages.success(request, "You have been signed out.")
    return redirect("ui-login")


# ---------------------------------------------------------------- Registration

@require_http_methods(["GET", "POST"])
def ui_register_individual(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number")
        org_name = request.POST.get("organization_name")

        if not username or not password or not email or not phone_number or not org_name:
            messages.error(request, "All fields are required.")
            return render(request, "registration/individual.html")

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, "registration/individual.html")
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, "registration/individual.html")

        try:
            with transaction.atomic():
                auth_user = User.objects.create_user(
                    username=username, email=email, password=password,
                )
                organization = Organization.objects.create(
                    name=org_name, org_type=OrganizationType.INDIVIDUAL,
                    status=OrganizationStatus.PENDING,
                )
                profile = UserProfile.objects.create(
                    user=auth_user, organization=organization, phone_number=phone_number,
                )
                OrganizationMembershipRole.objects.create(
                    user_profile=profile, role_code=MembershipRoleCode.ORG_ADMIN,
                )
                SubscriptionLicense.objects.create(
                    organization=organization,
                    product_code=SubscriptionProductCode.EDTECH_LMS,
                    seat_capacity=1,
                    status=LicenseStatus.PENDING,
                )
            messages.success(request, "Account created successfully. Please sign in.")
            return redirect("ui-login")
        except (ValidationError, IntegrityError) as exc:
            messages.error(request, f"Registration failed: {exc}")

    return render(request, "registration/individual.html")


@require_http_methods(["GET", "POST"])
def ui_register_institutional(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number")
        org_name = request.POST.get("organization_name")
        org_type = request.POST.get("organization_type")
        seat_capacity = request.POST.get("seat_capacity", 50)

        if not username or not password or not email or not phone_number or not org_name or not org_type:
            messages.error(request, "All fields are required.")
            return render(request, "registration/institutional.html")

        institutional_types = {
            OrganizationType.SCHOOL, OrganizationType.SME,
            OrganizationType.NGO, OrganizationType.ENTERPRISE,
        }
        if org_type not in institutional_types:
            messages.error(request, "Invalid organization type.")
            return render(request, "registration/institutional.html")

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, "registration/institutional.html")
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, "registration/institutional.html")

        try:
            seat_capacity = int(seat_capacity)
        except (TypeError, ValueError):
            seat_capacity = 50

        try:
            with transaction.atomic():
                auth_user = User.objects.create_user(
                    username=username, email=email, password=password,
                )
                organization = Organization.objects.create(
                    name=org_name, org_type=org_type, status=OrganizationStatus.PENDING,
                )
                profile = UserProfile.objects.create(
                    user=auth_user, organization=organization, phone_number=phone_number,
                )
                OrganizationMembershipRole.objects.create(
                    user_profile=profile, role_code=MembershipRoleCode.ORG_ADMIN,
                )
                SubscriptionLicense.objects.create(
                    organization=organization,
                    product_code=SubscriptionProductCode.EDTECH_LMS,
                    seat_capacity=seat_capacity,
                    status=LicenseStatus.PENDING,
                )
            messages.success(request, "Institutional account created successfully. Please sign in.")
            return redirect("ui-login")
        except (ValidationError, IntegrityError) as exc:
            messages.error(request, f"Registration failed: {exc}")

    return render(request, "registration/institutional.html")


def _user_has_permission_from_ctx(ctx, resource, action):
    if ctx.get("is_system_admin"):
        return True
    user_profile = ctx.get("user_profile")
    if user_profile is None:
        return False
    role_codes = set(
        user_profile.role_assignments.values_list("role_code", flat=True)
    )
    for role_code in role_codes:
        perms = ROLE_PERMISSIONS.get(role_code, {})
        allowed_actions = perms.get(resource, set())
        if action in allowed_actions:
            return True
    return False
