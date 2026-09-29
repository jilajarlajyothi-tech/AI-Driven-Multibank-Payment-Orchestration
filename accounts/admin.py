

from django.contrib import admin
from .models import BankAccount, Payment


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