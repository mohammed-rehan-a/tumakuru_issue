"""
Alternative email service for Render deployment
Uses SendGrid API instead of SMTP (more reliable on cloud platforms)
"""

import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

def send_email_via_sendgrid(to_email, subject, text_content, html_content=None):
    """
    Send email using SendGrid API (free tier available)
    More reliable than SMTP on cloud platforms like Render
    """
    try:
        api_key = getattr(settings, 'SENDGRID_API_KEY', '')
        if not api_key:
            logger.info("SendGrid API key not set - falling back to console")
            return send_email_via_console(to_email, subject, text_content, html_content)
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'tumakurucity@gmail.com')
        
        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "personalizations": [{
                "to": [{"email": to_email}],
                "subject": subject
            }],
            "from": {"email": from_email},
            "content": [
                {"type": "text/plain", "value": text_content}
            ]
        }
        
        if html_content:
            data["content"].append({"type": "text/html", "value": html_content})
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 202:
            logger.info("Email sent via SendGrid to %s", to_email)
            return True
        else:
            logger.error("SendGrid error: %s - %s", response.status_code, response.text)
            return False
            
    except Exception as e:
        logger.error("SendGrid failed: %s", e)
        return False

def send_email_via_console(to_email, subject, text_content, html_content=None):
    """
    Fallback: Print email to console/logs
    """
    logger.info("=== EMAIL TO CONSOLE ===")
    logger.info("To: %s", to_email)
    logger.info("Subject: %s", subject)
    logger.info("Text: %s", text_content)
    if html_content:
        logger.info("HTML: %s", html_content)
    logger.info("=== END EMAIL ===")
    return True

def send_email_via_mailgun(to_email, subject, text_content, html_content=None):
    """
    Alternative: Use Mailgun API (free tier available)
    """
    try:
        api_key = getattr(settings, 'MAILGUN_API_KEY', '')
        domain = getattr(settings, 'MAILGUN_DOMAIN', '')
        
        if not api_key or not domain:
            logger.info("Mailgun not configured - falling back to console")
            return send_email_via_console(to_email, subject, text_content, html_content)
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'tumakurucity@gmail.com')
        
        url = f"https://api.mailgun.net/v3/{domain}/messages"
        auth = ("api", api_key)
        data = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "text": text_content
        }
        
        if html_content:
            data["html"] = html_content
        
        response = requests.post(url, auth=auth, data=data, timeout=30)
        
        if response.status_code == 200:
            logger.info("Email sent via Mailgun to %s", to_email)
            return True
        else:
            logger.error("Mailgun error: %s - %s", response.status_code, response.text)
            return False
            
    except Exception as e:
        logger.error("Mailgun failed: %s", e)
        return False

# Try SendGrid first, then Mailgun, then console
def send_email_robust(to_email, subject, text_content, html_content=None):
    """
    Robust email sending with multiple fallbacks
    """
    # Try SendGrid first
    if send_email_via_sendgrid(to_email, subject, text_content, html_content):
        return True
    
    # Try Mailgun
    if send_email_via_mailgun(to_email, subject, text_content, html_content):
        return True
    
    # Fallback to console
    return send_email_via_console(to_email, subject, text_content, html_content)
