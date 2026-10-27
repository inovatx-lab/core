import time

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
