import time
import json

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    LicenseStatus,
    MembershipRoleCode,
    Organization,
    OrganizationMembershipRole,
    OrganizationStatus,
    OrganizationType,
    SubscriptionLicense,
    SubscriptionProductCode,
    UserProfile,
)


class CoreModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="member",
            password="test-password",
        )
        self.organization = Organization.objects.create(
            name="Example School",
            org_type=OrganizationType.SCHOOL,
            status=OrganizationStatus.ACTIVE,
        )

    def test_profile_requires_phone_number(self):
        profile = UserProfile(
            user=self.user,
            organization=self.organization,
            phone_number="",
        )

        with self.assertRaises(ValidationError):
            profile.full_clean()

    def test_profile_is_unique_per_user_and_organization(self):
        UserProfile.objects.create(
            user=self.user,
            organization=self.organization,
            phone_number="+256700000001",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UserProfile.objects.create(
                    user=self.user,
                    organization=self.organization,
                    phone_number="+256700000002",
                )

    def test_membership_role_is_unique_and_cascades_with_profile(self):
        profile = UserProfile.objects.create(
            user=self.user,
            organization=self.organization,
            phone_number="+256700000001",
        )
        role = OrganizationMembershipRole.objects.create(
            user_profile=profile,
            role_code=MembershipRoleCode.INSTRUCTOR,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OrganizationMembershipRole.objects.create(
                    user_profile=profile,
                    role_code=MembershipRoleCode.INSTRUCTOR,
                )

        profile.delete()
        self.assertFalse(OrganizationMembershipRole.objects.filter(pk=role.pk).exists())

    def test_invalid_organization_type_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Organization.objects.create(
                    name="Invalid",
                    org_type="not-a-type",
                    status=OrganizationStatus.ACTIVE,
                )

    def test_invalid_membership_role_is_rejected_by_database(self):
        profile = UserProfile.objects.create(
            user=self.user,
            organization=self.organization,
            phone_number="+256700000001",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OrganizationMembershipRole.objects.create(
                    user_profile=profile,
                    role_code="admin",
                )

    def test_license_capacity_must_be_positive(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SubscriptionLicense.objects.create(
                    organization=self.organization,
                    product_code=SubscriptionProductCode.EDTECH_LMS,
                    seat_capacity=0,
                    status=LicenseStatus.PENDING,
                )

    def test_ai_pro_license_requires_positive_explicit_allowances(self):
        license_record = SubscriptionLicense.objects.create(
            organization=self.organization,
            product_code=SubscriptionProductCode.AI_PRO,
            seat_capacity=1,
            status=LicenseStatus.PENDING,
            ai_monthly_interaction_allowance_per_learner_seat=1000,
            ai_daily_interaction_cap_per_learner_seat=50,
        )
        self.assertEqual(
            license_record.ai_monthly_interaction_allowance_per_learner_seat,
            1000,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SubscriptionLicense.objects.create(
                    organization=self.organization,
                    product_code=SubscriptionProductCode.AI_PRO,
                    seat_capacity=1,
                    status=LicenseStatus.PENDING,
                    ai_monthly_interaction_allowance_per_learner_seat=None,
                    ai_daily_interaction_cap_per_learner_seat=50,
                )

    def test_non_ai_license_has_no_ai_allowance_fields(self):
        record = SubscriptionLicense.objects.create(
            organization=self.organization,
            product_code=SubscriptionProductCode.CRM_BASIC,
            seat_capacity=1,
            status=LicenseStatus.PENDING,
        )

        self.assertIsNone(record.ai_monthly_interaction_allowance_per_learner_seat)
        self.assertIsNone(record.ai_daily_interaction_cap_per_learner_seat)

    def test_license_is_unique_per_organization_and_product(self):
        SubscriptionLicense.objects.create(
            organization=self.organization,
            product_code=SubscriptionProductCode.EDTECH_LMS,
            seat_capacity=1,
            status=LicenseStatus.PENDING,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SubscriptionLicense.objects.create(
                    organization=self.organization,
                    product_code=SubscriptionProductCode.EDTECH_LMS,
                    seat_capacity=2,
                    status=LicenseStatus.ACTIVE,
                )

    def test_user_and_organization_deletion_is_protected(self):
        UserProfile.objects.create(
            user=self.user,
            organization=self.organization,
            phone_number="+256700000001",
        )
        with self.assertRaises(ProtectedError):
            self.organization.delete()
        with self.assertRaises(ProtectedError):
            self.user.delete()

    def test_updated_at_changes_when_record_is_saved(self):
        initial_updated_at = self.organization.updated_at
        time.sleep(0.01)
        self.organization.name = "Renamed School"
        self.organization.save()
        self.organization.refresh_from_db()

        self.assertGreater(self.organization.updated_at, initial_updated_at)
        self.assertLessEqual(self.organization.updated_at, timezone.now())


class CoreAdminTests(TestCase):
    def test_core_models_are_registered(self):
        for model in (
            Organization,
            UserProfile,
            OrganizationMembershipRole,
            SubscriptionLicense,
        ):
            with self.subTest(model=model.__name__):
                self.assertTrue(admin.site.is_registered(model))

    def test_superuser_can_open_core_model_admin_lists(self):
        admin_user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="test-password",
        )
        self.client.force_login(admin_user)

        for url_name in (
            "admin:core_organization_changelist",
            "admin:core_userprofile_changelist",
            "admin:core_organizationmembershiprole_changelist",
            "admin:core_subscriptionlicense_changelist",
        ):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)


class CoreAuthorizationTests(TestCase):
    """Authorization tests for Task 2.1.3 — Django permission enforcement.

    Tests the RBAC matrix from Task 2.1.1 and membership rules from Task 2.1.2:
    - org_admin: view/create/update, no delete
    - instructor/student/parent/sme_staff: view only
    - system_admin (superuser): full CRUD
    - Cross-organization access denied (403)
    - Non-member gets uniform 404 (P1.2.3-D1)
    - Error semantics: 401/400/404/403/500 (P1.2.3-D1)
    """

    ORG_ID_HEADER = "HTTP_X_INOVATX_ORGANIZATION_ID"
    CORR_ID_HEADER = "HTTP_X_CORRELATION_ID"

    def setUp(self):
        self.User = get_user_model()

        # Two organizations for cross-org tests
        self.org_a = Organization.objects.create(
            name="Org A",
            org_type=OrganizationType.SCHOOL,
            status=OrganizationStatus.ACTIVE,
        )
        self.org_b = Organization.objects.create(
            name="Org B",
            org_type=OrganizationType.SCHOOL,
            status=OrganizationStatus.ACTIVE,
        )

        # Users with different roles in org_a
        self.admin_user = self.User.objects.create_user(
            username="org_admin_a", password="test-password"
        )
        self.instructor_user = self.User.objects.create_user(
            username="instructor_a", password="test-password"
        )
        self.student_user = self.User.objects.create_user(
            username="student_a", password="test-password"
        )
        self.parent_user = self.User.objects.create_user(
            username="parent_a", password="test-password"
        )
        self.sme_staff_user = self.User.objects.create_user(
            username="sme_staff_a", password="test-password"
        )
        self.system_admin_user = self.User.objects.create_superuser(
            username="system_admin", email="admin@example.com", password="test-password"
        )

        # User in org_b (for cross-org tests)
        self.org_b_user = self.User.objects.create_user(
            username="org_b_user", password="test-password"
        )

        # User profiles in org_a
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user,
            organization=self.org_a,
            phone_number="+256700000001",
        )
        self.instructor_profile = UserProfile.objects.create(
            user=self.instructor_user,
            organization=self.org_a,
            phone_number="+256700000002",
        )
        self.student_profile = UserProfile.objects.create(
            user=self.student_user,
            organization=self.org_a,
            phone_number="+256700000003",
        )
        self.parent_profile = UserProfile.objects.create(
            user=self.parent_user,
            organization=self.org_a,
            phone_number="+256700000004",
        )
        self.sme_staff_profile = UserProfile.objects.create(
            user=self.sme_staff_user,
            organization=self.org_a,
            phone_number="+256700000005",
        )
        self.system_admin_profile = UserProfile.objects.create(
            user=self.system_admin_user,
            organization=self.org_a,
            phone_number="+256700000006",
        )
        self.org_b_profile = UserProfile.objects.create(
            user=self.org_b_user,
            organization=self.org_b,
            phone_number="+256700000007",
        )

        # Role assignments in org_a
        OrganizationMembershipRole.objects.create(
            user_profile=self.admin_profile, role_code=MembershipRoleCode.ORG_ADMIN
        )
        OrganizationMembershipRole.objects.create(
            user_profile=self.instructor_profile,
            role_code=MembershipRoleCode.INSTRUCTOR,
        )
        OrganizationMembershipRole.objects.create(
            user_profile=self.student_profile, role_code=MembershipRoleCode.STUDENT
        )
        OrganizationMembershipRole.objects.create(
            user_profile=self.parent_profile, role_code=MembershipRoleCode.PARENT
        )
        OrganizationMembershipRole.objects.create(
            user_profile=self.sme_staff_profile,
            role_code=MembershipRoleCode.SME_STAFF,
        )

        # Subscription license in org_a
        self.license = SubscriptionLicense.objects.create(
            organization=self.org_a,
            product_code=SubscriptionProductCode.EDTECH_LMS,
            seat_capacity=10,
            status=LicenseStatus.ACTIVE,
        )

    def _headers(self, org_id=None, correlation_id=None):
        headers = {}
        if org_id is not None:
            headers[self.ORG_ID_HEADER] = str(org_id)
        if correlation_id is not None:
            headers[self.CORR_ID_HEADER] = str(correlation_id)
        return headers

    # ------------------------------------------------------------ 401 Unauthenticated

    def test_unauthenticated_get_returns_401(self):
        response = self.client.get(
            reverse("organization-list"), **self._headers(org_id=self.org_a.id)
        )
        self.assertEqual(response.status_code, 401)
        body = json.loads(response.content)
        self.assertEqual(body["errors"][0]["code"], "unauthenticated")

    # ------------------------------------------------------------ 400 Missing/Malformed Selector

    def test_missing_organization_selector_returns_400(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("organization-list"))
        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content)
        self.assertEqual(body["errors"][0]["code"], "missing_organization_selector")

    def test_malformed_organization_selector_returns_400(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse("organization-list"),
            **self._headers(org_id="not-a-uuid"),
        )
        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content)
        self.assertEqual(body["errors"][0]["code"], "invalid_organization_selector")

    # ------------------------------------------------------------ 404 Non-Member

    def test_non_member_gets_404_not_403(self):
        """P1.2.3-D1: same 404 for absent org or no matching membership."""
        self.client.force_login(self.org_b_user)
        response = self.client.get(
            reverse("organization-list"),
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 404)
        body = json.loads(response.content)
        self.assertEqual(body["errors"][0]["code"], "membership_not_found")

    def test_absent_organization_gets_404(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse("organization-list"),
            **self._headers(org_id="00000000-0000-0000-0000-000000000000"),
        )
        self.assertEqual(response.status_code, 404)

    # ------------------------------------------------------------ org_admin permissions

    def test_org_admin_can_view_organization(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse("organization-list"),
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 200)

    def test_org_admin_can_create_organization(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("organization-create"),
            data=json.dumps(
                {
                    "name": "New Org",
                    "org_type": "school",
                    "status": "pending",
                }
            ),
            content_type="application/json",
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 201)

    def test_org_admin_can_update_organization(self):
        self.client.force_login(self.admin_user)
        response = self.client.put(
            reverse("organization-update", args=[self.org_a.id]),
            data=json.dumps({"name": "Updated Org A"}),
            content_type="application/json",
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 200)

    def test_org_admin_cannot_delete_organization(self):
        self.client.force_login(self.admin_user)
        response = self.client.delete(
            reverse("organization-delete", args=[self.org_a.id]),
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 403)
        body = json.loads(response.content)
        self.assertEqual(body["errors"][0]["code"], "permission_denied")

    def test_org_admin_can_create_profile(self):
        new_user = self.User.objects.create_user(
            username="new_member", password="test-password"
        )
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("profile-create"),
            data=json.dumps(
                {
                    "user": str(new_user.id),
                    "phone_number": "+256700000099",
                }
            ),
            content_type="application/json",
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 201)

    def test_org_admin_can_update_profile(self):
        self.client.force_login(self.admin_user)
        response = self.client.put(
            reverse("profile-update", args=[self.student_profile.id]),
            data=json.dumps({"phone_number": "+256700000003-updated"}),
            content_type="application/json",
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------ view-only roles

    def test_instructor_can_view_organization(self):
        self.client.force_login(self.instructor_user)
        response = self.client.get(
            reverse("organization-list"),
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 200)

    def test_instructor_cannot_create_organization(self):
        self.client.force_login(self.instructor_user)
        response = self.client.post(
            reverse("organization-create"),
            data=json.dumps(
                {
                    "name": "Instructor Org",
                    "org_type": "school",
                    "status": "pending",
                }
            ),
            content_type="application/json",
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 403)
        body = json.loads(response.content)
        self.assertEqual(body["errors"][0]["code"], "permission_denied")

    def test_instructor_cannot_update_organization(self):
        self.client.force_login(self.instructor_user)
        response = self.client.put(
            reverse("organization-update", args=[self.org_a.id]),
            data=json.dumps({"name": "Hacked Name"}),
            content_type="application/json",
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 403)

    def test_instructor_cannot_delete_organization(self):
        self.client.force_login(self.instructor_user)
        response = self.client.delete(
            reverse("organization-delete", args=[self.org_a.id]),
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 403)

    def test_student_can_view_organization(self):
        self.client.force_login(self.student_user)
        response = self.client.get(
            reverse("organization-list"),
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_create_profile(self):
        new_user = self.User.objects.create_user(
            username="student_create_test", password="test-password"
        )
        self.client.force_login(self.student_user)
        response = self.client.post(
            reverse("profile-create"),
            data=json.dumps(
                {
                    "user": str(new_user.id),
                    "phone_number": "+256700000088",
                }
            ),
            content_type="application/json",
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 403)

    def test_parent_can_view_organization(self):
        self.client.force_login(self.parent_user)
        response = self.client.get(
            reverse("organization-list"),
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 200)

    def test_parent_cannot_create_license(self):
        self.client.force_login(self.parent_user)
        response = self.client.post(
            reverse("license-create"),
            data=json.dumps(
                {
                    "product_code": "EDTECH_LMS",
                    "seat_capacity": 5,
                    "status": "pending",
                }
            ),
            content_type="application/json",
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 403)

    def test_sme_staff_can_view_organization(self):
        self.client.force_login(self.sme_staff_user)
        response = self.client.get(
            reverse("organization-list"),
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 200)

    def test_sme_staff_cannot_update_profile(self):
        self.client.force_login(self.sme_staff_user)
        response = self.client.put(
            reverse("profile-update", args=[self.student_profile.id]),
            data=json.dumps({"phone_number": "+256700000003-hacked"}),
            content_type="application/json",
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 403)

    # ------------------------------------------------------------ Cross-organization access

    def test_cross_org_view_returns_403(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse("organization-list"),
            **self._headers(org_id=self.org_b.id),
        )
        self.assertEqual(response.status_code, 404)

    def test_cross_org_profile_access_returns_403(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse("profile-retrieve", args=[self.org_b_profile.id]),
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 403)
        body = json.loads(response.content)
        self.assertEqual(body["errors"][0]["code"], "permission_denied")

    def test_cross_org_role_access_returns_403(self):
        self.client.force_login(self.admin_user)
        org_b_role = OrganizationMembershipRole.objects.create(
            user_profile=self.org_b_profile,
            role_code=MembershipRoleCode.ORG_ADMIN,
        )
        response = self.client.get(
            reverse("role-retrieve", args=[org_b_role.id]),
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 403)

    def test_cross_org_license_access_returns_403(self):
        org_b_license = SubscriptionLicense.objects.create(
            organization=self.org_b,
            product_code=SubscriptionProductCode.EDTECH_LMS,
            seat_capacity=5,
            status=LicenseStatus.ACTIVE,
        )
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse("license-retrieve", args=[org_b_license.id]),
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 403)

    # ------------------------------------------------------------ system_admin (superuser)

    def test_system_admin_can_delete_profile(self):
        self.client.force_login(self.system_admin_user)
        temp_user = self.User.objects.create_user(
            username="temp_delete", password="test-password"
        )
        temp_profile = UserProfile.objects.create(
            user=temp_user,
            organization=self.org_a,
            phone_number="+256700000050",
        )
        response = self.client.delete(
            reverse("profile-delete", args=[temp_profile.id]),
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 204)

    def test_system_admin_can_delete_role(self):
        self.client.force_login(self.system_admin_user)
        temp_user = self.User.objects.create_user(
            username="temp_role_delete", password="test-password"
        )
        temp_profile = UserProfile.objects.create(
            user=temp_user,
            organization=self.org_a,
            phone_number="+256700000051",
        )
        temp_role = OrganizationMembershipRole.objects.create(
            user_profile=temp_profile,
            role_code=MembershipRoleCode.STUDENT,
        )
        response = self.client.delete(
            reverse("role-delete", args=[temp_role.id]),
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 204)

    def test_system_admin_can_delete_license(self):
        self.client.force_login(self.system_admin_user)
        temp_license = SubscriptionLicense.objects.create(
            organization=self.org_a,
            product_code=SubscriptionProductCode.CRM_BASIC,
            seat_capacity=1,
            status=LicenseStatus.PENDING,
        )
        response = self.client.delete(
            reverse("license-delete", args=[temp_license.id]),
            **self._headers(org_id=self.org_a.id),
        )
        self.assertEqual(response.status_code, 204)
