from django.urls import path
from . import views
from accounts import views


urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path(
    'forgot-password/',
    views.forgot_password,
    name='forgot_password'
),

path(
    'reset-password/',
    views.reset_password,
    name='reset_password'
),
path('dashboard/', views.dashboard, name='dashboard'),
path(
    'ai-router/',
    views.ai_router,
    name='ai_router'
),
path('confirm-payment/', views.confirm_payment, name='confirm_payment'),
path(
    'credit-score/',
    views.credit_score,
    name='credit_score'
),
path(
    'credit-score/',
    views.credit_score,
    name='credit_score'
),
path(
    'payments/',
    views.payments,
    name='payments'
),
path(
    'bank-accounts/',
    views.bank_accounts,
    name='bank_accounts'
),
path(
    'recharge-bills/',
    views.recharge_bills,
    name='recharge_bills'
),
path(
    'payment-pin/',
    views.payment_pin,
    name='payment_pin'
),
path(
    'set-payment-pin/',
    views.set_payment_pin,
    name='set_payment_pin'
),
path(
    'profile/',
    views.my_profile,
    name='my_profile'
),
path(
    'change-password/',
    views.change_password,
    name='change_password'
),
path(
    'profile/upload-photo/',
    views.upload_profile_photo,
    name='upload_profile_photo'
),
path(
    'change-password/',
    views.change_password,
    name='change_password'
),
path(
    'add-bank-account/',
    views.add_bank_account,
    name='add_bank_account'
),
path(
    'edit-bank-account/<int:account_id>/',
    views.edit_bank_account,
    name='edit_bank_account'
),
path(
    'payment-history/',
    views.payment_history,
    name='payment_history'
),
path(
    'payments/<int:payment_id>/',
    views.payment_detail,
    name='payment_detail'
),
]