from django.contrib import admin
from .models import BankAccount, Payment, CustomUser, RiskCompliance
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):

    list_display = (
        'username',
        'email',
        'phone_number',
        'email_verified',
        'phone_verified',
        'credit_score',
        'is_active',
        'date_joined',
    )

    list_filter = (
        'email_verified',
        'phone_verified',
        'is_active',
        'is_staff',
    )

    search_fields = (
        'username',
        'email',
        'phone_number',
    )

    ordering = (
        '-date_joined',
    )

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'bank_name',
        'account_number',
        'balance',
        'is_active',
        'created_at',
    )

    list_filter = (
        'bank_name',
        'is_active',
    )

    search_fields = (
        'user__username',
        'account_number',
    )

    ordering = (
        '-created_at',
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        'transaction_id',
        'user',
        'payment_type',
        'amount',
        'status',
        'risk_level',
        'fraud_probability',
        'cashback',
        'reward_points',
        'created_at',
    )

    list_filter = (
        'payment_type',
        'status',
        'risk_level',
        'created_at',
    )

    search_fields = (
        'transaction_id',
        'user__username',
        'user__email',
        'description',
    )

    readonly_fields = (
        'transaction_id',
        'created_at',
        'fraud_probability',
        'risk_level',
        'fraud_prediction',
    )

    ordering = (
        '-created_at',
    )

    list_per_page = 25
@admin.register(RiskCompliance)
class RiskComplianceAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'payment',
        'risk_level',
        'risk_score',
        'fraud_probability',
        'compliance_score',
        'aml_status',
        'transaction_status',
        'created_at',
    )

    list_filter = (
        'risk_level',
        'aml_status',
        'transaction_status',
        'created_at',
    )

    search_fields = (
        'user__username',
        'user__email',
        'payment__transaction_id',
        'notes',
    )

    readonly_fields = (
        'created_at',
    )

    ordering = (
        '-created_at',
    )

    list_per_page = 25