import json

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .models import (
    Organization,
    UserProfile,
    OrganizationMembershipRole,
    SubscriptionLicense,
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