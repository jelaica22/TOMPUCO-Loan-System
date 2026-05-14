from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime
from django.db.models import Q
from django.contrib.auth.models import User

from main.models import LoanApplication, CommitteeVote, Notification, Loan
from .models import CommitteeProfile

# Import real-time notification utility
from main.notification_utils import send_realtime_notification, send_realtime_notification_to_group


@login_required
def dashboard(request):
    """Committee Dashboard"""
    try:
        committee_profile = CommitteeProfile.objects.get(user=request.user)
    except CommitteeProfile.DoesNotExist:
        committee_profile = None

    # Get user's votes
    user_votes = CommitteeVote.objects.filter(committee_member=request.user)
    voted_application_ids = user_votes.values_list('application_id', flat=True)

    # Pending applications (with_committee status that user hasn't voted on)
    pending_apps = LoanApplication.objects.filter(status='with_committee').exclude(
        id__in=voted_application_ids
    ).order_by('-applied_date')

    # Stats
    total_pending = pending_apps.count()
    line_approved_count = LoanApplication.objects.filter(status='line_approved').count()
    approved_by_committee = user_votes.filter(vote='approved').count()
    rejected_count = user_votes.filter(vote='rejected').count()
    total_voted = approved_by_committee + rejected_count

    # Monthly stats
    from django.utils import timezone
    current_month = timezone.now().month
    current_year = timezone.now().year
    applications_this_month = user_votes.filter(
        voted_at__month=current_month,
        voted_at__year=current_year
    ).count()

    # Approval rate
    approval_rate = int((approved_by_committee / total_voted * 100)) if total_voted > 0 else 0

    # Average decision time
    from django.db.models import Avg, F, ExpressionWrapper, fields
    avg_decision = user_votes.filter(voted_at__isnull=False).annotate(
        decision_time=ExpressionWrapper(
            F('voted_at') - F('application__applied_date'),
            output_field=fields.DurationField()
        )
    ).aggregate(avg_time=Avg('decision_time'))
    avg_decision_days = round(avg_decision['avg_time'].days) if avg_decision['avg_time'] else 0

    # Trend data (last 7 days)
    from datetime import timedelta
    trend_labels = []
    trend_data = []
    for i in range(6, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        trend_labels.append(date.strftime('%a'))
        count = user_votes.filter(voted_at__date=date).count()
        trend_data.append(count)

    # Decision distribution
    decision_labels = ['Approved', 'Rejected']
    decision_data = [approved_by_committee, rejected_count]

    # Recent votes
    recent_votes = user_votes.select_related('application', 'committee_member').order_by('-voted_at')[:5]
    for vote in recent_votes:
        vote.application_id_display = vote.application.application_id
        vote.voted_date_formatted = vote.voted_at.strftime('%Y-%m-%d %H:%M')

    # Committee members count
    total_committee_members = CommitteeProfile.objects.filter(is_active=True).count()
    active_committee_members = total_committee_members
    required_votes_majority = (total_committee_members // 2) + 1

    # Pending applications for table
    pending_for_table = []
    for app in pending_apps[:5]:
        app.loan_type = app.loan_product.name if app.loan_product else 'N/A'
        app.requested_amount_display = f"{app.amount:,.2f}"
        app.votes_approved = CommitteeVote.objects.filter(application=app, vote='approved').count()
        app.has_voted = app.id in voted_application_ids
        pending_for_table.append(app)

    context = {
        'committee_profile': committee_profile,
        'total_pending': total_pending,
        'line_approved_count': line_approved_count,
        'approved_by_committee': approved_by_committee,
        'rejected_count': rejected_count,
        'total_voted': total_voted,
        'applications_this_month': applications_this_month,
        'approval_rate': approval_rate,
        'avg_decision_days': avg_decision_days,
        'trend_labels': trend_labels,
        'trend_data': trend_data,
        'decision_labels': decision_labels,
        'decision_data': decision_data,
        'recent_votes': recent_votes,
        'pending_applications': pending_for_table,
        'total_committee_members': total_committee_members,
        'active_committee_members': active_committee_members,
        'required_votes_majority': required_votes_majority,
    }
    return render(request, 'committee/dashboard.html', context)


@login_required
def applications_list(request):
    """List of pending applications for committee"""
    # Get pending applications (with_committee status)
    applications = LoanApplication.objects.filter(
        status='with_committee'
    ).order_by('-applied_date')

    # Get user's votes
    user_votes = CommitteeVote.objects.filter(
        committee_member=request.user
    ).values_list('application_id', flat=True)

    # Add has_voted flag to each application
    for app in applications:
        app.has_voted = app.id in user_votes
        app.loan_type = app.loan_product.name if app.loan_product else 'N/A'
        app.requested_amount_display = f"₱{app.amount:,.2f}"

    context = {
        'applications': applications,
        'total_pending': applications.count(),
        'voted_count': user_votes.count(),
        'remaining_count': applications.count() - user_votes.count(),
    }
    return render(request, 'committee/applications_list.html', context)


@login_required
def review_application(request, app_id):
    """Committee member reviews application and inputs approved line"""
    application = get_object_or_404(LoanApplication, id=app_id)

    # Get committee profile to check if user is head
    try:
        committee_profile = CommitteeProfile.objects.get(user=request.user)
        is_head = committee_profile.is_head
    except CommitteeProfile.DoesNotExist:
        is_head = False

    # ============================================================
    # HANDLE POST REQUEST - Committee Decision
    # ============================================================
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            approved_line = request.POST.get('approved_line')
            date_approved = request.POST.get('date_approved')
            reduction_reason = request.POST.get('reduction_reason', '')

            # Validate approved line
            try:
                approved_line = Decimal(approved_line)
                requested_amount = application.amount

                if approved_line > requested_amount:
                    messages.error(request,
                                   f'Approved Line (₱{approved_line:,.2f}) cannot exceed Requested Amount (₱{requested_amount:,.2f})')
                    return redirect('committee:review_application', app_id=app_id)

                if approved_line <= 0:
                    messages.error(request, 'Approved Line must be greater than zero')
                    return redirect('committee:review_application', app_id=app_id)

            except (TypeError, ValueError):
                messages.error(request, 'Please enter a valid Approved Line amount')
                return redirect('committee:review_application', app_id=app_id)

            # Save the committee decision
            application.approved_line = approved_line
            application.committee_approved_date = date_approved
            application.committee_reduction_reason = reduction_reason if approved_line < requested_amount else ''
            application.status = 'line_approved'
            application.save()

            # Send REAL-TIME notifications to all STAFF
            staff_users = User.objects.filter(groups__name='Staff') | User.objects.filter(is_staff=True)
            staff_users = staff_users.exclude(username=request.user.username)

            for staff in staff_users:
                send_realtime_notification(
                    staff,
                    '✅ Application Approved by Committee',
                    f'Application {application.application_id} has been approved with line amount ₱{approved_line:,.2f}. Please add charges.',
                    f'/staff/applications/{application.id}/add-charges/',
                    'committee'
                )

            # Send REAL-TIME notification to MEMBER
            send_realtime_notification(
                application.member.user,
                '🎉 Your Loan Application Was Approved!',
                f'Good news! Your application {application.application_id} has been approved by the committee for ₱{approved_line:,.2f}.',
                f'/my-applications/{application.id}/',
                'committee'
            )

            # Send REAL-TIME notification to MANAGERS
            manager_users = User.objects.filter(groups__name='Manager') | User.objects.filter(is_superuser=True)
            for manager in manager_users:
                send_realtime_notification(
                    manager,
                    '📋 Application Ready for Manager Review',
                    f'Application {application.application_id} has been approved by committee. Ready for your final approval.',
                    f'/manager/approvals/{application.id}/',
                    'committee'
                )

            messages.success(request, f'✅ Application approved! Approved Line: ₱{approved_line:,.2f}')
            return redirect('committee:applications_list')

        elif action == 'revision':
            application.status = 'needs_revision'
            application.save()

            # Send REAL-TIME notification to MEMBER
            send_realtime_notification(
                application.member.user,
                '📝 Application Needs Revision',
                f'Your application {application.application_id} needs revision based on committee feedback. Please update and resubmit.',
                f'/my-applications/{application.id}/edit/',
                'committee'
            )

            messages.info(request, 'Revision requested. Member will update the application.')
            return redirect('committee:applications_list')

        elif action == 'reject':
            application.status = 'rejected'
            application.save()

            # Send REAL-TIME notification to MEMBER
            send_realtime_notification(
                application.member.user,
                '❌ Your Loan Application Was Rejected',
                f'We regret to inform you that your application {application.application_id} has been rejected by the committee.',
                f'/my-applications/{application.id}/',
                'committee'
            )

            messages.warning(request, 'Application rejected.')
            return redirect('committee:applications_list')

    # ============================================================
    # GET REQUEST - Display the form
    # ============================================================

    # Get total committee members
    total_committee = CommitteeProfile.objects.filter(is_active=True).count()

    # Get committee votes
    committee_votes = CommitteeVote.objects.filter(application=application)
    votes_approved = committee_votes.filter(vote='approved').count()
    votes_rejected = committee_votes.filter(vote='rejected').count()

    # Check if user has voted
    has_voted = committee_votes.filter(committee_member=request.user).exists()

    # ============================================================
    # APPLICANT STATUS - AUTO DETECTED
    # ============================================================
    member = application.member
    member_loans = Loan.objects.filter(member=member)

    is_new_applicant = member_loans.count() == 0
    is_existing_borrower = member_loans.count() > 0
    has_outstanding_balance = member_loans.filter(
        Q(status='active') | Q(status='overdue'),
        remaining_balance__gt=0
    ).exists()
    has_paid_loans = member_loans.filter(status='paid').exists()
    is_restructured = application.is_restructuring if hasattr(application, 'is_restructuring') else False

    # Calculate suggested amounts
    try:
        requested = float(application.amount) if application.amount else 0
    except (TypeError, ValueError):
        requested = 0

    today = timezone.now().date()
    co_maker = application.co_maker if hasattr(application, 'co_maker') else None

    context = {
        'application': application,
        'member': member,
        'loan_product': application.loan_product,
        'co_maker': co_maker,
        'has_voted': has_voted,
        'committee_votes': committee_votes,
        'votes_approved': votes_approved,
        'votes_rejected': votes_rejected,
        'total_committee': total_committee,
        'is_head': is_head,
        'today': today,
        'is_new_applicant': is_new_applicant,
        'is_existing_borrower': is_existing_borrower,
        'has_outstanding_balance': has_outstanding_balance,
        'has_paid_loans': has_paid_loans,
        'is_restructured': is_restructured,
        'requested_amount': requested,
    }
    return render(request, 'committee/review_application.html', context)


@login_required
def application_detail(request, app_id):
    """View application details"""
    application = get_object_or_404(LoanApplication, id=app_id)
    committee_votes = CommitteeVote.objects.filter(application=application)

    context = {
        'application': application,
        'committee_votes': committee_votes,
    }
    return render(request, 'committee/application_detail.html', context)


@login_required
def decision_history(request):
    """View user's decision/voting history"""
    votes = CommitteeVote.objects.filter(
        committee_member=request.user
    ).order_by('-voted_at').select_related('application', 'application__member', 'application__loan_product')

    applications = []
    for vote in votes:
        app = vote.application
        app.my_vote = vote.vote
        app.my_vote_display = 'Approved' if vote.vote == 'approved' else 'Rejected'
        app.voted_at = vote.voted_at
        app.loan_type = app.loan_product.name if app.loan_product else 'N/A'
        app.requested_amount = app.amount
        app.approved_line = app.approved_line if hasattr(app, 'approved_line') else None
        applications.append(app)

    total_count = len(applications)
    approved_count = votes.filter(vote='approved').count()
    rejected_count = votes.filter(vote='rejected').count()

    voted_application_ids = votes.values_list('application_id', flat=True)
    pending_applications_count = LoanApplication.objects.filter(
        status='with_committee'
    ).exclude(id__in=voted_application_ids).count()

    context = {
        'applications': applications,
        'total_count': total_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'pending_applications_count': pending_applications_count,
    }
    return render(request, 'committee/decision_history.html', context)


@login_required
def reports(request):
    """Committee Reports Page"""
    context = {}
    return render(request, 'committee/reports.html', context)


@login_required
def report_api(request, report_type):
    """API endpoint for generating reports"""
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')

    votes = CommitteeVote.objects.filter(committee_member=request.user)

    if date_from:
        votes = votes.filter(voted_at__date__gte=date_from)
    if date_to:
        votes = votes.filter(voted_at__date__lte=date_to)

    if report_type == 'summary':
        total = votes.count()
        approved = votes.filter(vote='approved').count()
        rejected = votes.filter(vote='rejected').count()
        approval_rate = int((approved / total * 100)) if total > 0 else 0

        data = {
            'success': True,
            'total_applications': total,
            'approved_count': approved,
            'rejected_count': rejected,
            'approval_rate': approval_rate
        }

    elif report_type == 'voting':
        vote_list = []
        for vote in votes:
            vote_list.append({
                'application_id': vote.application.application_id,
                'member_name': f"{vote.application.member.last_name}, {vote.application.member.first_name}",
                'requested_amount': float(vote.application.amount),
                'my_vote': vote.vote,
                'status': vote.application.status,
                'voted_date': vote.voted_at.strftime('%Y-%m-%d')
            })
        data = {'success': True, 'votes': vote_list}

    elif report_type == 'performance':
        total = votes.count()
        approved = votes.filter(vote='approved').count()
        approval_rate = int((approved / total * 100)) if total > 0 else 0

        monthly_data = {}
        for vote in votes:
            month_key = vote.voted_at.strftime('%Y-%m')
            monthly_data[month_key] = monthly_data.get(month_key, 0) + 1

        data = {
            'success': True,
            'total_votes': total,
            'approval_rate': approval_rate,
            'monthly_avg': int(total / 12) if total > 0 else 0,
            'monthly_labels': list(monthly_data.keys()),
            'monthly_data': list(monthly_data.values()),
            'role': 'Committee Member'
        }

    elif report_type == 'applications':
        app_list = []
        for vote in votes:
            app_list.append({
                'application_id': vote.application.application_id,
                'member_name': f"{vote.application.member.last_name}, {vote.application.member.first_name}",
                'loan_product': vote.application.loan_product.name if vote.application.loan_product else 'N/A',
                'requested_amount': float(vote.application.amount),
                'approved_line': float(vote.application.approved_line) if vote.application.approved_line else 0,
                'decision': vote.vote,
                'review_date': vote.voted_at.strftime('%Y-%m-%d')
            })
        data = {'success': True, 'applications': app_list}

    else:
        data = {'success': False, 'error': 'Invalid report type'}

    return JsonResponse(data)


@login_required
def notification_detail(request, notif_id):
    """View a single notification detail"""
    from main.models import Notification

    notification = get_object_or_404(Notification, id=notif_id, recipient=request.user)

    if not notification.is_read:
        notification.is_read = True
        notification.save()

    if notification.link:
        return redirect(notification.link)

    context = {
        'notification': notification,
    }
    return render(request, 'committee/notification_detail.html', context)


@login_required
def notifications_list(request):
    """View notifications"""
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'notifications': page_obj,
        'total_notifications': notifications.count(),
        'unread_count': notifications.filter(is_read=False).count(),
        'read_count': notifications.filter(is_read=True).count(),
        'system_notifications': notifications.filter(notification_type='system').count(),
    }
    return render(request, 'committee/notifications.html', context)


@login_required
def notification_count_api(request):
    """API endpoint for notification count"""
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'unread_count': unread_count})


@login_required
def notification_list_api(request):
    """API endpoint to get recent notifications for dropdown"""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:10]

    from django.utils.timesince import timesince

    notification_data = []
    for notif in notifications:
        notification_data.append({
            'id': notif.id,
            'title': notif.title,
            'message': notif.message,
            'link': notif.link or '#',
            'is_read': notif.is_read,
            'time_ago': timesince(notif.created_at) + ' ago'
        })

    return JsonResponse({
        'success': True,
        'notifications': notification_data,
        'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count()
    })


@login_required
def mark_notification_read(request, notif_id):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})


@login_required
def profile(request):
    """Committee member profile page"""
    try:
        committee_profile = CommitteeProfile.objects.get(user=request.user)
    except CommitteeProfile.DoesNotExist:
        committee_profile = CommitteeProfile.objects.create(user=request.user)

    votes = CommitteeVote.objects.filter(committee_member=request.user)
    total_votes = votes.count()
    approved_votes = votes.filter(vote='approved').count()
    rejected_votes = votes.filter(vote='rejected').count()
    approval_rate = int((approved_votes / total_votes * 100)) if total_votes > 0 else 0

    current_month = timezone.now().month
    monthly_votes = votes.filter(voted_at__month=current_month).count()
    recent_votes = votes.order_by('-voted_at')[:10]

    context = {
        'committee_profile': committee_profile,
        'total_votes': total_votes,
        'approved_votes': approved_votes,
        'rejected_votes': rejected_votes,
        'approval_rate': approval_rate,
        'monthly_votes': monthly_votes,
        'recent_votes': recent_votes,
        'contact_number': committee_profile.contact_number,
    }
    return render(request, 'committee/profile.html', context)


@login_required
def upload_avatar(request):
    """Upload profile avatar"""
    if request.method == 'POST' and request.FILES.get('avatar'):
        try:
            committee_profile, created = CommitteeProfile.objects.get_or_create(user=request.user)
            committee_profile.avatar = request.FILES['avatar']
            committee_profile.save()
            messages.success(request, 'Profile picture updated successfully!')
        except Exception as e:
            messages.error(request, f'Error uploading image: {str(e)}')
    return redirect('committee:profile')


@login_required
def update_profile(request):
    """Update profile information"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.username = request.POST.get('username', '')
        user.save()

        committee_profile, created = CommitteeProfile.objects.get_or_create(user=user)
        committee_profile.contact_number = request.POST.get('contact_number', '')
        committee_profile.save()

        messages.success(request, 'Profile updated successfully!')
    return redirect('committee:profile')


@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        from django.contrib.auth import authenticate
        from django.contrib.auth.hashers import make_password

        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = authenticate(username=request.user.username, password=current_password)
        if not user:
            messages.error(request, 'Current password is incorrect.')
            return redirect('committee:profile')

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('committee:profile')

        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('committee:profile')

        request.user.password = make_password(new_password)
        request.user.save()

        messages.success(request, 'Password changed successfully! Please log in again.')
        return redirect('main:login')

    return redirect('committee:profile')


@login_required
def logout_all_devices(request):
    """Logout from all devices by changing password hash"""
    from django.contrib.auth.hashers import make_password
    import secrets

    new_password = secrets.token_urlsafe(32)
    request.user.password = make_password(new_password)
    request.user.save()

    messages.info(request, 'You have been logged out from all devices.')
    return redirect('main:login')


@login_required
def committee_logout(request):
    """Committee logout"""
    from django.contrib.auth import logout as auth_logout
    auth_logout(request)
    return redirect('main:landing')


@login_required
def cast_vote(request, app_id):
    """Committee member casts vote on an application"""
    if request.method == 'POST':
        application = get_object_or_404(LoanApplication, id=app_id)

        existing_vote = CommitteeVote.objects.filter(
            application=application,
            committee_member=request.user
        ).first()

        if existing_vote:
            messages.error(request, 'You have already voted on this application.')
            return redirect('committee:review_application', app_id=app_id)

        vote_value = request.POST.get('vote')
        reason = request.POST.get('reason', '')

        if vote_value not in ['approved', 'rejected']:
            messages.error(request, 'Invalid vote value.')
            return redirect('committee:review_application', app_id=app_id)

        CommitteeVote.objects.create(
            application=application,
            committee_member=request.user,
            vote=vote_value,
            reason=reason
        )

        messages.success(request, f'Your vote has been recorded: {vote_value.upper()}')

        # Send notification to other committee members
        other_committee_members = CommitteeProfile.objects.filter(is_active=True).exclude(
            user=request.user
        ).select_related('user')

        for cm in other_committee_members:
            send_realtime_notification(
                cm.user,
                f'🗳️ New Vote Cast on {application.application_id}',
                f'{request.user.get_full_name()} voted {vote_value.upper()} on application {application.application_id}.',
                f'/committee/applications/{application.id}/review/',
                'committee'
            )

        # Check if all committee members have voted
        total_committee = CommitteeProfile.objects.filter(is_active=True).count()
        votes_cast = CommitteeVote.objects.filter(application=application).count()

        if votes_cast >= total_committee:
            votes_approved = CommitteeVote.objects.filter(application=application, vote='approved').count()
            votes_rejected = CommitteeVote.objects.filter(application=application, vote='rejected').count()

            head_vote = CommitteeVote.objects.filter(
                application=application,
                committee_member__committee_profile__is_head=True
            ).first()

            if head_vote and head_vote.vote == 'rejected':
                application.status = 'rejected'

                # Notify member
                send_realtime_notification(
                    application.member.user,
                    '❌ Application Rejected by Head Committee',
                    f'Your application {application.application_id} has been rejected by the Head Committee.',
                    f'/my-applications/{application.id}/',
                    'committee'
                )

            elif votes_approved > total_committee / 2:
                application.status = 'line_approved'

                # Notify staff
                staff_users = User.objects.filter(groups__name='Staff') | User.objects.filter(is_staff=True)
                for staff in staff_users:
                    send_realtime_notification(
                        staff,
                        '✅ Application Ready for Line Approval',
                        f'Application {application.application_id} has been approved by committee. Please input approved line.',
                        f'/staff/applications/{application.id}/approve-line/',
                        'committee'
                    )

                # Notify member
                send_realtime_notification(
                    application.member.user,
                    '🎉 Your Application Has Been Approved!',
                    f'Congratulations! Your application {application.application_id} has been approved by the committee.',
                    f'/my-applications/{application.id}/',
                    'committee'
                )
            else:
                application.status = 'rejected'

                # Notify member
                send_realtime_notification(
                    application.member.user,
                    '❌ Application Rejected by Committee',
                    f'Your application {application.application_id} has been rejected by the committee vote.',
                    f'/my-applications/{application.id}/',
                    'committee'
                )

            application.save()

        return redirect('committee:applications_list')

    return redirect('committee:review_application', app_id=app_id)