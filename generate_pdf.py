import os
import sys
import subprocess

def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
except ImportError:
    print("Installing reportlab for PDF generation...")
    try:
        install_package("reportlab")
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
    except Exception as e:
        print(f"Could not install reportlab automatically: {e}")

def create_pdf(filename="AutoPay_Guard_Documentation.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    styles = getSampleStyleSheet()
    
    primary_color = colors.HexColor("#4F46E5") # Indigo
    secondary_color = colors.HexColor("#0F172A") # Dark Navy
    accent_color = colors.HexColor("#10B981") # Emerald
    bg_light = colors.HexColor("#F8FAFC")
    text_dark = colors.HexColor("#1E293B")
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        alignment=0,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#64748B"),
        alignment=0,
        spaceAfter=15
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=secondary_color,
        spaceBefore=12,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=4
    )
    
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=text_dark,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3
    )
    
    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
        backColor=colors.HexColor("#F1F5F9"),
        borderColor=colors.HexColor("#CBD5E1"),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=6
    )
    
    story = []
    
    # Header Title
    story.append(Paragraph("🛡️ AutoPay Guard — Comprehensive System Documentation", title_style))
    story.append(Paragraph("Complete Workflow, System Architecture & Implemented Features Overview | Version 1.0", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=0, spaceAfter=12))
    
    # Executive Summary
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(Paragraph(
        "<b>AutoPay Guard</b> is an enterprise-grade automated Subscription, Loan EMI, and Recurring Payment Tracker & Alert System. "
        "It protects users against unexpected bank charges, unannounced trial renewals, credit card auto-debits, and late payment penalties. "
        "The system incorporates multi-channel proactive notifications (Email, Web Push, WhatsApp, Google Calendar) and strict GDPR data privacy compliance.",
        body_style
    ))
    
    # System Architecture
    story.append(Paragraph("2. System Architecture & Tech Stack", h1_style))
    
    tech_data = [
        [Paragraph("<b>Layer</b>", body_style), Paragraph("<b>Technology Stack</b>", body_style), Paragraph("<b>Key Responsibilities</b>", body_style)],
        [Paragraph("<b>Frontend UI</b>", body_style), Paragraph("React (Vite), TailwindCSS / Glassmorphism UI", body_style), Paragraph("Responsive User Dashboard, Auth Screens, EMI & Subscription hub, Analytics charts.", body_style)],
        [Paragraph("<b>Backend API</b>", body_style), Paragraph("Python FastAPI, Uvicorn, Pydantic", body_style), Paragraph("REST API endpoints, business logic execution, audit logging, GDPR handlers.", body_style)],
        [Paragraph("<b>Database & Auth</b>", body_style), Paragraph("Supabase PostgreSQL + Supabase Auth", body_style), Paragraph("User identity, row-level security (RLS), encrypted database storage.", body_style)],
        [Paragraph("<b>Email Engine</b>", body_style), Paragraph("Brevo Custom SMTP Relay", body_style), Paragraph("High-deliverability 6-digit OTP codes for account verification & password reset.", body_style)],
        [Paragraph("<b>Multi-Channel Alerts</b>", body_style), Paragraph("Firebase FCM, Meta Cloud API, Google Calendar API", body_style), Paragraph("Browser Push Notifications, WhatsApp automated messages, Google Calendar event sync.", body_style)]
    ]
    
    t = Table(tech_data, colWidths=[1.3*inch, 2.7*inch, 3.2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light])
    ]))
    # Fix header text color inside table
    for i in range(3):
        tech_data[0][i].style.textColor = colors.white
    
    story.append(t)
    story.append(Spacer(1, 10))
    
    # Workflows Implemented
    story.append(Paragraph("3. Core Workflows & Implemented Features", h1_style))
    
    story.append(Paragraph("A. Authentication & Security Flow", h2_style))
    story.append(Paragraph("• <b>Account Registration with 6-Digit Email OTP:</b> Users register with Name, Email, Phone, and Password. Account creation triggers a Brevo SMTP 6-digit verification code sent to their inbox.", bullet_style))
    story.append(Paragraph("• <b>Dual Login Support:</b> Supports standard Email + Password login and Phone Number OTP authentication.", bullet_style))
    story.append(Paragraph("• <b>Password Recovery ('Forgot Password' Workflow):</b> Enter Email → 6-digit OTP sent to inbox → Enter OTP → Verified → Set New Password screen (no current password needed) → Instant password update.", bullet_style))
    story.append(Paragraph("• <b>Supabase Row-Level Security (RLS):</b> Ensures users can exclusively query and modify their own financial records.", bullet_style))

    story.append(Paragraph("B. Subscription & Loan EMI Management", h2_style))
    story.append(Paragraph("• <b>Comprehensive Tracking:</b> Track Netflix, Spotify, AWS, Gym, Rent, Home Loans, Car EMIs, and Personal Loans.", bullet_style))
    story.append(Paragraph("• <b>Auto-Pay vs Manual Pay Modes:</b> Distinguishes between automatic credit/debit card debits and manual bank transfers.", bullet_style))
    story.append(Paragraph("• <b>Billing Cycle & Renewal Calculation:</b> Monthly, Quarterly, and Annual recurrence logic automatically calculates exact upcoming due dates.", bullet_style))
    story.append(Paragraph("• <b>Interactive Financial Analytics:</b> Real-time monthly spend outlays, upcoming auto-debits in 7 days, and trial expiration warnings.", bullet_style))

    story.append(Paragraph("C. Multi-Channel Reminder & Alert Engine", h2_style))
    story.append(Paragraph("• <b>Firebase Cloud Messaging (FCM):</b> Real-time web push notifications on desktop/mobile browsers.", bullet_style))
    story.append(Paragraph("• <b>WhatsApp Business Messaging:</b> Automated reminder alerts delivered directly to user's WhatsApp via Meta Cloud API.", bullet_style))
    story.append(Paragraph("• <b>Google Calendar Event Sync:</b> Automatic creation of Google Calendar event reminders on payment due dates.", bullet_style))
    story.append(Paragraph("• <b>Automated Daily Scheduler:</b> Background engine runs daily scans triggering alerts at T-3 days, T-1 day, and on the due date.", bullet_style))

    story.append(Paragraph("D. Audit Logging & GDPR Compliance", h2_style))
    story.append(Paragraph("• <b>Audit Trail:</b> Internal AuditLoggerService records critical events (USER_SIGNUP, USER_LOGIN, PASSWORD_CHANGE, SUBSCRIPTION_CREATE).", bullet_style))
    story.append(Paragraph("• <b>GDPR Data Portability:</b> Download full account data, subscriptions, EMIs, and logs as JSON.", bullet_style))
    story.append(Paragraph("• <b>GDPR Right to be Forgotten:</b> Permanently delete user profile and associated database records upon request.", bullet_style))

    story.append(Spacer(1, 10))
    story.append(Paragraph("4. Quick Start & Execution Commands", h1_style))
    story.append(Paragraph("<b>Backend Server (FastAPI):</b>", body_style))
    story.append(Paragraph("uvicorn backend.main:app --reload --port 8000", code_style))
    story.append(Paragraph("<b>Frontend Development Server (Vite):</b>", body_style))
    story.append(Paragraph("npm run dev", code_style))

    doc.build(story)
    print(f"✅ PDF successfully generated at: {os.path.abspath(filename)}")

if __name__ == "__main__":
    create_pdf()
