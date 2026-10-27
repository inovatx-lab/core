from django.contrib import admin

from .models import (
    Organization,
    OrganizationMembershipRole,
    SubscriptionLicense,
    UserProfile,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "org_type", "status", "created_at")
    list_filter = ("org_type", "status")
    search_fields = ("name",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "phone_number", "created_at")
    list_filter = ("organization",)
    list_select_related = ("user", "organization")
    search_fields = ("user__username", "user__email", "organization__name")


@admin.register(OrganizationMembershipRole)
class OrganizationMembershipRoleAdmin(admin.ModelAdmin):
    list_display = ("user_profile", "role_code", "created_at")
    list_filter = ("role_code", "user_profile__organization")
    list_select_related = ("user_profile", "user_profile__organization", "user_profile__user")
    search_fields = (
        "user_profile__user__username",
        "user_profile__user__email",
        "user_profile__organization__name",
    )


@admin.register(SubscriptionLicense)
class SubscriptionLicenseAdmin(admin.ModelAdmin):
    list_display = ("organization", "product_code", "status", "seat_capacity", "valid_until")
    list_filter = ("product_code", "status")
    list_select_related = ("organization",)
    search_fields = ("organization__name",)
