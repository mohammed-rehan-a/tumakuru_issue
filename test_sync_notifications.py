#!/usr/bin/env python
"""
Test synchronous email/SMS sending (no threads)
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

def test_sync_notifications():
    print("=== Testing Synchronous Email/SMS ===")
    
    # Get the latest report
    latest_report = IssueReport.objects.order_by('-created_at').first()
    if not latest_report:
        print("No reports found in database")
        return
    
    print(f"Testing with Report ID: {latest_report.report_id}")
    
    # Get user profile
    profile = latest_report.citizen.profile
    print(f"User Email: {latest_report.citizen.email}")
    print(f"User Phone: {profile.phone}")
    
    print("\n=== Testing Synchronous Email ===")
    try:
        _send_email(latest_report, profile)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Email failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Testing Synchronous SMS ===")
    try:
        _send_sms(latest_report, profile)
        print("SMS sent successfully!")
    except Exception as e:
        print(f"SMS failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sync_notifications()
