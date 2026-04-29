#!/usr/bin/env python
"""
Direct email test without Django to isolate the issue
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def test_gmail_smtp():
    print("=== Testing Gmail SMTP Connection ===")
    
    # Email configuration
    smtp_server = "smtp.gmail.com"
    port = 587  # For starttls
    sender_email = "tumakurucity@gmail.com"
    password = "wotz lymy yjzb opxx"  # App password
    
    # Test recipient (change to your email for testing)
    receiver_email = "test@example.com"  # Change this to your email
    
    print(f"SMTP Server: {smtp_server}:{port}")
    print(f"Sender: {sender_email}")
    print(f"Receiver: {receiver_email}")
    print(f"Password: {'SET' if password else 'NOT SET'}")
    
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Test Email from Tumakuru Civic"
        message["From"] = sender_email
        message["To"] = receiver_email
        
        # Email body
        text = """\
Hi,
This is a test email from Tumakuru Civic portal.
If you receive this, SMTP is working correctly.
        
Thanks,
Tumakuru City Corporation"""
        
        html = """\
<html>
  <body>
    <p>Hi,<br>
       This is a test email from Tumakuru Civic portal.<br>
       If you receive this, SMTP is working correctly.<br><br>
       <strong>Thanks,</strong><br>
       Tumakuru City Corporation
    </p>
  </body>
</html>
"""
        
        # Attach parts
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        message.attach(part1)
        message.attach(part2)
        
        print("\n=== Creating SMTP Connection ===")
        
        # Create SMTP session
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()  # Secure the connection
        
        print("=== Logging into Gmail ===")
        server.login(sender_email, password)
        
        print("=== Sending Email ===")
        server.sendmail(sender_email, receiver_email, message.as_string())
        
        print("=== Email sent successfully! ===")
        server.quit()
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {e}")
        print("Possible causes:")
        print("1. App password is incorrect")
        print("2. 2-Step Verification not enabled")
        print("3. App password not generated correctly")
        
    except smtplib.SMTPConnectError as e:
        print(f"SMTP Connection Error: {e}")
        print("Possible causes:")
        print("1. Render blocks SMTP connections")
        print("2. Network connectivity issues")
        print("3. SMTP server is down")
        
    except smtplib.SMTPException as e:
        print(f"SMTP Error: {e}")
        
    except Exception as e:
        print(f"Unexpected Error: {e}")

def test_fast2sms():
    print("\n=== Testing Fast2SMS API ===")
    
    import requests
    
    api_key = "Nlgj9dSIsM61DEtyzTeZxU0P3VcYCv2GX8OwJbhkrnoqKpQL7moyz3nbs05kZep2EV8hOKifTa4dtqMW"
    phone = "1234567890"  # Change to your phone for testing
    
    print(f"API Key: {'SET' if api_key else 'NOT SET'}")
    print(f"Phone: {phone}")
    
    try:
        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {
            "authorization": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "route": "q",
            "message": "Test message from Tumakuru Civic portal",
            "language": "english",
            "flash": 0,
            "numbers": phone,
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        data = response.json()
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Data: {data}")
        
        if data.get('return') is True:
            print("SMS sent successfully!")
        else:
            print(f"SMS failed: {data}")
            
    except Exception as e:
        print(f"SMS Error: {e}")

if __name__ == "__main__":
    test_gmail_smtp()
    test_fast2sms()
