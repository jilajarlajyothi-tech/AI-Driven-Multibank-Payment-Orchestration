
from django.urls import path
from . import views


urlpatterns = [
    # Home → Login
    path('', views.user_login, name='home'),

    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # AI Router
    path('ai-router/', views.ai_router, name='ai_router'),

    # Payments
    path('confirm-payment/', views.confirm_payment, name='confirm_payment'),
    path('payments/', views.payments, name='payments'),
    path('payment-history/', views.payment_history, name='payment_history'),
    path('payments/<int:payment_id>/', views.payment_detail, name='payment_detail'),

    # Credit Score
    path('credit-score/', views.credit_score, name='credit_score'),

    # Bank Accounts
    path('bank-accounts/', views.bank_accounts, name='bank_accounts'),
    path('add-bank-account/', views.add_bank_account, name='add_bank_account'),
    path(
        'edit-bank-account/<int:account_id>/',
        views.edit_bank_account,
        name='edit_bank_account'
    ),

    # Recharge & Bills
    path('recharge-bills/', views.recharge_bills, name='recharge_bills'),

    # Payment PIN
    path('payment-pin/', views.payment_pin, name='payment_pin'),
    path('set-payment-pin/', views.set_payment_pin, name='set_payment_pin'),

    # Profile
    path('profile/', views.my_profile, name='my_profile'),
    path(
        'profile/upload-photo/',
        views.upload_profile_photo,
        name='upload_profile_photo'
    ),

    # Password
    path('change-password/', views.change_password, name='change_password'),
]

