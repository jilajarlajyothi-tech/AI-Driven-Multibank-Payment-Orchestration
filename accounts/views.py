import random
import uuid
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from .models import CustomUser
from django.db.models import Sum , Q
from .models import BankAccount,Payment
from accounts.models import CustomUser
from ml.fraud_detector import detect_fraud
from decimal import Decimal
from django.db import transaction
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import update_session_auth_hash
from decimal import Decimal
from .models import Payment

def register(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('register')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('register')

        if CustomUser.objects.filter(phone_number=phone_number).exists():
            messages.error(request, 'Phone number already registered.')
            return redirect('register')

        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            phone_number=phone_number,
            password=password
        )

        user.email_verified = False
        user.phone_verified = False
        user.save()

        messages.success(request, 'Account created successfully!')

        return redirect('register')

    return render(request, 'accounts/register.html')
def user_login(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect('dashboard')

        else:

            messages.error(
                request,
                'Invalid username or password.'
            )

            return redirect('login')

    return render(request, 'accounts/login.html')
@never_cache
def forgot_password(request):

    if request.method == 'POST':

        email = request.POST.get('email', '').strip().lower()

        # Check whether email exists
        try:
            user = CustomUser.objects.get(email=email)

        except CustomUser.DoesNotExist:
            messages.error(
                request,
                'No account found with this email address.'
            )

            return render(
                request,
                'accounts/forgot_password.html'
            )

        # Generate 6 digit OTP
        otp = str(random.randint(100000, 999999))

        # Save OTP
        user.reset_otp = otp
        user.reset_otp_created_at = timezone.now()

        user.save(
            update_fields=[
                'reset_otp',
                'reset_otp_created_at'
            ]
        )

        # Save user ID in session
        request.session['password_reset_user_id'] = user.id

        # Email subject
        subject = 'MultiBank AI - Password Reset OTP'

        # Email message
        message = f"""
Hello {user.username},

Your MultiBank AI password reset OTP is:

{otp}

This OTP is valid for 10 minutes.

If you did not request a password reset,
please ignore this email.

Regards,
MultiBank AI
"""

        # Send email
        try:

            send_mail(
                subject,
                message,
                None,
                [user.email],
                fail_silently=False
            )

            messages.success(
                request,
                'OTP has been sent to your email.'
            )

            return redirect('reset_password')

        except Exception as e:

            print("EMAIL ERROR:", e)

            messages.error(
                request,
                'Unable to send OTP. Please check your email configuration.'
            )

            return render(
                request,
                'accounts/forgot_password.html'
            )

    # GET request
    return render(
        request,
        'accounts/forgot_password.html'
    )


@never_cache
def reset_password(request):

    # Get user ID from session
    user_id = request.session.get(
        'password_reset_user_id'
    )

    if not user_id:

        messages.error(
            request,
            'Please request a password reset first.'
        )

        return redirect('forgot_password')

    # Find user
    try:

        user = CustomUser.objects.get(
            id=user_id
        )

    except CustomUser.DoesNotExist:

        messages.error(
            request,
            'Invalid password reset request.'
        )

        return redirect('forgot_password')

    # When Reset Password form is submitted
    if request.method == 'POST':

        otp = request.POST.get(
            'otp',
            ''
        ).strip()

        password = request.POST.get(
            'password',
            ''
        )

        confirm_password = request.POST.get(
            'confirm_password',
            ''
        )

        # Check OTP exists
        if not user.reset_otp:

            messages.error(
                request,
                'No OTP found. Please request a new OTP.'
            )

            return render(
                request,
                'accounts/reset_password.html'
            )

        # Check OTP time
        if not user.reset_otp_created_at:

            messages.error(
                request,
                'Invalid OTP. Please request a new OTP.'
            )

            return render(
                request,
                'accounts/reset_password.html'
            )

        # Check OTP expiry
        otp_age = (
            timezone.now()
            - user.reset_otp_created_at
        )

        if otp_age > timedelta(minutes=10):

            messages.error(
                request,
                'OTP has expired. Please request a new OTP.'
            )

            return render(
                request,
                'accounts/reset_password.html'
            )

        # Check OTP
        if otp != user.reset_otp:

            messages.error(
                request,
                'Invalid OTP.'
            )

            return render(
                request,
                'accounts/reset_password.html'
            )

        # Password length
        if len(password) < 8:

            messages.error(
                request,
                'Password must contain at least 8 characters.'
            )

            return render(
                request,
                'accounts/reset_password.html'
            )

        # Check passwords
        if password != confirm_password:

            messages.error(
                request,
                'Passwords do not match.'
            )

            return render(
                request,
                'accounts/reset_password.html'
            )

        # Change password
        user.set_password(password)

        # Remove used OTP
        user.reset_otp = None
        user.reset_otp_created_at = None

        user.save()

        # Remove session
        request.session.pop(
            'password_reset_user_id',
            None
        )

        messages.success(
            request,
            'Password changed successfully. Please login with your new password.'
        )

        return redirect('login')

    return render(
        request,
        'accounts/reset_password.html'
    )
def dashboard(request):

    # Total balance
    total_balance = BankAccount.objects.filter(
        user=request.user,
        is_active=True
    ).aggregate(
        total=Sum('balance')
    )['total'] or 0

    # Current date
    today = timezone.localdate()

    # This month's successful payments
    this_month_spent = Payment.objects.filter(
        user=request.user,
        created_at__year=today.year,
        created_at__month=today.month,
        status='SUCCESS'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0
    credit_score = getattr(request.user, 'credit_score', 0)
    # Total cashback earned
    cashback_earned = Payment.objects.filter(
        user=request.user,
        status='SUCCESS'
    ).aggregate(
        total=Sum('cashback')
    )['total'] or 0
    # Total reward points
    reward_points = Payment.objects.filter(
        user=request.user,
        status='SUCCESS'
    ).aggregate(
        total=Sum('reward_points')
    )['total'] or 0

    # Latest 5 payments
    recent_payments = Payment.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]

    return render(
        request,
        'dashboard/dashboard.html',
        {
            'total_balance': total_balance,
            'this_month_spent': this_month_spent,
            'recent_payments': recent_payments,
            'cashback_earned': cashback_earned,
            'reward_points': reward_points,
            'credit_score': credit_score,
        }
    )
@login_required
def ai_router(request):

    routing_result = None

    # ============================================================
    # SERVICE TYPE
    # ============================================================

    selected_type = request.GET.get(
        'type',
        request.POST.get('payment_type', 'OTHER')
    )

    payment_types = {
        'MOBILE': 'Mobile Recharge',
        'ELECTRICITY': 'Electricity Bill',
        'RENT': 'Rent Payment',
        'LOAN': 'Loan Repayment',
        'OTHER': 'Internet / Other Payment',
    }

    selected_type_name = payment_types.get(
        selected_type,
        'Other Payment'
    )

    # ============================================================
    # PAYMENT PROCESSING
    # ============================================================

    if request.method == 'POST':

        amount = float(
            request.POST.get('amount', 0)
        )

        payment_type = request.POST.get(
            'payment_type',
            selected_type
        )

        # ========================================================
        # SERVICE DETAILS
        # ========================================================

        mobile_number = request.POST.get(
            'mobile_number',
            ''
        ).strip()

        mobile_operator = request.POST.get(
            'mobile_operator',
            ''
        ).strip()

        consumer_number = request.POST.get(
            'consumer_number',
            ''
        ).strip()

        electricity_provider = request.POST.get(
            'electricity_provider',
            ''
        ).strip()

        rent_recipient = request.POST.get(
            'rent_recipient',
            ''
        ).strip()

        rent_reference = request.POST.get(
            'rent_reference',
            ''
        ).strip()

        loan_account = request.POST.get(
            'loan_account',
            ''
        ).strip()

        loan_provider = request.POST.get(
            'loan_provider',
            ''
        ).strip()

        other_description = request.POST.get(
            'other_description',
            ''
        ).strip()

        # ========================================================
        # CREATE SERVICE DESCRIPTION
        # ========================================================

        service_description = ''

        if payment_type == 'MOBILE':

            service_description = (
                f'Mobile Recharge | '
                f'Number: {mobile_number} | '
                f'Operator: {mobile_operator}'
            )

        elif payment_type == 'ELECTRICITY':

            service_description = (
                f'Electricity Bill | '
                f'Consumer: {consumer_number} | '
                f'Provider: {electricity_provider}'
            )

        elif payment_type == 'RENT':

            service_description = (
                f'Rent Payment | '
                f'Recipient: {rent_recipient} | '
                f'Reference: {rent_reference}'
            )

        elif payment_type == 'LOAN':

            service_description = (
                f'Loan Repayment | '
                f'Account: {loan_account} | '
                f'Lender: {loan_provider}'
            )

        else:

            service_description = (
                f'Other Payment | '
                f'{other_description}'
            )

        # ========================================================
        # EXISTING BANK ACCOUNT LOGIC
        # DO NOT CHANGE
        # ========================================================

        bank_accounts = BankAccount.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('balance')

        if bank_accounts.exists():

            # ====================================================
            # EXISTING ML TRANSACTION DATA
            # ====================================================

            transaction_data = {
                "Time": 0,
                "V1": 0,
                "V2": 0,
                "V3": 0,
                "V4": 0,
                "V5": 0,
                "V6": 0,
                "V7": 0,
                "V8": 0,
                "V9": 0,
                "V10": 0,
                "V11": 0,
                "V12": 0,
                "V13": 0,
                "V14": 0,
                "V15": 0,
                "V16": 0,
                "V17": 0,
                "V18": 0,
                "V19": 0,
                "V20": 0,
                "V21": 0,
                "V22": 0,
                "V23": 0,
                "V24": 0,
                "V25": 0,
                "V26": 0,
                "V27": 0,
                "V28": 0,
                "Amount": amount
            }

            # ====================================================
            # EXISTING FRAUD DETECTION
            # ====================================================

            fraud_result = detect_fraud(
                transaction_data
            )

            fraud_probability = fraud_result[
                'fraud_probability'
            ]

            risk_level = fraud_result[
                'risk_level'
            ]

            prediction = fraud_result[
                'prediction'
            ]

            # ====================================================
            # HIGH RISK
            # ====================================================

            if risk_level == "HIGH":

                routing_result = {

                    'bank': 'Payment Blocked',

                    'amount': amount,

                    'status': 'PAYMENT BLOCKED',

                    'risk': risk_level,

                    'fraud_probability':
                        fraud_probability,

                    'prediction':
                        prediction,

                    'payment_type':
                        payment_type,

                    'reason': (
                        'The ML fraud detection model '
                        'identified this transaction as '
                        'high risk. Payment routing has '
                        'been blocked.'
                    )
                }

            else:

                # =================================================
                # EXISTING BANK BALANCE CHECK
                # =================================================

                eligible_banks = []

                for account in bank_accounts:

                    if float(account.balance) >= amount:

                        eligible_banks.append(
                            account
                        )

                # =================================================
                # NO ELIGIBLE BANK
                # =================================================

                if not eligible_banks:

                    routing_result = {

                        'bank':
                            'Insufficient Balance',

                        'amount':
                            amount,

                        'status':
                            'ROUTE UNAVAILABLE',

                        'risk':
                            risk_level,

                        'fraud_probability':
                            fraud_probability,

                        'prediction':
                            prediction,

                        'payment_type':
                            payment_type,

                        'reason': (
                            'None of your active bank '
                            'accounts has sufficient '
                            'balance for this payment.'
                        )
                    }

                else:

                    # =============================================
                    # EXISTING BANK SELECTION
                    # =============================================

                    selected_bank = min(
                        eligible_banks,
                        key=lambda account:
                            float(account.balance)
                    )

                    # =============================================
                    # SAVE EVERYTHING NEEDED FOR NEXT STEP
                    # =============================================

                    request.session[
                        'pending_payment'
                    ] = {

                        'bank_id':
                            selected_bank.id,

                        'amount':
                            str(amount),

                        'payment_type':
                            payment_type,

                        'service_description':
                            service_description,

                        'mobile_number':
                            mobile_number,

                        'mobile_operator':
                            mobile_operator,

                        'consumer_number':
                            consumer_number,

                        'electricity_provider':
                            electricity_provider,

                        'rent_recipient':
                            rent_recipient,

                        'rent_reference':
                            rent_reference,

                        'loan_account':
                            loan_account,

                        'loan_provider':
                            loan_provider,

                        'other_description':
                            other_description,
                    }

                    # =============================================
                    # ROUTING RESULT
                    # =============================================

                    routing_result = {

                        'bank':
                            selected_bank.get_bank_name_display(),

                        'amount':
                            amount,

                        'status':
                            'ROUTE AVAILABLE',

                        'risk':
                            risk_level,

                        'fraud_probability':
                            fraud_probability,

                        'prediction':
                            prediction,

                        'payment_type':
                            payment_type,

                        'reason': (
                            'AI selected the bank with '
                            'sufficient available balance '
                            'while considering the ML '
                            'transaction risk.'
                        )
                    }

        # ========================================================
        # NO ACTIVE BANK ACCOUNT
        # ========================================================

        else:

            routing_result = {

                'bank':
                    'No Bank Account',

                'amount':
                    amount,

                'status':
                    'ROUTE UNAVAILABLE',

                'risk':
                    'HIGH',

                'fraud_probability':
                    100,

                'prediction':
                    1,

                'payment_type':
                    payment_type,

                'reason': (
                    'Please add an active bank account first.'
                )
            }

    # ============================================================
    # RENDER PAGE
    # ============================================================

    return render(
        request,
        'dashboard/ai_router.html',
        {
            'routing_result':
                routing_result,

            'selected_type':
                selected_type,

            'selected_type_name':
                selected_type_name,
        }
    )
        # Your existing AI routing code continues here...
def credit_score(request):
    credit_score = request.user.credit_score

    score_percentage = (credit_score / 900) * 100

    # Get user's payments
    payments = Payment.objects.filter(
        user=request.user
    )

    total_payments = payments.count()

    successful_payments = payments.filter(
        status='SUCCESS'
    ).count()

    # Payment history status
    if total_payments == 0:
        payment_history = "No Payment History"
    else:
        success_percentage = (
            successful_payments / total_payments
        ) * 100

        if success_percentage >= 90:
            payment_history = "Excellent"
        elif success_percentage >= 75:
            payment_history = "Good"
        elif success_percentage >= 50:
            payment_history = "Fair"
        else:
            payment_history = "Needs Improvement"

    # Credit score status
    if credit_score >= 750:
        score_status = "Excellent"
    elif credit_score >= 650:
        score_status = "Good"
    elif credit_score >= 550:
        score_status = "Fair"
    else:
        score_status = "Needs Improvement"
        # Calculate credit utilization
    total_balance = BankAccount.objects.filter(
        user=request.user,
        is_active=True
    ).aggregate(
        total=Sum('balance')
    )['total'] or 0

    monthly_spending = payments.filter(
        status='SUCCESS',
        created_at__year=timezone.localdate().year,
        created_at__month=timezone.localdate().month
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    if total_balance > 0:
        utilization_percentage = (
            float(monthly_spending) / float(total_balance)
        ) * 100
    else:
        utilization_percentage = 0

    if utilization_percentage <= 30:
        credit_utilization = "Low"
    elif utilization_percentage <= 60:
        credit_utilization = "Moderate"
    elif utilization_percentage <= 80:
        credit_utilization = "High"
    else:
        credit_utilization = "Very High"
        # Recent payment status
    recent_payments = payments.order_by('-created_at')[:5]

    late_or_failed = payments.filter(
        status__in=['FAILED', 'PENDING']
    ).count()

    if not recent_payments:
        recent_payment_status = "No Recent Payments"
    elif late_or_failed == 0:
        recent_payment_status = "On Time"
    elif late_or_failed <= 2:
        recent_payment_status = "Needs Attention"
    else:
        recent_payment_status = "Multiple Issues"
        # Dynamic breakdown percentages

    # Payment history percentage
    if total_payments > 0:
        payment_history_percentage = (
            successful_payments / total_payments
        ) * 100
    else:
        payment_history_percentage = 0

    # Credit utilization percentage
    # Lower utilization is better, so convert it to a health score.
    utilization_health = max(
        0,
        100 - utilization_percentage
    )

    # Account balance health
    if total_balance > 0:
        balance_health = min(
            100,
            (float(total_balance) / 50000) * 100
        )
    else:
        balance_health = 0

    # Payment activity
    payment_activity_percentage = min(
        100,
        total_payments * 10
    )
        # Credit score improvement tips
    improvement_tips = []

    if credit_score < 650:
        improvement_tips.append(
            "Make all payments on time and avoid missed payments."
        )

    if utilization_percentage > 30:
        improvement_tips.append(
            "Reduce your monthly payment usage compared with your available balance."
        )

    if total_balance == 0:
        improvement_tips.append(
            "Add an active bank account with a balance to build your financial profile."
        )

    if total_payments < 5:
        improvement_tips.append(
            "Maintain regular payment activity to build a stronger payment history."
        )

    if not improvement_tips:
        improvement_tips.append(
            "Continue making payments on time and maintain healthy account usage."
        )

    return render(
        request,
        'dashboard/credit_score.html',
        {
            'credit_score': credit_score,
            'score_percentage': score_percentage,
            'score_status': score_status,
            'payment_history': payment_history,
            'credit_utilization': credit_utilization,
            'recent_payment_status': recent_payment_status,
            'payment_history_percentage': payment_history_percentage,
            'utilization_health': utilization_health,
            'balance_health': balance_health,
            'payment_activity_percentage': payment_activity_percentage,
            'improvement_tips': improvement_tips,
        }
    )
@login_required
def confirm_payment(request):

    # ============================================================
    # GET PENDING PAYMENT
    # ============================================================

    pending_payment = request.session.get(
        'pending_payment'
    )

    if not pending_payment:
        return redirect('ai_router')


    # ============================================================
    # PAYMENT DETAILS
    # ============================================================

    try:
        amount = Decimal(
            pending_payment['amount']
        )

        bank_id = pending_payment['bank_id']

        payment_type = pending_payment[
            'payment_type'
        ]

    except (KeyError, InvalidOperation):

        request.session.pop(
            'pending_payment',
            None
        )

        return redirect('ai_router')


    # ============================================================
    # SERVICE DESCRIPTION
    # ============================================================

    service_description = pending_payment.get(
        'service_description',
        ''
    )


    # ============================================================
    # PAYMENT PIN VERIFICATION
    # ============================================================

    if not request.session.get(
        'payment_pin_verified'
    ):
        return redirect('payment_pin')


    # ============================================================
    # PROCESS PAYMENT
    # ============================================================

    try:

        with transaction.atomic():

            account = BankAccount.objects.get(
                id=bank_id,
                user=request.user,
                is_active=True
            )


            # ====================================================
            # FINAL BALANCE CHECK
            # ====================================================

            if account.balance < amount:

                request.session.pop(
                    'pending_payment',
                    None
                )

                request.session.pop(
                    'payment_pin_verified',
                    None
                )

                return render(
                    request,
                    'dashboard/payment_result.html',
                    {
                        'success': False,
                        'message':
                            'Insufficient balance for this payment.'
                    }
                )


            # ====================================================
            # DEDUCT AMOUNT
            # ====================================================

            account.balance -= amount

            account.save(
                update_fields=['balance']
            )


            # ====================================================
            # GENERATE TRANSACTION ID
            # ====================================================

            transaction_id = (
                'TXN' +
                uuid.uuid4().hex[:12].upper()
            )


            # ====================================================
            # CREATE PAYMENT RECORD
            # ====================================================

            payment = Payment.objects.create(

                transaction_id=
                    transaction_id,

                user=
                    request.user,

                payment_type=
                    payment_type,

                amount=
                    amount,

                cashback=
                    0,

                reward_points=
                    0,

                description=
                    service_description,

                status=
                    'SUCCESS'
            )


        # ========================================================
        # CLEAR SESSION DATA
        # ========================================================

        request.session.pop(
            'pending_payment',
            None
        )

        request.session.pop(
            'payment_pin_verified',
            None
        )


        # ========================================================
        # SUCCESS PAGE
        # ========================================================

        return render(
            request,
            'dashboard/payment_result.html',
            {
                'success':
                    True,

                'amount':
                    amount,

                'bank':
                    account.get_bank_name_display(),

                'payment_type':
                    payment_type,

                'transaction_id':
                    payment.transaction_id,

                'description':
                    service_description,
            }
        )


    # ============================================================
    # BANK ACCOUNT NOT FOUND
    # ============================================================

    except BankAccount.DoesNotExist:

        request.session.pop(
            'pending_payment',
            None
        )

        request.session.pop(
            'payment_pin_verified',
            None
        )

        return render(
            request,
            'dashboard/payment_result.html',
            {
                'success': False,

                'message':
                    'Selected bank account is no longer available.'
            }
        )


    # ============================================================
    # UNEXPECTED ERROR
    # ============================================================

    except Exception as e:

        return render(
            request,
            'dashboard/payment_result.html',
            {
                'success': False,

                'message':
                    'Payment could not be completed.'
            }
        )
@login_required
def payments(request):

    user_payments = Payment.objects.filter(
        user=request.user
    ).order_by('-created_at')

    # Search
    search = request.GET.get('search', '').strip()

    if search:
        user_payments = user_payments.filter(
            Q(transaction_id__icontains=search) |
            Q(description__icontains=search)
        )

    # Payment type filter
    payment_type = request.GET.get('payment_type', '').strip()

    if payment_type:
        user_payments = user_payments.filter(
            payment_type=payment_type
        )

    # Status filter
    status = request.GET.get('status', '').strip()

    if status:
        user_payments = user_payments.filter(
            status=status
        )

    # Date filter
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if date_from:
        user_payments = user_payments.filter(
            created_at__date__gte=date_from
        )

    if date_to:
        user_payments = user_payments.filter(
            created_at__date__lte=date_to
        )

    # Summary values
    total_payments = user_payments.count()

    total_spent = user_payments.filter(
        status='SUCCESS'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    successful_payments = user_payments.filter(
        status='SUCCESS'
    ).count()

    return render(
        request,
        'dashboard/payments.html',
        {
            'payments': user_payments,
            'total_payments': total_payments,
            'total_spent': total_spent,
            'successful_payments': successful_payments,

            # Keep filter values
            'search': search,
            'selected_payment_type': payment_type,
            'selected_status': status,
            'date_from': date_from,
            'date_to': date_to,
        }
    )

   
def bank_accounts(request):

    user_accounts = BankAccount.objects.filter(
        user=request.user
    ).order_by('bank_name')

    total_accounts = user_accounts.count()

    active_accounts = user_accounts.filter(
        is_active=True
    ).count()

    total_balance = user_accounts.filter(
        is_active=True
    ).aggregate(
        total=Sum('balance')
    )['total'] or 0

    return render(
        request,
        'dashboard/bank_accounts.html',
        {
            'bank_accounts': user_accounts,
            'total_accounts': total_accounts,
            'active_accounts': active_accounts,
            'total_balance': total_balance,
        }
    )
def recharge_bills(request):
    return render(
        request,
        'dashboard/recharge_bills.html'
    )
def payment_pin(request):

    pending_payment = request.session.get('pending_payment')

    if not pending_payment:
        return redirect('ai_router')

    amount = pending_payment['amount']
    payment_type = pending_payment['payment_type']
    bank_id = pending_payment['bank_id']

    account = BankAccount.objects.filter(
        id=bank_id,
        user=request.user,
        is_active=True
    ).first()

    if not account:
        request.session.pop('pending_payment', None)
        return redirect('ai_router')

    # -----------------------------------
    # CHECK TEMPORARY PIN LOCK
    # -----------------------------------

    lock_until = request.session.get('pin_locked_until')

    if lock_until:

        lock_time = timezone.datetime.fromisoformat(lock_until)

        if timezone.now() < lock_time:

            remaining = int(
                (lock_time - timezone.now()).total_seconds()
            )

            return render(
                request,
                'dashboard/payment_pin.html',
                {
                    'amount': amount,
                    'payment_type': payment_type,
                    'bank': account.get_bank_name_display(),
                    'error': (
                        f'Too many incorrect attempts. '
                        f'Please try again in {remaining} seconds.'
                    )
                }
            )

        else:
            # Lock expired
            request.session.pop('pin_locked_until', None)
            request.session['pin_attempts'] = 0

    # -----------------------------------
    # HANDLE PIN SUBMISSION
    # -----------------------------------

    if request.method == 'POST':

        entered_pin = request.POST.get(
            'payment_pin',
            ''
        ).strip()

        # Validate PIN format
        if not entered_pin.isdigit() or len(entered_pin) != 4:

            return render(
                request,
                'dashboard/payment_pin.html',
                {
                    'amount': amount,
                    'payment_type': payment_type,
                    'bank': account.get_bank_name_display(),
                    'error': 'Please enter a valid 4-digit PIN.'
                }
            )

        # Check whether user has a PIN
        if not request.user.payment_pin:

            return render(
                request,
                'dashboard/payment_pin.html',
                {
                    'amount': amount,
                    'payment_type': payment_type,
                    'bank': account.get_bank_name_display(),
                    'error': (
                        'Payment PIN is not configured. '
                        'Please set your Payment PIN first.'
                    )
                }
            )

        # -----------------------------------
        # VERIFY PIN
        # -----------------------------------

        if check_password(
            entered_pin,
            request.user.payment_pin
        ):

            # Reset failed attempts
            request.session.pop(
                'pin_attempts',
                None
            )

            request.session.pop(
                'pin_locked_until',
                None
            )

            # Mark PIN as verified
            request.session['payment_pin_verified'] = True

            return redirect('confirm_payment')

        # -----------------------------------
        # WRONG PIN
        # -----------------------------------

        attempts = request.session.get(
            'pin_attempts',
            0
        )

        attempts += 1

        request.session['pin_attempts'] = attempts

        remaining_attempts = 3 - attempts

        if attempts >= 3:

            lock_until = timezone.now() + timedelta(
                minutes=5
            )

            request.session['pin_locked_until'] = (
                lock_until.isoformat()
            )

            request.session['pin_attempts'] = 0

            return render(
                request,
                'dashboard/payment_pin.html',
                {
                    'amount': amount,
                    'payment_type': payment_type,
                    'bank': account.get_bank_name_display(),
                    'error': (
                        'Too many incorrect PIN attempts. '
                        'Payment authorization is locked for 5 minutes.'
                    )
                }
            )

        return render(
            request,
            'dashboard/payment_pin.html',
            {
                'amount': amount,
                'payment_type': payment_type,
                'bank': account.get_bank_name_display(),
                'error': (
                    f'Incorrect Payment PIN. '
                    f'{remaining_attempts} attempt(s) remaining.'
                )
            }
        )

    # -----------------------------------
    # DISPLAY PIN PAGE
    # -----------------------------------

    return render(
        request,
        'dashboard/payment_pin.html',
        {
            'amount': amount,
            'payment_type': payment_type,
            'bank': account.get_bank_name_display()
        }
    )
def set_payment_pin(request):

    if request.method == 'POST':

        pin = request.POST.get('pin', '').strip()
        confirm_pin = request.POST.get('confirm_pin', '').strip()

        # Check PIN length and numbers
        if not pin.isdigit() or len(pin) != 4:
            return render(
                request,
                'dashboard/set_payment_pin.html',
                {
                    'error': 'PIN must contain exactly 4 digits.'
                }
            )

        # Check confirmation
        if pin != confirm_pin:
            return render(
                request,
                'dashboard/set_payment_pin.html',
                {
                    'error': 'PINs do not match.'
                }
            )

        # Save hashed PIN
        request.user.payment_pin = make_password(pin)

        request.user.save(
            update_fields=['payment_pin']
        )

        return render(
            request,
            'dashboard/set_payment_pin.html',
            {
                'success': 'Payment PIN created successfully!'
            }
        )

    return render(
        request,
        'dashboard/set_payment_pin.html'
    )
@login_required
def my_profile(request):
    bank_accounts = BankAccount.objects.filter(
        user=request.user
    ).order_by('bank_name')

    return render(
        request,
        'dashboard/profile.html',
        {
            'bank_accounts': bank_accounts
        }
    )
@login_required
def change_password(request):

    if request.method == 'POST':

        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not request.user.check_password(current_password):
            return render(
                request,
                'dashboard/change_password.html',
                {
                    'error': 'Current password is incorrect.'
                }
            )

        if len(new_password) < 8:
            return render(
                request,
                'dashboard/change_password.html',
                {
                    'error': 'New password must contain at least 8 characters.'
                }
            )

        if new_password != confirm_password:
            return render(
                request,
                'dashboard/change_password.html',
                {
                    'error': 'New passwords do not match.'
                }
            )

        request.user.set_password(new_password)
        request.user.save()

        update_session_auth_hash(
            request,
            request.user
        )

        return render(
            request,
            'dashboard/change_password.html',
            {
                'success': 'Password changed successfully!'
            }
        )

    return render(
        request,
        'dashboard/change_password.html'
    )
@login_required
def upload_profile_photo(request):

    if request.method == 'POST':

        if 'profile_photo' in request.FILES:

            request.user.profile_photo = request.FILES['profile_photo']

            request.user.save(
                update_fields=['profile_photo']
            )

        return redirect('my_profile')

    return redirect('my_profile')
@login_required
def change_password(request):

    if request.method == 'POST':

        current_password = request.POST.get(
            'current_password',
            ''
        )

        new_password = request.POST.get(
            'new_password',
            ''
        )

        confirm_password = request.POST.get(
            'confirm_password',
            ''
        )

        # Check current password
        if not request.user.check_password(current_password):

            return render(
                request,
                'dashboard/change_password.html',
                {
                    'error':
                        'Current password is incorrect.'
                }
            )

        # Check password length
        if len(new_password) < 8:

            return render(
                request,
                'dashboard/change_password.html',
                {
                    'error':
                        'New password must contain at least 8 characters.'
                }
            )

        # Check passwords match
        if new_password != confirm_password:

            return render(
                request,
                'dashboard/change_password.html',
                {
                    'error':
                        'New passwords do not match.'
                }
            )

        # Change password
        request.user.set_password(new_password)

        request.user.save()

        # Keep user logged in
        update_session_auth_hash(
            request,
            request.user
        )

        return render(
            request,
            'dashboard/change_password.html',
            {
                'success':
                    'Password changed successfully!'
            }
        )

    return render(
        request,
        'dashboard/change_password.html'
    )
@login_required
def add_bank_account(request):

    if request.method == 'POST':

        bank_name = request.POST.get('bank_name')
        account_number = request.POST.get('account_number')
        balance = request.POST.get('balance')

        if not bank_name or not account_number or not balance:

            return render(
                request,
                'dashboard/add_bank_account.html',
                {
                    'error': 'Please fill in all fields.'
                }
            )

        try:
            balance = Decimal(balance)
        except:
            return render(
                request,
                'dashboard/add_bank_account.html',
                {
                    'error': 'Please enter a valid balance.'
                }
            )

        BankAccount.objects.create(
            user=request.user,
            bank_name=bank_name,
            account_number=account_number,
            balance=balance,
            is_active=True
        )

        return redirect('my_profile')

    return render(
        request,
        'dashboard/add_bank_account.html'
    )
@login_required
def edit_bank_account(request, account_id):

    account = BankAccount.objects.filter(
        id=account_id,
        user=request.user
    ).first()

    if not account:
        return redirect('my_profile')

    if request.method == 'POST':

        bank_name = request.POST.get('bank_name')
        account_number = request.POST.get('account_number')
        balance = request.POST.get('balance')
        is_active = request.POST.get('is_active')

        if not bank_name or not account_number or not balance:
            return render(
                request,
                'dashboard/edit_bank_account.html',
                {
                    'account': account,
                    'error': 'Please fill in all fields.'
                }
            )

        try:
            balance = Decimal(balance)
        except:
            return render(
                request,
                'dashboard/edit_bank_account.html',
                {
                    'account': account,
                    'error': 'Please enter a valid balance.'
                }
            )

        account.bank_name = bank_name
        account.account_number = account_number
        account.balance = balance
        account.is_active = is_active == 'on'

        account.save()

        return redirect('my_profile')

    return render(
        request,
        'dashboard/edit_bank_account.html',
        {
            'account': account
        }
    )
@login_required
def payment_history(request):

    payments = Payment.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(
        request,
        'dashboard/payment_history.html',
        {
            'payments': payments
        }
    )
@login_required
def payment_detail(request, payment_id):

    payment = Payment.objects.filter(
        id=payment_id,
        user=request.user
    ).first()

    if not payment:
        return redirect('payments')

    return render(
        request,
        'dashboard/payment_detail.html',
        {
            'payment': payment
        }
    )
@login_required
def risk_compliance(request):
    from django.db.models import Sum
    from django.utils import timezone
    from datetime import timedelta

    user = request.user

    # =====================================================
    # USER PAYMENTS
    # =====================================================

    payments = Payment.objects.filter(user=user)

    total_transactions = payments.count()

    successful_transactions = payments.filter(
        status__iexact="SUCCESS"
    ).count()

    failed_transactions = payments.exclude(
        status__iexact="SUCCESS"
    ).count()

    total_amount = payments.aggregate(
        total=Sum("amount")
    )["total"] or 0

    # =====================================================
    # LAST 30 DAYS
    # =====================================================

    thirty_days_ago = timezone.now() - timedelta(days=30)

    recent_payments = payments.filter(
        created_at__gte=thirty_days_ago
    )

    recent_transaction_count = recent_payments.count()

    recent_amount = recent_payments.aggregate(
        total=Sum("amount")
    )["total"] or 0

    # =====================================================
    # COMPLIANCE SCORE
    # =====================================================

    if total_transactions > 0:
        compliance_score = round(
            (successful_transactions / total_transactions) * 100
        )
    else:
        compliance_score = 100

    # =====================================================
    # TRANSACTION SAFETY
    # =====================================================

    transaction_safety = compliance_score

    # =====================================================
    # IDENTITY VERIFICATION
    # =====================================================

    verified_count = 0

    if user.email_verified:
        verified_count += 1

    if user.phone_verified:
        verified_count += 1

    identity_verification = verified_count * 50

    # =====================================================
    # RISK SCORE
    # =====================================================

    risk_score = 100 - compliance_score

    if risk_score <= 30:
        risk_level = "Low Risk"
    elif risk_score <= 60:
        risk_level = "Medium Risk"
    else:
        risk_level = "High Risk"

    # =====================================================
    # ALERTS
    # =====================================================

    alerts = failed_transactions

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {
        "total_transactions": total_transactions,
        "successful_transactions": successful_transactions,
        "failed_transactions": failed_transactions,

        "total_amount": total_amount,

        "recent_transaction_count": recent_transaction_count,
        "recent_amount": recent_amount,

        "compliance_score": compliance_score,
        "transaction_safety": transaction_safety,

        "identity_verification": identity_verification,

        "risk_score": risk_score,
        "risk_level": risk_level,

        "alerts": alerts,
    }

    return render(
        request,
        "dashboard/risk_compliance.html",
        context
    )