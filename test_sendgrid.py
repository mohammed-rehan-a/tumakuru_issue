#!/usr/bin/env python
"""
Test SendGrid API directly
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tumakuru_civic.settings')
django.setup()

from django.conf import settings
from reports.email_service import send_email_robust

def test_sendgrid():
    print("=== Testing SendGrid Email Service ===")
    print(f"SENDGRID_API_KEY: {'SET' if getattr(settings, 'SENDGRID_API_KEY', None) else 'NOT SET'}")
    print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT SET')}")
    
    # Test email - change to your email for testing
    test_email = "tumakurucity@gmail.com"  # CHANGE THIS TO YOUR EMAIL
    subject = "Test Email from Tumakuru Civic"
    text_content = "This is a test email from the Tumakuru Civic portal using SendGrid."
    html_content = "<p>This is a <strong>test email</strong> from the Tumakuru Civic portal using SendGrid.</p>"
    
    print(f"\nSending test email to: {test_email}")
    
    try:
        success = send_email_robust(test_email, subject, text_content, html_content)
        if success:
            print("Email sent successfully!")
        else:
            print("Email failed - check logs above")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sendgrid()
