#!/usr/bin/env python
"""
Test script to debug email/SMS functionality
Run this in production to see what's happening
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tumakuru_civic.settings')
django.setup()

from django.conf import settings
from reports.notifications import _send_email, _send_sms
from reports.models import IssueReport
from accounts.models import CitizenProfile

def test_email_sms():
    print("=== Testing Email/SMS Configuration ===")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'NOT SET')}")
    print(f"EMAIL_HOST_PASSWORD: {'SET' if getattr(settings, 'EMAIL_HOST_PASSWORD', None) else 'NOT SET'}")
    print(f"SITE_URL: {getattr(settings, 'SITE_URL', 'NOT SET')}")
    print(f"FAST2SMS_API_KEY: {'SET' if getattr(settings, 'FAST2SMS_API_KEY', None) else 'NOT SET'}")
    
    print("\n=== Testing with latest report ===")
    
    # Get the latest report
    latest_report = IssueReport.objects.order_by('-created_at').first()
    if not latest_report:
        print("No reports found in database")
        return
    
    print(f"Latest Report ID: {latest_report.report_id}")
    print(f"Report Title: {latest_report.title}")
    
    # Get user profile
    profile = latest_report.citizen.profile
    print(f"User: {latest_report.citizen.username}")
    print(f"User Email: {latest_report.citizen.email}")
    print(f"User Phone: {profile.phone}")
    
    print("\n=== Testing Email ===")
    try:
        _send_email(latest_report, profile)
        print("Email function executed without errors")
    except Exception as e:
        print(f"Email failed with error: {e}")
    
    print("\n=== Testing SMS ===")
    try:
        _send_sms(latest_report, profile)
        print("SMS function executed without errors")
    except Exception as e:
        print(f"SMS failed with error: {e}")

if __name__ == "__main__":
    test_email_sms()
