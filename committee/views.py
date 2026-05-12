from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from decimal import Decimal

from main.models import LoanApplication, CommitteeVote, Notification
from .models import CommitteeProfile


@login_required
def dashboard(request):
    """Committee Dashboard"""
    # Get committee profile
    try:
        committee_profile = CommitteeProfile.objects.get(user=request.user)
    except CommitteeProfile.DoesNotExist:
        committee_profile = None

    # Get pending applications (with_committee status)
    pending_applications = LoanApplication.objects.filter(
        status='with_committee'
    ).order_by('-created_at')

    # Get user's voting history
    user_votes = CommitteeVote.objects.filter(
        committee_member=request.user
    ).values_list('application_id', flat=True)

    # Calculate counts
    total_pending = pending_applications.count()
    voted_count = user_votes.count()
    remaining_count = total_pending - voted_count

    context = {
        'committee_profile': committee_profile,
        'pending_applications': pending_applications[:10],
        'total_pending': total_pending,
        'voted_count': voted_count,
        'remaining_count': remaining_count,
        'committee_members_count': CommitteeProfile.objects.filter(is_active=True).count(),
    }
    return render(request, 'committee/dashboard.html', context)


@login_required
def applications_list(request):
    """List of pending applications"""
    applications = LoanApplication.objects.filter(
        status='with_committee'
    ).order_by('-created_at')

    user_votes = CommitteeVote.objects.filter(
        committee_member=request.user
    ).values_list('application_id', flat=True)

    # Add has_voted flag to each application
    for app in applications:
        app.has_voted = app.id in user_votes

    context = {
        'applications': applications,
        'total_pending': applications.count(),
        'not_voted_count': applications.count() - user_votes.count(),
        'voted_count': user_votes.count(),
    }
    return render(request, 'committee/applications_list.html', context)


@login_required
def review_application(request, app_id):
    """Review a single application"""
    application = get_object_or_404(LoanApplication, id=app_id)

    # Check if user has already voted
    existing_vote = CommitteeVote.objects.filter(
        application=application,
        committee_member=request.user
    ).first()
    has_voted = existing_vote is not None

    # Handle form submission
    if request.method == 'POST':
        action = request.POST.get('action')

        if not has_voted:
            vote = CommitteeVote.objects.create(
                application=application,
                committee_member=request.user,
                vote=action,
                approved_line=request.POST.get('approved_line') if action == 'approve' else None,
                reduction_reason=request.POST.get('reduction_reason'),
                reason=request.POST.get('reason')
            )

            # Update application status if all committee members have voted
            total_committee = CommitteeProfile.objects.filter(is_active=True).count()
            votes_count = CommitteeVote.objects.filter(application=application).count()

            if votes_count >= total_committee:
                # Check if majority approved
                approved_count = CommitteeVote.objects.filter(application=application, vote='approved').count()
                if approved_count > total_committee / 2:
                    application.status = 'line_approved'
                    # Save the average approved line if multiple approvals
                    approved_lines = CommitteeVote.objects.filter(application=application, vote='approved').exclude(
                        approved_line=None).values_list('approved_line', flat=True)
                    if approved_lines:
                        application.approved_line = sum(approved_lines) / len(approved_lines)
                else:
                    application.status = 'rejected'
                application.save()

            messages.success(request, 'Your vote has been recorded successfully!')
        else:
            messages.warning(request, 'You have already voted on this application.')

        return redirect('committee:applications_list')

    # Get committee votes for this application
    committee_votes = CommitteeVote.objects.filter(application=application)
    votes_approved = committee_votes.filter(vote='approved').count()
    votes_rejected = committee_votes.filter(vote='rejected').count()
    total_votes = committee_votes.count()

    # Calculate suggested amounts
    requested = application.requested_amount
    suggested_full = float(requested)
    suggested_90 = float(requested) * 0.9
    suggested_70 = float(requested) * 0.7

    context = {
        'application': application,
        'member': application.member,
        'loan_product': application.loan_product,
        'has_voted': has_voted,
        'existing_vote': existing_vote,
        'committee_votes': committee_votes,
        'votes_approved': votes_approved,
        'votes_rejected': votes_rejected,
        'total_votes': total_votes,
        'suggested_full': suggested_full,
        'suggested_90': suggested_90,
        'suggested_70': suggested_70,
    }
    return render(request, 'committee/review_application.html', context)


@login_required
def application_detail(request, app_id):
    """View application details"""
    application = get_object_or_404(LoanApplication, id=app_id)
    return render(request, 'committee/application_detail.html', {'application': application})


@login_required
def decision_history(request):
    """View user's decision history"""
    votes = CommitteeVote.objects.filter(
        committee_member=request.user
    ).order_by('-voted_at').select_related('application', 'application__member')

    # Add properties for template
    for vote in votes:
        vote.application_id_display = vote.application.application_id
        vote.member_name = f"{vote.application.member.last_name}, {vote.application.member.first_name}"
        vote.requested_amount = vote.application.requested_amount
        vote.loan_type = vote.application.loan_product.name if vote.application.loan_product else 'N/A'
        vote.application_status = vote.application.status
        vote.voted_date = vote.voted_at.strftime('%Y-%m-%d %H:%M')

    total_count = votes.count()
    approved_count = votes.filter(vote='approved').count()
    rejected_count = votes.filter(vote='rejected').count()

    # Get pending applications count
    pending_applications_count = LoanApplication.objects.filter(
        status='with_committee'
    ).count()

    context = {
        'applications': votes,
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
                'requested_amount': float(vote.application.requested_amount),
                'my_vote': vote.vote,
                'status': vote.application.status,
                'voted_date': vote.voted_at.strftime('%Y-%m-%d')
            })
        data = {'success': True, 'votes': vote_list}

    elif report_type == 'performance':
        total = votes.count()
        approved = votes.filter(vote='approved').count()
        approval_rate = int((approved / total * 100)) if total > 0 else 0

        # Monthly data
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
                'requested_amount': float(vote.application.requested_amount),
                'approved_line': float(vote.application.approved_line) if vote.application.approved_line else 0,
                'decision': vote.vote,
                'review_date': vote.voted_at.strftime('%Y-%m-%d')
            })
        data = {'success': True, 'applications': app_list}

    else:
        data = {'success': False, 'error': 'Invalid report type'}

    return JsonResponse(data)


@login_required
def notifications_list(request):
    """View notifications - FIXED: using 'recipient' instead of 'user'"""
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    # Pagination
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
    """API endpoint for notification count - FIXED: using 'recipient' instead of 'user'"""
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'unread_count': unread_count})


@login_required
def mark_notification_read(request, notif_id):
    """Mark a single notification as read - FIXED: using 'recipient' instead of 'user'"""
    notification = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read - FIXED: using 'recipient' instead of 'user'"""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})


@login_required
def profile(request):
    """Committee member profile page"""
    try:
        committee_profile = CommitteeProfile.objects.get(user=request.user)
    except CommitteeProfile.DoesNotExist:
        committee_profile = CommitteeProfile.objects.create(user=request.user)

    # Get voting statistics
    votes = CommitteeVote.objects.filter(committee_member=request.user)
    total_votes = votes.count()
    approved_votes = votes.filter(vote='approved').count()
    rejected_votes = votes.filter(vote='rejected').count()
    approval_rate = int((approved_votes / total_votes * 100)) if total_votes > 0 else 0

    # Get monthly votes
    current_month = timezone.now().month
    monthly_votes = votes.filter(voted_at__month=current_month).count()

    # Get recent votes
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

        # Update committee profile
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

        # Check current password
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

    # Change password to force logout from all sessions
    new_password = secrets.token_urlsafe(32)
    request.user.password = make_password(new_password)
    request.user.save()

    messages.info(request, 'You have been logged out from all devices.')
    return redirect('main:login')


@login_required
def committee_logout(request):
    """Committee logout"""
    auth_logout(request)
    return redirect('main:landing')