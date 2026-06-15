"""
Certificate generation utility for Best Citizen Award
Tumakuru City Corporation
"""
import os
import uuid
from io import BytesIO
from datetime import datetime
from django.conf import settings


def generate_certificate_number(citizen_id, milestone):
    """Generate unique certificate number."""
    year = datetime.now().year
    return f"TCC-BC-{year}-{citizen_id:04d}-M{milestone // 100}"


def generate_tree_certificate_number(user_id, environment_save_id):
    year = datetime.now().year
    return f"TCC-TREE-{year}-{user_id:04d}-T{environment_save_id:06d}"


def generate_tree_milestone_certificate_number(user_id, milestone):
    year = datetime.now().year
    return f"TCC-TREE-M{milestone}-{year}-{user_id:04d}"


def generate_tree_milestone_pdf(user, certificate):
    """
    Generate a simple Tree Milestone PDF certificate (ReportLab).
    Returns BytesIO buffer or None if reportlab missing.
    """
    try:
        from io import BytesIO
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import HexColor

        buffer = BytesIO()
        w, h = landscape(A4)
        c = canvas.Canvas(buffer, pagesize=landscape(A4))

        # Background
        c.setFillColor(HexColor('#0A1628'))
        c.rect(0, 0, w, h, fill=1, stroke=0)

        # Border
        c.setStrokeColor(HexColor('#2ECC71'))
        c.setLineWidth(6)
        c.rect(24, 24, w - 48, h - 48, fill=0, stroke=1)

        c.setStrokeColor(HexColor('#E8C96B'))
        c.setLineWidth(2)
        c.rect(40, 40, w - 80, h - 80, fill=0, stroke=1)

        # Header
        c.setFillColor(HexColor('#E8C96B'))
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(w / 2, h - 80, "TUMAKURU CITY CORPORATION")

        c.setFillColor(HexColor('#FFFFFF'))
        c.setFont("Helvetica", 11)
        c.drawCentredString(w / 2, h - 102, "Tree Planting Milestone Certificate")

        # Title
        c.setFillColor(HexColor('#2ECC71'))
        c.setFont("Helvetica-Bold", 36)
        c.drawCentredString(w / 2, h - 170, "GREEN HERO AWARD")

        # Name
        full_name = user.get_full_name() or user.username
        c.setFillColor(HexColor('#FFD700'))
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(w / 2, h - 230, full_name.upper())

        # Body
        c.setFillColor(HexColor('#E8E8E8'))
        c.setFont("Helvetica", 12)
        c.drawCentredString(w / 2, h - 270, f"For achieving {certificate.milestone} Tree Points by planting trees.")
        c.drawCentredString(w / 2, h - 292, f"Trees saved: {certificate.trees_count_at_issue}  ·  Tree Points: {certificate.tree_points_at_issue}")

        # Info
        c.setFillColor(HexColor('#B0C4DE'))
        c.setFont("Helvetica", 10)
        c.drawCentredString(w / 2, 90, f"Certificate No: {certificate.certificate_number}")
        c.drawCentredString(w / 2, 72, f"Issue Date: {certificate.issued_date.strftime('%d %b %Y')}")

        c.save()
        buffer.seek(0)
        return buffer
    except ImportError:
        return None


def generate_certificate_pdf(citizen, certificate):
    """
    Generate a professional PDF certificate using ReportLab.
    Returns BytesIO buffer.
    """
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import inch, cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import HexColor

        buffer = BytesIO()
        page_size = landscape(A4)
        w, h = page_size

        c = canvas.Canvas(buffer, pagesize=page_size)

        # --- Background gradient effect using rectangles ---
        # Dark navy background
        c.setFillColor(HexColor('#0A1628'))
        c.rect(0, 0, w, h, fill=1, stroke=0)

        # Gold border outer
        c.setStrokeColor(HexColor('#C9A84C'))
        c.setLineWidth(8)
        c.rect(20, 20, w - 40, h - 40, fill=0, stroke=1)

        # Gold border inner
        c.setStrokeColor(HexColor('#E8C96B'))
        c.setLineWidth(2)
        c.rect(35, 35, w - 70, h - 70, fill=0, stroke=1)

        # Top decorative band
        c.setFillColor(HexColor('#C9A84C'))
        c.rect(35, h - 100, w - 70, 65, fill=1, stroke=0)

        # Bottom decorative band
        c.setFillColor(HexColor('#C9A84C'))
        c.rect(35, 35, w - 70, 65, fill=1, stroke=0)

        # --- Header in gold band ---
        c.setFillColor(HexColor('#0A1628'))
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(w / 2, h - 75, "TUMAKURU CITY CORPORATION")
        c.setFont("Helvetica", 10)
        c.drawCentredString(w / 2, h - 58, "ತುಮಕೂರು ನಗರ ನಿಗಮ  ·  Government of Karnataka")

        # --- Certificate title ---
        c.setFillColor(HexColor('#E8C96B'))
        c.setFont("Helvetica-Bold", 36)
        c.drawCentredString(w / 2, h - 165, "BEST CITIZEN AWARD")

        c.setFillColor(HexColor('#FFFFFF'))
        c.setFont("Helvetica", 13)
        c.drawCentredString(w / 2, h - 190, "Certificate of Excellence in Civic Participation")

        # Divider line
        c.setStrokeColor(HexColor('#C9A84C'))
        c.setLineWidth(1.5)
        c.line(80, h - 210, w - 80, h - 210)

        # Star decorations
        c.setFillColor(HexColor('#E8C96B'))
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(w / 2, h - 235, "★  ★  ★")

        # Presented to
        c.setFillColor(HexColor('#B0C4DE'))
        c.setFont("Helvetica", 12)
        c.drawCentredString(w / 2, h - 265, "This certificate is proudly presented to")

        # Citizen name
        full_name = citizen.user.get_full_name().upper() or citizen.user.username.upper()
        c.setFillColor(HexColor('#FFD700'))
        c.setFont("Helvetica-Bold", 30)
        c.drawCentredString(w / 2, h - 305, full_name)

        # Underline under name
        name_width = c.stringWidth(full_name, "Helvetica-Bold", 30)
        c.setStrokeColor(HexColor('#C9A84C'))
        c.setLineWidth(1)
        c.line(w/2 - name_width/2, h - 310, w/2 + name_width/2, h - 310)

        # Body text
        c.setFillColor(HexColor('#E8E8E8'))
        c.setFont("Helvetica", 12)
        body_text = (
            f"In recognition of outstanding civic participation and dedication"
        )
        c.drawCentredString(w / 2, h - 340, body_text)

        body_text2 = f"to the betterment of Tumakuru City by reporting {citizen.total_reports} civic issues"
        c.drawCentredString(w / 2, h - 358, body_text2)

        body_text3 = f"and earning {certificate.points_at_issue} Civic Points — Milestone {certificate.milestone} Points"
        c.drawCentredString(w / 2, h - 376, body_text3)

        # Info boxes
        box_y = h - 430
        box_h = 45
        box_w = 180

        info_items = [
            ("Ward No.", f"Ward {citizen.ward_number}" if citizen.ward_number else "—"),
            ("Certificate No.", certificate.certificate_number),
            ("Issue Date", certificate.issued_date.strftime("%d %B %Y")),
            ("Civic Points", str(certificate.points_at_issue)),
        ]

        start_x = (w - (len(info_items) * box_w + (len(info_items) - 1) * 15)) / 2

        for i, (label, value) in enumerate(info_items):
            bx = start_x + i * (box_w + 15)
            c.setFillColor(HexColor('#1A2B45'))
            c.setStrokeColor(HexColor('#C9A84C'))
            c.setLineWidth(1)
            c.roundRect(bx, box_y, box_w, box_h, 5, fill=1, stroke=1)
            c.setFillColor(HexColor('#C9A84C'))
            c.setFont("Helvetica", 8)
            c.drawCentredString(bx + box_w / 2, box_y + box_h - 13, label.upper())
            c.setFillColor(HexColor('#FFFFFF'))
            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(bx + box_w / 2, box_y + 10, value)

        # Signatures
        sig_y = 75
        c.setStrokeColor(HexColor('#C9A84C'))
        c.setLineWidth(0.8)

        # Left signature
        c.line(100, sig_y + 25, 260, sig_y + 25)
        c.setFillColor(HexColor('#0A1628'))
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(180, sig_y + 15, "MUNICIPAL COMMISSIONER")
        c.setFont("Helvetica", 8)
        c.drawCentredString(180, sig_y + 4, "Tumakuru City Corporation")

        # Right signature
        c.line(w - 260, sig_y + 25, w - 100, sig_y + 25)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(w - 180, sig_y + 15, "MAYOR")
        c.setFont("Helvetica", 8)
        c.drawCentredString(w - 180, sig_y + 4, "Tumakuru City Corporation")

        # Seal circle (decorative)
        c.setStrokeColor(HexColor('#C9A84C'))
        c.setFillColor(HexColor('#1A2B45'))
        c.setLineWidth(2)
        c.circle(w / 2, sig_y + 15, 28, fill=1, stroke=1)
        c.setFillColor(HexColor('#E8C96B'))
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(w / 2, sig_y + 20, "OFFICIAL")
        c.drawCentredString(w / 2, sig_y + 11, "SEAL")
        c.setFont("Helvetica", 6)
        c.drawCentredString(w / 2, sig_y + 3, "TCC")

        c.save()
        buffer.seek(0)
        return buffer

    except ImportError:
        # Fallback: return simple text-based PDF placeholder
        return None
