"""
notifications.py
────────────────────────────────────────────────────────
Tumakuru Civic Portal — Email & SMS notification service
Sends thank-you messages after every report submission.

EMAIL  → Django SMTP (Gmail)
SMS    → Fast2SMS (free Indian SMS API)
────────────────────────────────────────────────────────
"""

import logging
import threading
import requests
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)

def _send_web_push(user, title, body, url_path='/dashboard/'):
    """
    Send a Web Push notification (PWA) to all user subscriptions.
    Requires VAPID keys in settings and pywebpush installed.
    """
    public_key = getattr(settings, 'VAPID_PUBLIC_KEY', '')
    private_key = getattr(settings, 'VAPID_PRIVATE_KEY', '')
    if not public_key or not private_key:
        return
    try:
        from pywebpush import webpush, WebPushException
        from accounts.models import PushSubscription
        import json

        subs = PushSubscription.objects.filter(user=user)
        if not subs.exists():
            return

        payload = json.dumps({
            'title': title,
            'body': body,
            'url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000') + url_path,
        })
        vapid_claims = {"sub": getattr(settings, 'VAPID_CLAIMS_EMAIL', 'mailto:admin@tumakuru.gov.in')}

        for s in subs:
            subscription_info = {
                "endpoint": s.endpoint,
                "keys": {"p256dh": s.p256dh, "auth": s.auth},
            }
            try:
                webpush(
                    subscription_info=subscription_info,
                    data=payload,
                    vapid_private_key=private_key,
                    vapid_claims=vapid_claims,
                )
            except Exception:
                # Ignore failures for individual endpoints
                continue
    except Exception:
        return


# ─────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────

def _run_in_thread(fn, *args, **kwargs):
    """Run a function in a background thread so the user
    is never kept waiting for email/SMS to send."""
    t = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
    t.start()


def _progress_percent(total_points, threshold=100):
    return min(int((total_points % threshold) / threshold * 100), 100)


def _points_to_cert(total_points, threshold=100):
    rem = threshold - (total_points % threshold)
    return 0 if rem == threshold else rem


# ─────────────────────────────────────────────────────────
# EMAIL
# ─────────────────────────────────────────────────────────

def _send_email(report, profile):
    """Send the HTML thank-you email. Updated for Render compatibility."""
    try:
        user = profile.user
        email = user.email
        if not email:
            logger.info("No email for user %s - skipping email.", user.username)
            return

        citizen_name = user.get_full_name() or user.username
        total_points = profile.points
        threshold    = getattr(settings, 'POINTS_FOR_CERTIFICATE', 100)
        points_earned = getattr(settings, 'POINTS_PER_REPORT', 5)
        dashboard_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000') + '/dashboard/'

        context = {
            'citizen_name'   : citizen_name,
            'report_id'      : report.report_id,
            'report_title'   : report.title,
            'category'       : report.category.name if report.category else 'General',
            'ward'           : report.ward_number,
            'points_earned'  : points_earned,
            'total_points'   : total_points,
            'points_to_cert' : _points_to_cert(total_points, threshold),
            'progress_percent': _progress_percent(total_points, threshold),
            'dashboard_url'  : dashboard_url,
        }

        subject    = f" Report Received [{report.report_id}] - Tumakuru City Corporation"
        text_body  = (
            f"Dear {citizen_name},\n\n"
            f"Your civic issue report has been received.\n"
            f"Report ID : {report.report_id}\n"
            f"Issue     : {report.title}\n"
            f"Ward      : {report.ward_number}\n"
            f"Points    : +{points_earned} (Total: {total_points})\n\n"
            f"Track your report: {dashboard_url}\n\n"
            f"Thank you for making Tumakuru better!\n"
            f"Tumakuru City Corporation\n"
            f"Helpline: 1800-425-0006"
        )

        html_body = render_to_string('emails/thank_you_report.html', context)

        # Try robust email service first
        from .email_service import send_email_robust
        success = send_email_robust(email, subject, text_body, html_body)
        
        if success:
            logger.info(" Thank-you email sent to %s", email)
        else:
            logger.error("All email methods failed for report %s", report.report_id)

    except Exception as exc:
        logger.error("Email send failed for report %s: %s", report.report_id, exc)
        import traceback
        traceback.print_exc()


# ─────────────────────────────────────────────────────────
# SMS  (Fast2SMS — free Indian SMS API)
# ─────────────────────────────────────────────────────────

def _send_sms(report, profile):
    """Send SMS via Fast2SMS. Called in a thread."""
    try:
        api_key = getattr(settings, 'FAST2SMS_API_KEY', '')
        if not api_key:
            logger.info("FAST2SMS_API_KEY not set — skipping SMS.")
            return

        phone = profile.phone
        if not phone:
            logger.info("No phone for user %s — skipping SMS.", profile.user.username)
            return

        # Clean phone: remove +91, spaces, dashes
        phone = ''.join(filter(str.isdigit, phone))
        if phone.startswith('91') and len(phone) == 12:
            phone = phone[2:]
        if len(phone) != 10:
            logger.warning("Invalid phone number '%s' — skipping SMS.", phone)
            return

        citizen_name  = profile.user.get_full_name() or profile.user.username
        points_earned = getattr(settings, 'POINTS_PER_REPORT', 5)
        total_points  = profile.points
        threshold     = getattr(settings, 'POINTS_FOR_CERTIFICATE', 100)
        to_cert       = _points_to_cert(total_points, threshold)

        message = (
            f"Dear {citizen_name}, your civic report [{report.report_id}] "
            f"has been received by Tumakuru City Corporation. "
            f"You earned +{points_earned} points! Total: {total_points} pts. "
            f"{to_cert} more for Best Citizen Certificate. "
            f"Track: tumakuru.gov.in/dashboard  -TCC"
        )

        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {
            "authorization": api_key,
            "Content-Type" : "application/json",
        }
        payload = {
            "route"   : "q",          # Transactional route
            "message" : message,
            "language": "english",
            "flash"   : 0,
            "numbers" : phone,
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        data = response.json()

        if data.get('return') is True:
            logger.info("📱 SMS sent to %s", phone)
        else:
            logger.error("Fast2SMS error for %s: %s", phone, data)

    except Exception as exc:
        logger.error("SMS send failed for report %s: %s", report.report_id, exc)


# ─────────────────────────────────────────────────────────
# PUBLIC API  — call this from views.py
# ─────────────────────────────────────────────────────────

def send_report_thankyou(report, profile):
    """
    Send thank-you Email + SMS after a report is submitted.
    Made synchronous for debugging on Render.
    """
    try:
        _send_email(report, profile)
        _send_sms(report, profile)
        logger.info("Notifications sent for report %s", report.report_id)
    except Exception as e:
        logger.error("Notification failed for report %s: %s", report.report_id, e)

# ─────────────────────────────────────────────────────────
# CERTIFICATE EMAIL
# ─────────────────────────────────────────────────────────

def _send_certificate_email(profile, certificate):
    """Send congratulations email when a certificate is earned."""
    try:
        user  = profile.user
        email = user.email
        if not email:
            return

        citizen_name = user.get_full_name() or user.username
        subject      = f"🏆 Congratulations! Best Citizen Certificate — {certificate.certificate_number}"
        from_email   = settings.DEFAULT_FROM_EMAIL

        text_body = (
            f"Dear {citizen_name},\n\n"
            f"CONGRATULATIONS! 🎉\n\n"
            f"You have earned the BEST CITIZEN CERTIFICATE from Tumakuru City Corporation!\n\n"
            f"Certificate No : {certificate.certificate_number}\n"
            f"Milestone      : {certificate.milestone} Civic Points\n"
            f"Issued On      : {certificate.issued_date.strftime('%d %B %Y')}\n\n"
            f"Download your certificate at:\n"
            f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/reports/certificate/{certificate.pk}/\n\n"
            f"Thank you for your outstanding civic contribution to Tumakuru!\n"
            f"Tumakuru City Corporation"
        )

        # Try robust email service first
        from .email_service import send_email_robust
        success = send_email_robust(email, subject, text_body)
        
        if success:
            logger.info("🏆 Certificate email sent to %s", email)
        else:
            logger.error("🏆 Certificate email failed for %s", user.username)

    except Exception as exc:
        logger.error("Certificate email failed: %s", exc)


def _send_certificate_sms(profile, certificate):
    """Send congratulations SMS when a certificate is earned."""
    try:
        api_key = getattr(settings, 'FAST2SMS_API_KEY', '')
        if not api_key or not profile.phone:
            return

        phone = ''.join(filter(str.isdigit, profile.phone))
        if phone.startswith('91') and len(phone) == 12:
            phone = phone[2:]
        if len(phone) != 10:
            return

        citizen_name = profile.user.get_full_name() or profile.user.username
        message = (
            f"Congratulations {citizen_name}! You have earned the BEST CITIZEN CERTIFICATE "
            f"[{certificate.certificate_number}] from Tumakuru City Corporation for reaching "
            f"{certificate.milestone} Civic Points! Download: tumakuru.gov.in/dashboard  -TCC"
        )

        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {"authorization": api_key, "Content-Type": "application/json"}
        payload = {"route": "q", "message": message, "language": "english", "flash": 0, "numbers": phone}
        requests.post(url, json=payload, headers=headers, timeout=10)
        logger.info("🏆 Certificate SMS sent to %s", phone)

    except Exception as exc:
        logger.error("Certificate SMS failed: %s", exc)


def send_certificate_notification(profile, certificate):
    """Send certificate congratulations via Email + SMS."""
    _run_in_thread(_send_certificate_email, profile, certificate)
    _run_in_thread(_send_certificate_sms,   profile, certificate)

# ─────────────────────────────────────────────────────────
# STATUS UPDATE EMAIL & SMS
# ─────────────────────────────────────────────────────────

def _send_status_email(report, profile):
    """Send an email when report status changes to In Progress or Resolved."""
    try:
        user = profile.user
        email = user.email
        if not email:
            return

        citizen_name = user.get_full_name() or user.username
        status_display = report.get_status_display()
        dashboard_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000') + '/dashboard/'

        subject = f"🔔 Status Update: {status_display} — Report [{report.report_id}]"
        from_email = settings.DEFAULT_FROM_EMAIL

        text_body = (
            f"Dear {citizen_name},\n\n"
            f"The status of your civic issue report has been updated to: {status_display}.\n\n"
            f"Report ID : {report.report_id}\n"
            f"Issue     : {report.title}\n\n"
        )
        
        if report.status == 'resolved':
            text_body += f"Resolution Remarks: {report.admin_remarks or 'Issue has been successfully resolved.'}\n\n"
            text_body += f"Please login to your dashboard to provide feedback: {dashboard_url}\n\n"
        else:
            text_body += f"Our team is currently working on it. Track here: {dashboard_url}\n\n"
            
        text_body += (
            f"Thank you for making Tumakuru better!\n"
            f"Tumakuru City Corporation\n"
        )

        # Try robust email service first
        from .email_service import send_email_robust
        success = send_email_robust(email, subject, text_body)
        
        if success:
            logger.info("✉️  Status update email sent to %s", email)
        else:
            logger.error("✉️  Status update email failed for report %s", report.report_id)

    except Exception as exc:
        logger.error("Status update email failed for report %s: %s", report.report_id, exc)


def _send_status_sms(report, profile):
    """Send SMS when report status changes."""
    try:
        api_key = getattr(settings, 'FAST2SMS_API_KEY', '')
        if not api_key or not profile.phone:
            return

        phone = ''.join(filter(str.isdigit, profile.phone))
        if phone.startswith('91') and len(phone) == 12:
            phone = phone[2:]
        if len(phone) != 10:
            return

        citizen_name = profile.user.get_full_name() or profile.user.username
        status_display = report.get_status_display()
        
        message = (
            f"Update {citizen_name}: Your report [{report.report_id}] "
            f"status is now {status_display}. "
            f"Track at: tumakuru.gov.in/dashboard -TCC"
        )

        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {"authorization": api_key, "Content-Type": "application/json"}
        payload = {"route": "q", "message": message, "language": "english", "flash": 0, "numbers": phone}
        requests.post(url, json=payload, headers=headers, timeout=10)
        logger.info("📱 Status update SMS sent to %s", phone)

    except Exception as exc:
        logger.error("Status update SMS failed for report %s: %s", report.report_id, exc)


def send_status_update_notification(report, profile):
    """Send status update via Email + SMS."""
    _run_in_thread(_send_status_email, report, profile)
    _run_in_thread(_send_status_sms,   report, profile)
    _run_in_thread(
        _send_web_push,
        profile.user,
        f"Report {report.report_id} updated",
        f"Status is now {report.get_status_display()}",
        f"/reports/{report.pk}/",
    )

