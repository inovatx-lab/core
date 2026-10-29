import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class OrganizationType(models.TextChoices):
    INDIVIDUAL = "individual", "Individual"
    SCHOOL = "school", "School"
    SME = "sme", "SME"
    NGO = "ngo", "NGO"
    ENTERPRISE = "enterprise", "Enterprise"


class OrganizationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    EXPIRED = "expired", "Expired"
    CANCELLED = "cancelled", "Cancelled"


class MembershipRoleCode(models.TextChoices):
    ORG_ADMIN = "org_admin", "Organization admin"
    INSTRUCTOR = "instructor", "Instructor"
    STUDENT = "student", "Student"
    PARENT = "parent", "Parent"
    SME_STAFF = "sme_staff", "SME staff"


class SubscriptionProductCode(models.TextChoices):
    EDTECH_LMS = "EDTECH_LMS", "EdTech LMS"
    CRM_BASIC = "CRM_BASIC", "CRM Basic"
    AI_PRO = "AI_PRO", "AI Pro"


class LicenseStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"
    SUSPENDED = "suspended", "Suspended"
    CANCELLED = "cancelled", "Cancelled"


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Organization(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    org_type = models.CharField(
        max_length=10,
        choices=OrganizationType.choices,
    )
    status = models.CharField(
        max_length=9,
        choices=OrganizationStatus.choices,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(org_type__in=OrganizationType.values),
                name="core_org_type_valid",
            ),
            models.CheckConstraint(
                condition=Q(status__in=OrganizationStatus.values),
                name="core_org_status_valid",
            ),
        ]

    def __str__(self):
        return self.name


class UserProfile(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="organization_memberships",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="memberships",
    )
    phone_number = models.CharField(max_length=32)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "organization"),
                name="uq_profile_user_organization",
            )
        ]

    def __str__(self):
        return f"{self.user} @ {self.organization}"


class OrganizationMembershipRole(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="role_assignments",
    )
    role_code = models.CharField(
        max_length=10,
        choices=MembershipRoleCode.choices,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(role_code__in=MembershipRoleCode.values),
                name="core_membership_role_valid",
            ),
            models.UniqueConstraint(
                fields=("user_profile", "role_code"),
                name="uq_membership_role_code",
            ),
        ]

    def __str__(self):
        return f"{self.user_profile} - {self.role_code}"


class SubscriptionLicense(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="licenses",
    )
    product_code = models.CharField(
        max_length=10,
        choices=SubscriptionProductCode.choices,
    )
    seat_capacity = models.IntegerField()
    moodle_cohort_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=9, choices=LicenseStatus.choices)
    ai_monthly_interaction_allowance_per_learner_seat = models.IntegerField(
        null=True,
        blank=True,
    )
    ai_daily_interaction_cap_per_learner_seat = models.IntegerField(
        null=True,
        blank=True,
    )
    valid_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(product_code__in=SubscriptionProductCode.values),
                name="core_license_product_valid",
            ),
            models.CheckConstraint(
                condition=Q(status__in=LicenseStatus.values),
                name="core_license_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(seat_capacity__gte=1),
                name="core_license_seat_capacity_positive",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        product_code=SubscriptionProductCode.AI_PRO,
                        ai_monthly_interaction_allowance_per_learner_seat__isnull=False,
                        ai_monthly_interaction_allowance_per_learner_seat__gt=0,
                        ai_daily_interaction_cap_per_learner_seat__isnull=False,
                        ai_daily_interaction_cap_per_learner_seat__gt=0,
                    )
                    | (
                        ~Q(product_code=SubscriptionProductCode.AI_PRO)
                        & Q(
                            ai_monthly_interaction_allowance_per_learner_seat__isnull=True,
                            ai_daily_interaction_cap_per_learner_seat__isnull=True,
                        )
                    )
                ),
                name="core_license_ai_allowances_match_product",
            ),
            models.UniqueConstraint(
                fields=("organization", "product_code"),
                name="uq_license_organization_product",
            ),
        ]

    def __str__(self):
        return f"{self.organization} - {self.product_code}"


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class PaymentGatewayCode(models.TextChoices):
    MOBILE_MONEY = "mobile_money", "Mobile Money"
    CARD = "card", "Card"


class PaymentEventType(models.TextChoices):
    INITIATED = "payment.initiated", "Payment initiated"
    SUCCEEDED = "payment.succeeded", "Payment succeeded"
    FAILED = "payment.failed", "Payment failed"
    CANCELLED = "payment.cancelled", "Payment cancelled"
    RECONCILED = "payment.reconciled", "Payment reconciled"


class Payment(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    license = models.ForeignKey(
        SubscriptionLicense,
        on_delete=models.PROTECT,
        related_name="payments",
        null=True,
        blank=True,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    gateway = models.CharField(
        max_length=20,
        choices=PaymentGatewayCode.choices,
    )
    gateway_reference = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=9,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    idempotency_key = models.CharField(max_length=255, unique=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=PaymentStatus.values),
                name="core_payment_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(gateway__in=PaymentGatewayCode.values),
                name="core_payment_gateway_valid",
            ),
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="core_payment_amount_positive",
            ),
        ]

    def __str__(self):
        return f"{self.id} - {self.status}"


class PaymentEvent(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(
        max_length=30,
        choices=PaymentEventType.choices,
    )
    event_id = models.UUIDField()
    payload = models.JSONField(default=dict)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(event_type__in=PaymentEventType.values),
                name="core_payment_event_type_valid",
            ),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.payment_id}"
