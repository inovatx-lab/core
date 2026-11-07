"""Celery tasks for INOVATX Core.

Task 3.2.1: Build Celery task for Moodle user creation.
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
)

logger = logging.getLogger(__name__)


def _moodle_api_url() -> str:
    return getattr(settings, "MOODLE_API_URL", "")


def _moodle_token() -> str:
    return getattr(settings, "MOODLE_TOKEN", "")


def _http_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_moodle_token()}",
        "Content-Type": "application/x-www-form-urlencoded",
    }


def _create_moodle_user(payload: dict[str, Any]) -> int | None:
    """Call core_user_create_users and return the created user ID."""
    url = f"{_moodle_api_url()}/core_user_create_users"
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
    response = requests.post(url, data=data, headers=_http_headers(), timeout=30)
    response.raise_for_status()
    users = response.json()
    if not users:
        return None
    return users[0].get("id")


def _create_moodle_cohort(payload: dict[str, Any]) -> int | None:
    """Call core_cohort_create_cohorts and return the created cohort ID."""
    url = f"{_moodle_api_url()}/core_cohort_create_cohorts"
    data = {
        "cohorts[0][name]": payload["name"],
        "cohorts[0][contextlevel]": payload.get("contextlevel", "context"),
        "cohorts[0][contextinstanceid]": payload.get("contextinstanceid", 1),
        "cohorts[0][visible]": payload.get("visible", 1),
        "cohorts[0][description]": payload.get("description", ""),
    }
    response = requests.post(url, data=data, headers=_http_headers(), timeout=30)
    response.raise_for_status()
    cohorts = response.json()
    if not cohorts:
        return None
    return cohorts[0].get("id")


def _add_cohort_members(cohort_id: int, user_ids: list[int]) -> bool:
    """Call core_cohort_add_cohort_members."""
    url = f"{_moodle_api_url()}/core_cohort_add_cohort_members"
    data = {}
    for i, uid in enumerate(user_ids):
        data[f"members[{i}][cohortid]"] = cohort_id
        data[f"members[{i}][userid]"] = uid
    response = requests.post(url, data=data, headers=_http_headers(), timeout=30)
    response.raise_for_status()
    return True


def _enroll_individual_user(payload: dict[str, Any]) -> bool:
    """Enroll individual user in standard course group (deferred to Task 3.2.2)."""
    return True


@shared_task(bind=True, max_retries=5, default_retry_delay=5)
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

    org = Organization.objects.get(pk=org_uuid)
    profile = UserProfile.objects.get(user=user_uuid, organization=org)
    license_obj = SubscriptionLicense.objects.get(pk=license_uuid, organization=org)

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

    moodle_user_id = _create_moodle_user(moodle_payload)
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
        cohort_id = _create_moodle_cohort(cohort_payload)
        if cohort_id is None:
            return {"status": "failed", "error": "cohort_creation_failed"}
        _add_cohort_members(cohort_id, [moodle_user_id])
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
