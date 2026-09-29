
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class CustomUser(AbstractUser):

    email = models.EmailField(unique=True)

    phone_number = models.CharField(
        max_length=15,
        unique=True
    )

    email_verified = models.BooleanField(
        default=False
    )

    phone_verified = models.BooleanField(
        default=False
    )

    email_otp = models.CharField(
        max_length=6,
        blank=True,
        null=True
    )

    phone_otp = models.CharField(
        max_length=6,
        blank=True,
        null=True
    )

    email_otp_created_at = models.DateTimeField(
        blank=True,
        null=True
    )

    phone_otp_created_at = models.DateTimeField(
        blank=True,
        null=True
    )

    # Forgot Password fields
    reset_otp = models.CharField(
        max_length=6,
        blank=True,
        null=True
    )

    reset_otp_created_at = models.DateTimeField(
        blank=True,
        null=True
    )

    payment_pin = models.CharField(
        max_length=128,
        blank=True,
        null=True
    )

    credit_score = models.PositiveIntegerField(
        default=750
    )
    profile_photo = models.ImageField(
    upload_to='profile_photos/',
    blank=True,
    null=True
    )
class BankAccount(models.Model):

    BANK_CHOICES = [
        ('SBI', 'State Bank of India'),
        ('HDFC', 'HDFC Bank'),
        ('ICICI', 'ICICI Bank'),
    ]
    user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name='bank_accounts'
    )

    bank_name = models.CharField(
        max_length=20,
        choices=BANK_CHOICES
    )

    account_number = models.CharField(
        max_length=20
    )

    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
class Payment(models.Model):
    transaction_id = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        null=True
    )

    PAYMENT_TYPES = [
        ('MOBILE', 'Mobile Recharge'),
        ('RENT', 'Rent Payment'),
        ('ELECTRICITY', 'Electricity Bill'),
        ('LOAN', 'Loan Repayment'),
        ('OTHER', 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPES
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    cashback = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    default=0
    )
    reward_points = models.PositiveIntegerField(
    default=0
    )

    description = models.CharField(
        max_length=255,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        default='SUCCESS'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.payment_type} - ₹{self.amount}"
    

    