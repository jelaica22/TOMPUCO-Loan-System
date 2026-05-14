from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password
from decimal import Decimal
from main.models import (
    Member, Loan, Payment, Notification,
    SystemSetting, AuditLog, LoanApplication
)
from django.db import models
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from datetime import date
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from datetime import datetime, timedelta, date
from datetime import date
import random
import json

from django.contrib.auth import authenticate, login as auth_login


def cashier_login(request):
    if request.user.is_authenticated and hasattr(request.user, 'cashier_profile'):
        return redirect('cashier:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and hasattr(user, 'cashier_profile'):
            auth_login(request, user)
            return redirect('cashier:dashboard')
        else:
            return render(request, 'cashier/login.html', {'error': 'Invalid credentials or not a cashier'})

    return render(request, 'cashier/login.html')


# Cashier required decorator
def cashier_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login/')
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        if not request.user.groups.filter(name='Cashier').exists():
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Access denied. Cashier access required.")
        return view_func(request, *args, **kwargs)

    return wrapper


@login_required
@cashier_required
def dashboard(request):
    today = timezone.now().date()
    today_payments = Payment.objects.filter(payment_date=today, status='completed')
    today_collection = today_payments.aggregate(total=Sum('amount'))['total'] or 0
    pending_count = Payment.objects.filter(status='pending').count()

    # Monthly collection
    this_month = datetime.now().month
    this_year = datetime.now().year
    monthly_payments = Payment.objects.filter(
        payment_date__month=this_month,
        payment_date__year=this_year,
        status='completed'
    )
    monthly_collection = monthly_payments.aggregate(total=Sum('amount'))['total'] or 0

    # Weekly average
    last_7_days = date.today() - timedelta(days=7)
    weekly_payments = Payment.objects.filter(
        payment_date__gte=last_7_days,
        payment_date__lte=today,
        status='completed'
    )
    weekly_total = weekly_payments.aggregate(total=Sum('amount'))['total'] or 0
    weekly_avg = weekly_total / 7 if weekly_total > 0 else 0

    # Chart data - last 7 days trend
    trend_labels = []
    trend_data = []
    for i in range(6, -1, -1):
        dt = date.today() - timedelta(days=i)
        trend_labels.append(dt.strftime('%a'))
        daily_total = Payment.objects.filter(
            payment_date=dt,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        trend_data.append(float(daily_total))

    # Payment method distribution (today)
    cash_total = today_payments.filter(payment_method='cash').aggregate(total=Sum('amount'))['total'] or 0
    pesada_total = today_payments.filter(payment_method='pesada').aggregate(total=Sum('amount'))['total'] or 0
    quedan_total = today_payments.filter(payment_method='quedan').aggregate(total=Sum('amount'))['total'] or 0

    method_labels = ['Cash', 'Pesada', 'Quedan']
    method_data = [float(cash_total), float(pesada_total), float(quedan_total)]

    # Hourly distribution (for today)
    hourly_labels = []
    hourly_data = []
    for hour in range(9, 18):
        if hour < 12:
            hourly_labels.append(f'{hour}AM')
        else:
            hourly_labels.append(f'{hour - 12}PM')
        hourly_total = today_payments.filter(
            created_at__hour=hour
        ).aggregate(total=Sum('amount'))['total'] or 0
        hourly_data.append(float(hourly_total))

    # Weekly performance (last 4 weeks)
    performance_labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
    performance_data = []
    for week in range(4, 0, -1):
        week_start = date.today() - timedelta(days=week * 7)
        week_end = week_start + timedelta(days=6)
        weekly_total = Payment.objects.filter(
            payment_date__gte=week_start,
            payment_date__lte=week_end,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        performance_data.append(float(weekly_total))

    # KPI counts
    total_payments = Payment.objects.filter(status='completed').count()
    cash_count = Payment.objects.filter(payment_method='cash', status='completed').count()
    pesada_count = Payment.objects.filter(payment_method='pesada', status='completed').count()
    quedan_count = Payment.objects.filter(payment_method='quedan', status='completed').count()

    return render(request, 'cashier/dashboard.html', {
        'today_collection': today_collection,
        'today_count': today_payments.count(),
        'today_payments': today_payments[:20],
        'pending_count': pending_count,
        'monthly_collection': monthly_collection,
        'weekly_avg': weekly_avg,
        'trend_labels': trend_labels,
        'trend_data': trend_data,
        'method_labels': method_labels,
        'method_data': method_data,
        'hourly_labels': hourly_labels,
        'hourly_data': hourly_data,
        'performance_labels': performance_labels,
        'performance_data': performance_data,
        'total_payments': total_payments,
        'cash_count': cash_count,
        'pesada_count': pesada_count,
        'quedan_count': quedan_count,
    })


@login_required
@cashier_required
def dashboard_data_api(request):
    """API endpoint for real-time dashboard data"""
    data_type = request.GET.get('type', 'collection')

    if data_type == 'collection':
        labels = []
        values = []
        for i in range(6, -1, -1):
            dt = date.today() - timedelta(days=i)
            labels.append(dt.strftime('%a'))
            daily_total = Payment.objects.filter(
                payment_date=dt,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0
            values.append(float(daily_total))
        return JsonResponse({'labels': labels, 'values': values})

    elif data_type == 'method':
        today = date.today()
        payments = Payment.objects.filter(payment_date=today, status='completed')
        cash_total = payments.filter(payment_method='cash').aggregate(total=Sum('amount'))['total'] or 0
        pesada_total = payments.filter(payment_method='pesada').aggregate(total=Sum('amount'))['total'] or 0
        quedan_total = payments.filter(payment_method='quedan').aggregate(total=Sum('amount'))['total'] or 0
        return JsonResponse({
            'labels': ['Cash', 'Pesada', 'Quedan'],
            'values': [float(cash_total), float(pesada_total), float(quedan_total)]
        })

    elif data_type == 'hourly':
        today = date.today()
        hourly_data = []
        labels = []
        for hour in range(9, 18):
            if hour < 12:
                labels.append(f'{hour}AM')
            else:
                labels.append(f'{hour - 12}PM')
            hourly_total = Payment.objects.filter(
                payment_date=today,
                status='completed',
                created_at__hour=hour
            ).aggregate(total=Sum('amount'))['total'] or 0
            hourly_data.append(float(hourly_total))
        return JsonResponse({'labels': labels, 'values': hourly_data})

    elif data_type == 'performance':
        labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
        values = []
        today = date.today()
        for week in range(4, 0, -1):
            week_start = today - timedelta(days=week * 7)
            week_end = week_start + timedelta(days=6)
            weekly_total = Payment.objects.filter(
                payment_date__gte=week_start,
                payment_date__lte=week_end,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0
            values.append(float(weekly_total))
        return JsonResponse({'labels': labels, 'values': values})

    return JsonResponse({'error': 'Invalid data type'}, status=400)


@login_required
@cashier_required
def post_payment(request):
    """Display post payment page"""
    return render(request, 'cashier/post_payment.html')


@login_required
@cashier_required
def post_payment_submit(request):
    """Submit payment processing"""
    if request.method == 'POST':
        try:
            loan_id = request.POST.get('payment_id')
            amount = Decimal(request.POST.get('amount', 0))
            payment_method = request.POST.get('payment_method')
            reference_number = request.POST.get('reference_number', '')

            loan = get_object_or_404(Loan, id=loan_id)

            if amount <= 0:
                return JsonResponse({'success': False, 'error': 'Amount must be greater than 0'})

            if amount > loan.remaining_balance:
                return JsonResponse(
                    {'success': False, 'error': f'Amount exceeds remaining balance of ₱{loan.remaining_balance:,.2f}'})

            payment_number = f'PAY-{timezone.now().year}-{timezone.now().strftime("%m%d%H%M%S")}{random.randint(10, 99)}'

            payment = Payment.objects.create(
                payment_number=payment_number,
                loan=loan,
                member=loan.borrower,
                amount=amount,
                payment_method=payment_method,
                reference_number=reference_number,
                status='completed',
                payment_date=timezone.now().date()
            )

            loan.remaining_balance -= amount
            if loan.remaining_balance <= 0:
                loan.status = 'completed'
                loan.remaining_balance = 0
            loan.save()

            return JsonResponse({'success': True,
                                 'message': f'Payment of ₱{amount:,.2f} posted successfully! Receipt: {payment_number}'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
@cashier_required
def search_payment_instruction(request):
    q = request.GET.get('q', '')

    loan = None
    if q:
        if q.startswith('LN-'):
            loan = Loan.objects.filter(loan_number=q).first()
        else:
            member = Member.objects.filter(membership_number=q).first()
            if member:
                loan = Loan.objects.filter(borrower=member, status='active').first()

    if loan:
        monthly_payment = loan.monthly_payment if hasattr(loan,
                                                          'monthly_payment') and loan.monthly_payment else loan.principal_amount / 12
        return JsonResponse({
            'success': True,
            'payment_id': loan.id,
            'member_name': f"{loan.borrower.first_name} {loan.borrower.last_name}",
            'loan_number': loan.loan_number,
            'amount_due': str(monthly_payment),
            'remaining_balance': str(loan.remaining_balance),
            'issued_by': 'Staff',
            'instruction_date': timezone.now().strftime('%Y-%m-%d'),
        })
    return JsonResponse({'success': False, 'error': 'No payment instruction found'})


@login_required
@cashier_required
def today_collection(request):
    today = timezone.now().date()
    payments = Payment.objects.filter(payment_date=today, status='completed')
    total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0

    cash_total = payments.filter(payment_method='cash').aggregate(total=Sum('amount'))['total'] or 0
    pesada_total = payments.filter(payment_method='pesada').aggregate(total=Sum('amount'))['total'] or 0
    quedan_total = payments.filter(payment_method='quedan').aggregate(total=Sum('amount'))['total'] or 0

    cash_count = payments.filter(payment_method='cash').count()
    pesada_count = payments.filter(payment_method='pesada').count()
    quedan_count = payments.filter(payment_method='quedan').count()

    # Get manager name from system settings
    try:
        manager_name = SystemSetting.objects.get(setting_key='branch_manager_name').setting_value
    except SystemSetting.DoesNotExist:
        manager_name = 'Mr. ERWIN D. CLAVERIA'

    return render(request, 'cashier/today_collection.html', {
        'payments': payments,
        'total_amount': total_amount,
        'count': payments.count(),
        'cash_total': cash_total,
        'pesada_total': pesada_total,
        'quedan_total': quedan_total,
        'cash_count': cash_count,
        'pesada_count': pesada_count,
        'quedan_count': quedan_count,
        'date': today,
        'manager_name': manager_name,
    })


@login_required
@cashier_required
def end_of_day(request):
    today = timezone.now().date()
    payments = Payment.objects.filter(payment_date=today, status='completed')
    total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0

    cash_total = payments.filter(payment_method='cash').aggregate(total=Sum('amount'))['total'] or 0
    pesada_total = payments.filter(payment_method='pesada').aggregate(total=Sum('amount'))['total'] or 0
    quedan_total = payments.filter(payment_method='quedan').aggregate(total=Sum('amount'))['total'] or 0

    cash_count = payments.filter(payment_method='cash').count()
    pesada_count = payments.filter(payment_method='pesada').count()
    quedan_count = payments.filter(payment_method='quedan').count()

    return render(request, 'cashier/end_of_day.html', {
        'payments': payments,
        'total_amount': total_amount,
        'count': payments.count(),
        'cash_total': cash_total,
        'pesada_total': pesada_total,
        'quedan_total': quedan_total,
        'cash_count': cash_count,
        'pesada_count': pesada_count,
        'quedan_count': quedan_count,
        'date': today,
    })


# ==================== PROFILE VIEWS ====================

@login_required
def profile(request):
    """Cashier profile page"""
    # Import date at the beginning of the function to ensure it's available
    from datetime import date
    from main.models import Payment
    from django.db.models import Sum

    try:
        staff_profile = request.user.staff_profile
    except:
        # If no staff profile exists, create one
        from staff.models import StaffProfile
        staff_profile = StaffProfile.objects.create(
            user=request.user,
            staff_id=f"CSH-{request.user.id}",
            position='cashier',
            department='Collection',
            hire_date=date.today()  # Now date is imported
        )

    # Calculate stats
    payments_processed = Payment.objects.filter(posted_by=request.user).count()
    total_collected = Payment.objects.filter(posted_by=request.user, status='completed').aggregate(
        total=Sum('amount'))['total'] or 0

    # Calculate days active
    first_payment = Payment.objects.filter(posted_by=request.user).order_by('payment_date').first()
    days_active = 0
    if first_payment:
        days_active = (date.today() - first_payment.payment_date).days

    # Get recent activities - handle if model doesn't exist
    recent_activities = []
    try:
        from .models import StaffActivityLog
        recent_activities = StaffActivityLog.objects.filter(staff=staff_profile).order_by('-created_at')[:10]
    except:
        pass  # StaffActivityLog model doesn't exist yet

    contact_number = ''
    if hasattr(staff_profile, 'contact_number'):
        contact_number = staff_profile.contact_number

    context = {
        'user': request.user,
        'staff_profile': staff_profile,
        'cashier_profile': staff_profile,  # Alias for template
        'payments_processed': payments_processed,
        'total_collected': total_collected / 1000 if total_collected else 0,
        'days_active': days_active,
        'recent_activities': recent_activities,
        'contact_number': contact_number,
    }
    return render(request, 'cashier/profile.html', context)


@login_required
@cashier_required
def remove_avatar(request):
    """Remove profile picture for cashier"""
    if request.method == 'POST':
        try:
            # Check if user has cashier_profile or staff_profile
            if hasattr(request.user, 'cashier_profile'):
                profile = request.user.cashier_profile
            elif hasattr(request.user, 'staff_profile'):
                profile = request.user.staff_profile
            else:
                return JsonResponse({'success': False, 'message': 'Profile not found'}, status=400)

            # Delete profile picture if exists
            if profile.profile_picture:
                profile.profile_picture.delete(save=False)
                profile.profile_picture = None
                profile.save()
                return JsonResponse({'success': True, 'message': 'Profile picture removed successfully'})
            else:
                return JsonResponse({'success': False, 'message': 'No profile picture to remove'}, status=400)

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)


@login_required
def upload_avatar(request):
    """Upload profile picture for cashier"""
    if request.method == 'POST' and request.FILES.get('avatar'):
        try:
            # Try multiple profile model possibilities
            profile = None

            # Check for staff_profile (from your profile view)
            if hasattr(request.user, 'staff_profile'):
                profile = request.user.staff_profile
            # Check for cashier_profile
            elif hasattr(request.user, 'cashier_profile'):
                profile = request.user.cashier_profile
            # Check for member_profile
            elif hasattr(request.user, 'member_profile'):
                profile = request.user.member_profile

            if profile is None:
                # Create a staff profile if it doesn't exist
                from staff.models import StaffProfile
                from datetime import date

                profile = StaffProfile.objects.create(
                    user=request.user,
                    staff_id=f"CSH-{request.user.id}",
                    position='cashier',
                    department='Collection',
                    hire_date=date.today()
                )

            # Delete old profile picture if exists
            if hasattr(profile, 'profile_picture') and profile.profile_picture:
                try:
                    profile.profile_picture.delete(save=False)
                except:
                    pass

            # Save new profile picture
            if hasattr(profile, 'profile_picture'):
                profile.profile_picture = request.FILES['avatar']
                profile.save()

                # Return JSON response for AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Profile picture updated successfully!',
                        'avatar_url': profile.profile_picture.url
                    })

                messages.success(request, 'Profile picture updated successfully!')
            else:
                # If profile doesn't have profile_picture field
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Profile model does not support profile pictures'
                    }, status=400)
                messages.error(request, 'Profile model does not support profile pictures')

        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': str(e)}, status=500)
            messages.error(request, f'Error uploading image: {str(e)}')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'No image selected'}, status=400)
        messages.error(request, 'No image selected')

    return redirect('cashier:profile')


@login_required
@cashier_required
def update_profile(request):
    """Update profile information"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.username = request.POST.get('username', user.username)
        user.save()

        # Update contact number in member profile
        try:
            member = user.member_profile
            member.contact_number = request.POST.get('contact_number', '')
            member.save()
        except:
            Member.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                contact_number=request.POST.get('contact_number', ''),
                residence_address='',
                is_active=True
            )

        messages.success(request, 'Profile updated successfully!')
    return redirect('cashier:profile')


@login_required
@cashier_required
def change_password(request):
    """Change password"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not check_password(current_password, request.user.password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully!')

    return redirect('cashier:profile')


@login_required
@cashier_required
def logout_all_devices(request):
    """Logout from all devices"""
    if request.method == 'POST':
        request.user.session_key = None
        request.user.save()
        messages.success(request, 'Logged out from all devices. Please login again.')
        return redirect('main:login')
    return redirect('cashier:profile')


# ==================== NOTIFICATION VIEWS ====================

@login_required
@cashier_required
def notifications_list(request):
    """List all notifications for cashier"""
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    notification_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')

    if notification_type and notification_type != 'all':
        notifications = notifications.filter(notification_type=notification_type)

    if status == 'unread':
        notifications = notifications.filter(is_read=False)
    elif status == 'read':
        notifications = notifications.filter(is_read=True)

    if search:
        notifications = notifications.filter(
            Q(title__icontains=search) |
            Q(message__icontains=search)
        )

    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_notifications = Notification.objects.filter(recipient=request.user).count()
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    read_count = total_notifications - unread_count
    payment_notifications = Notification.objects.filter(recipient=request.user, notification_type='payment').count()

    return render(request, 'cashier/notifications.html', {
        'notifications': page_obj,
        'total_notifications': total_notifications,
        'unread_count': unread_count,
        'read_count': read_count,
        'payment_notifications': payment_notifications,
    })


@login_required
@cashier_required
def notifications_api(request):
    """API endpoint for notifications"""
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:30]
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    total_count = Notification.objects.filter(recipient=request.user).count()

    data = {
        'success': True,
        'total': total_count,
        'unread_count': unread_count,
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'link': n.link,
            'type': n.notification_type,
            'created_at': n.created_at.strftime('%Y-%m-%d %I:%M %p'),
            'is_read': n.is_read
        } for n in notifications]
    }
    return JsonResponse(data)


@login_required
@cashier_required
def mark_notification_read(request, notif_id):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})


@login_required
@cashier_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})

def cashier_profile_context(request):
    if request.user.is_authenticated and hasattr(request.user, 'cashier_profile'):
        return {'cashier_profile': request.user.cashier_profile}
    return {}


@login_required
@cashier_required
def activity_api(request):
    """API endpoint for recent cashier activities"""
    try:
        activities = []

        # Get recent payments as activities
        recent_payments = Payment.objects.filter(
            status='completed'
        ).order_by('-payment_date')[:15]

        for payment in recent_payments:
            activities.append({
                'id': payment.id,
                'title': '💰 Payment Processed',
                'message': f"Payment of ₱{payment.amount:,.2f} from {payment.member.first_name} {payment.member.last_name}",
                'type': 'payment',
                'link': f"/cashier/payments/{payment.id}/",
                'created_at': payment.payment_date.isoformat()
            })

        # Get recent loan applications
        recent_apps = LoanApplication.objects.filter(
            status__in=['pending_staff_review', 'with_committee']
        ).order_by('-created_at')[:5]

        for app in recent_apps:
            activities.append({
                'id': app.id,
                'title': '📋 New Application',
                'message': f"Loan application from {app.member.first_name} {app.member.last_name}",
                'type': 'application',
                'link': "#",
                'created_at': app.created_at.isoformat()
            })

        # Sort by date (newest first)
        activities.sort(key=lambda x: x['created_at'], reverse=True)
        activities = activities[:8]

        # If no activities, add a welcome message
        if not activities:
            activities = [{
                'id': 1,
                'title': '👋 Welcome to Cashier Portal',
                'message': 'Start processing payments using the "Post Payment" button',
                'type': 'system',
                'link': '#',
                'created_at': timezone.now().isoformat()
            }]

        return JsonResponse({'activities': activities})
    except Exception as e:
        return JsonResponse({'activities': [], 'error': str(e)})


@login_required
@cashier_required
def dashboard_stats_api(request):
    """API endpoint for dashboard statistics"""
    try:
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_start = today.replace(day=1)

        # Today's collection
        today_payments = Payment.objects.filter(payment_date=today, status='completed')
        today_collection = float(today_payments.aggregate(total=Sum('amount'))['total'] or 0)
        today_count = today_payments.count()

        # Monthly collection
        monthly_payments = Payment.objects.filter(payment_date__gte=month_start, status='completed')
        monthly_collection = float(monthly_payments.aggregate(total=Sum('amount'))['total'] or 0)

        # Weekly average
        weekly_payments = Payment.objects.filter(payment_date__gte=week_ago, status='completed')
        weekly_total = float(weekly_payments.aggregate(total=Sum('amount'))['total'] or 0)
        weekly_avg = weekly_total / 7 if weekly_total > 0 else 0

        # Payment method counts
        cash_count = Payment.objects.filter(payment_method='cash', payment_date=today, status='completed').count()
        pesada_count = Payment.objects.filter(payment_method='pesada', payment_date=today, status='completed').count()
        quedan_count = Payment.objects.filter(payment_method='quedan', payment_date=today, status='completed').count()

        # Total payments
        total_payments = Payment.objects.filter(status='completed').count()

        # Pending count
        pending_count = Payment.objects.filter(status='pending').count()

        return JsonResponse({
            'today_collection': today_collection,
            'today_count': today_count,
            'monthly_collection': monthly_collection,
            'weekly_avg': weekly_avg,
            'pending_count': pending_count,
            'total_payments': total_payments,
            'cash_count': cash_count,
            'pesada_count': pesada_count,
            'quedan_count': quedan_count,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)