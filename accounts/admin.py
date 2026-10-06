from django.contrib import admin
from .models import BankAccount, Payment, CustomUser
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
        'user',
        'payment_type',
        'amount',
        'status',
        'created_at',
    )

    list_filter = (
        'payment_type',
        'status',
    )

    search_fields = (
        'user__username',
        'description',
    )

    ordering = (
        '-created_at',
    )