"""Celery tasks for INOVATX Core.

Task 3.2.1: Build Celery task for Moodle user creation.
Task 3.2.2: Build Celery task for cohort creation and member assignment.
Task 3.2.3: Add retry and error handling for Moodle API failures.
"""

import logging
import uuid
from typing import Any

import requests
from celery import shared_task
from django.conf import settings

from core.models import (
    Organization,
    OrganizationMembershipRole,
    SubscriptionLicense,
    UserProfile,
    WebhookDLQ,
)

logger = logging.getLogger(__name__)

# Retry backoff intervals per Decision log D6: 5s, 15s, 45s, 2m, 6m
RETRY_BACKOFF_INTERVALS = [5, 15, 45, 120, 360]
MAX_RETRIES = 5


def _moodle_api_url() -> str:
    return getattr(settings, "MOODLE_API_URL", "")


def _moodle_token() -> str:
    return getattr(settings, "MOODLE_TOKEN", "")


def _http_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_moodle_token()}",
        "Content-Type": "application/x-www-form-urlencoded",
    }


def _is_retryable_error(exc: Exception) -> bool:
    """Determine if an error should trigger a retry vs dead-letter."""
    if isinstance(exc, requests.exceptions.ConnectionError):
        return True
    if isinstance(exc, requests.exceptions.Timeout):
        return True
    if isinstance(exc, requests.exceptions.HTTPError):
        response = exc.response
        if response is not None:
            status_code = response.status_code
            # 5xx errors are retryable, 4xx are terminal (except 429)
            if 500 <= status_code < 600:
                return True
            if status_code == 429:  # Too Many Requests
                return True
    return False


def _exponential_backoff(retry_count: int) -> int:
    """Return backoff interval in seconds for given retry count."""
    if retry_count < len(RETRY_BACKOFF_INTERVALS):
        return RETRY_BACKOFF_INTERVALS[retry_count]
    return RETRY_BACKOFF_INTERVALS[-1] * (2 ** (retry_count - len(RETRY_BACKOFF_INTERVALS) + 1))


def _dead_letter(
    organization_id: str,
    event_type: str,
    payload: dict,
    error: str,
    correlation_id: str | None = None,
) -> None:
    """Write a terminal failure to the WebhookDLQ table."""
    try:
        org_uuid = uuid.UUID(organization_id)
        org = Organization.objects.get(pk=org_uuid)
        corr_uuid = None
        if correlation_id:
            try:
                corr_uuid = uuid.UUID(correlation_id)
            except (ValueError, TypeError):
                pass
        WebhookDLQ.objects.create(
            organization=org,
            event_type=event_type,
            payload=payload,
            error=error,
            status="pending",
            correlation_id=corr_uuid,
        )
    except Exception as dlq_exc:
        logger.error("Failed to write to WebhookDLQ: %s", dlq_exc)


def _moodle_request(method: str, endpoint: str, data: dict = None) -> dict | None:
    """Make a Moodle API request and return the parsed JSON response."""
    url = f"{_moodle_api_url()}/{endpoint}"
    response = requests.request(method, url, data=data, headers=_http_headers(), timeout=30)
    response.raise_for_status()
    result = response.json()
    return result if result else None


def _create_moodle_user(payload: dict[str, Any]) -> int | None:
    """Call core_user_create_users and return the created user ID."""
    data = {
        "users[0][username]": payload["username"],
        "users[0][password]": payload["password"],
        "users[0][firstname]": payload["firstname"],
        "users[0][lastname]": payload["lastname"],
        "users[0][email]": payload["email"],
        "users[0][auth]": payload.get("auth", "manual"),
        "users[0][lang]": payload.get("lang", "en"),
        "users[0][timezone]": payload.get("timezone", "UTC"),
    }
    result = _moodle_request("post", "core_user_create_users", data)
    if result:
        return result[0].get("id")
    return None


def _create_moodle_cohort(payload: dict[str, Any]) -> int | None:
    """Call core_cohort_create_cohorts and return the created cohort ID."""
    data = {
        "cohorts[0][name]": payload["name"],
        "cohorts[0][contextlevel]": payload.get("contextlevel", "context"),
        "cohorts[0][contextinstanceid]": payload.get("contextinstanceid", 1),
        "cohorts[0][visible]": payload.get("visible", 1),
        "cohorts[0][description]": payload.get("description", ""),
    }
    result = _moodle_request("post", "core_cohort_create_cohorts", data)
    if result:
        return result[0].get("id")
    return None


def _add_cohort_members(cohort_id: int, user_ids: list[int]) -> bool:
    """Call core_cohort_add_cohort_members."""
    data = {}
    for i, uid in enumerate(user_ids):
        data[f"members[{i}][cohortid]"] = cohort_id
        data[f"members[{i}][userid]"] = uid
    _moodle_request("post", "core_cohort_add_cohort_members", data)
    return True


def _enroll_individual_user(payload: dict[str, Any]) -> bool:
    """Enroll individual user in standard course group (deferred to Task 3.2.2)."""
    return True


@shared_task(bind=True, max_retries=MAX_RETRIES)
def provision_moodle_user(
    self,
    organization_id: str,
    user_id: str,
    license_id: str,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Create Moodle user account for an INOVATX user.

    Task 3.2.1: Build Celery task for Moodle user creation.
    """
    try:
        org_uuid = uuid.UUID(organization_id)
        user_uuid = uuid.UUID(user_id)
        license_uuid = uuid.UUID(license_id)
    except (ValueError, TypeError):
        return {"status": "failed", "error": "invalid_uuid"}

    try:
        org = Organization.objects.get(pk=org_uuid)
        profile = UserProfile.objects.get(user=user_uuid, organization=org)
        license_obj = SubscriptionLicense.objects.get(pk=license_uuid, organization=org)
    except (Organization.DoesNotExist, UserProfile.DoesNotExist, SubscriptionLicense.DoesNotExist):
        return {"status": "failed", "error": "not_found"}

    role_codes = set(
        profile.role_assignments.values_list("role_code", flat=True)
    )

    moodle_payload = {
        "username": profile.user.username,
        "password": str(uuid.uuid4()),
        "firstname": profile.user.first_name or "",
        "lastname": profile.user.last_name or "",
        "email": profile.user.email or "",
        "auth": "manual",
        "lang": "en",
        "timezone": "UTC",
    }

    try:
        moodle_user_id = _create_moodle_user(moodle_payload)
    except Exception as exc:
        if _is_retryable_error(exc) and self.request.retries < MAX_RETRIES:
            retry_in = _exponential_backoff(self.request.retries)
            raise self.retry(exc=exc, countdown=retry_in)
        _dead_letter(
            organization_id=str(org.id),
            event_type="user_creation",
            payload=moodle_payload,
            error=str(exc),
            correlation_id=correlation_id,
        )
        return {"status": "failed", "error": "user_creation_failed"}

    if moodle_user_id is None:
        return {"status": "failed", "error": "user_creation_failed"}

    if org.org_type != "individual":
        cohort_payload = {
            "name": f"{org.name} - Cohort",
            "contextlevel": "context",
            "contextinstanceid": 1,
            "visible": 1,
            "description": f"Provisioned for {org.name}",
        }
        try:
            cohort_id = _create_moodle_cohort(cohort_payload)
        except Exception as exc:
            if _is_retryable_error(exc) and self.request.retries < MAX_RETRIES:
                retry_in = _exponential_backoff(self.request.retries)
                raise self.retry(exc=exc, countdown=retry_in)
            _dead_letter(
                organization_id=str(org.id),
                event_type="cohort_creation",
                payload=cohort_payload,
                error=str(exc),
                correlation_id=correlation_id,
            )
            return {"status": "failed", "error": "cohort_creation_failed"}
        if cohort_id is None:
            return {"status": "failed", "error": "cohort_creation_failed"}
        try:
            _add_cohort_members(cohort_id, [moodle_user_id])
        except Exception as exc:
            if _is_retryable_error(exc) and self.request.retries < MAX_RETRIES:
                retry_in = _exponential_backoff(self.request.retries)
                raise self.retry(exc=exc, countdown=retry_in)
            _dead_letter(
                organization_id=str(org.id),
                event_type="cohort_member_assignment",
                payload={"cohort_id": cohort_id, "user_ids": [moodle_user_id]},
                error=str(exc),
                correlation_id=correlation_id,
            )
            return {"status": "failed", "error": "member_assignment_failed"}
        license_obj.moodle_cohort_id = str(cohort_id)
        license_obj.save()
    else:
        _enroll_individual_user(moodle_payload)

    return {
        "status": "success",
        "moodle_user_id": moodle_user_id,
        "organization_id": str(org.id),
        "user_id": str(user_id),
        "license_id": str(license_obj.id),
        "role_codes": list(role_codes),
    }


@shared_task(bind=True, max_retries=MAX_RETRIES)
def provision_moodle_cohort(
    self,
    organization_id: str,
    user_ids: list[str],
    license_id: str,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Create Moodle cohort and assign members for institutional org type.

    Task 3.2.2: Build Celery task for cohort creation and member assignment.
    """
    try:
        org_uuid = uuid.UUID(organization_id)
        license_uuid = uuid.UUID(license_id)
        user_uuids = [uuid.UUID(uid) for uid in user_ids]
    except (ValueError, TypeError):
        return {"status": "failed", "error": "invalid_uuid"}

    try:
        org = Organization.objects.get(pk=org_uuid)
    except Organization.DoesNotExist:
        return {"status": "failed", "error": "not_found"}

    if org.org_type == "individual":
        return {"status": "failed", "error": "individual_org_not_cohort"}

    profiles = list(
        UserProfile.objects.filter(
            user__in=user_uuids, organization=org
        ).select_related("user")
    )
    if len(profiles) != len(user_uuids):
        return {"status": "failed", "error": "user_membership_mismatch"}

    try:
        license_obj = SubscriptionLicense.objects.get(pk=license_uuid, organization=org)
    except SubscriptionLicense.DoesNotExist:
        return {"status": "failed", "error": "not_found"}

    cohort_payload = {
        "name": f"{org.name} - Cohort",
        "contextlevel": "context",
        "contextinstanceid": 1,
        "visible": 1,
        "description": f"Provisioned for {org.name}",
    }
    try:
        cohort_id = _create_moodle_cohort(cohort_payload)
    except Exception as exc:
        if _is_retryable_error(exc) and self.request.retries < MAX_RETRIES:
            retry_in = _exponential_backoff(self.request.retries)
            raise self.retry(exc=exc, countdown=retry_in)
        _dead_letter(
            organization_id=str(org.id),
            event_type="cohort_creation",
            payload=cohort_payload,
            error=str(exc),
            correlation_id=correlation_id,
        )
        return {"status": "failed", "error": "cohort_creation_failed"}
    if cohort_id is None:
        return {"status": "failed", "error": "cohort_creation_failed"}

    user_ids_for_moodle = [p.user.id for p in profiles]
    try:
        _add_cohort_members(cohort_id, user_ids_for_moodle)
    except Exception as exc:
        if _is_retryable_error(exc) and self.request.retries < MAX_RETRIES:
            retry_in = _exponential_backoff(self.request.retries)
            raise self.retry(exc=exc, countdown=retry_in)
        _dead_letter(
            organization_id=str(org.id),
            event_type="cohort_member_assignment",
            payload={"cohort_id": cohort_id, "user_ids": user_ids_for_moodle},
            error=str(exc),
            correlation_id=correlation_id,
        )
        return {"status": "failed", "error": "member_assignment_failed"}

    license_obj.moodle_cohort_id = str(cohort_id)
    license_obj.save()

    return {
        "status": "success",
        "cohort_id": str(cohort_id),
        "organization_id": str(org.id),
        "user_ids": [str(uid) for uid in user_uuids],
        "license_id": str(license_obj.id),
        "member_count": len(user_ids_for_moodle),
    }
