"""
VendorBridge ERP – Email Sender
================================
Wraps Flask-Mail to send transactional emails.
All email dispatch goes through this module.
"""

from flask_mail import Message


def send_email(
    to: str,
    subject: str,
    body: str,
    html: str = None,
    attachments: list = None,
) -> bool:
    """
    Send a single email.

    Args:
        to:          Recipient email address.
        subject:     Email subject line.
        body:        Plain-text body fallback.
        html:        Optional HTML body.
        attachments: Optional list of dicts, each with:
                       - filename:     str  (e.g. 'INV-2025-0001.pdf')
                       - content_type: str  (e.g. 'application/pdf')
                       - data:         bytes

    Returns:
        True if sent successfully, False otherwise.
    """
    try:
        from app import mail  # import the extension initialised in app/__init__.py

        msg = Message(subject=subject, recipients=[to], body=body, html=html)

        if attachments:
            for att in attachments:
                msg.attach(att["filename"], att["content_type"], att["data"])

        mail.send(msg)
        return True

    except Exception as exc:
        # Log to stdout – replace with proper logging in production
        print(f"[email_sender] Failed to send email to {to}: {exc}")
        return False


def send_password_reset(to: str, reset_link: str) -> bool:
    """
    Send a password reset email with a reset link.

    Args:
        to:         User's email address.
        reset_link: Full URL for the password reset page.
    """
    subject = "VendorBridge – Password Reset Request"
    body = (
        f"You requested a password reset for your VendorBridge account.\n\n"
        f"Click the link below to reset your password:\n{reset_link}\n\n"
        f"This link expires in 1 hour.\n"
        f"If you did not request this, please ignore this email."
    )
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; padding: 24px;">
        <h2 style="color: #1a1a2e;">Password Reset</h2>
        <p>You requested a password reset for your VendorBridge account.</p>
        <p>
            <a href="{reset_link}"
               style="display:inline-block; padding:12px 24px; background:#4f46e5;
                      color:#fff; text-decoration:none; border-radius:6px;">
                Reset Password
            </a>
        </p>
        <p style="color:#666; font-size:13px;">
            This link expires in 1 hour. If you didn't request this, ignore this email.
        </p>
        <hr style="border:none; border-top:1px solid #eee; margin:24px 0;">
        <p style="color:#999; font-size:12px;">VendorBridge ERP</p>
    </div>
    """
    return send_email(to, subject, body, html=html)


def send_invoice_email(
    to: str,
    subject: str,
    invoice_data: dict,
    pdf_path: str,
) -> bool:
    """
    Send an invoice email with the PDF attached.

    Args:
        to:           Recipient email address.
        subject:      Email subject line.
        invoice_data: Dict with invoice fields for the email body template.
        pdf_path:     Absolute path to the generated PDF file.
    """
    try:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
    except (FileNotFoundError, IOError) as exc:
        print(f"[email_sender] Cannot read PDF at {pdf_path}: {exc}")
        return False

    inv_number  = invoice_data.get("invoice_number", "Invoice")
    vendor_name = invoice_data.get("vendor_name", "")
    total       = invoice_data.get("total_amount", "0.00")
    due_date    = invoice_data.get("due_date", "")

    body = (
        f"Dear {vendor_name},\n\n"
        f"Please find attached invoice {inv_number} for ₹{total}.\n"
        f"Due Date: {due_date}\n\n"
        f"Thank you for your business.\n"
        f"— VendorBridge Team"
    )

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; padding: 24px;">
        <h2 style="color: #1a1a2e;">Invoice {inv_number}</h2>
        <p>Dear <strong>{vendor_name}</strong>,</p>
        <p>Please find your invoice attached to this email.</p>
        <table style="border-collapse:collapse; width:100%; margin:16px 0;">
            <tr style="background:#f8f9fa;">
                <td style="padding:8px 12px; font-weight:bold;">Invoice Number</td>
                <td style="padding:8px 12px;">{inv_number}</td>
            </tr>
            <tr>
                <td style="padding:8px 12px; font-weight:bold;">Total Amount</td>
                <td style="padding:8px 12px;">₹{total}</td>
            </tr>
            <tr style="background:#f8f9fa;">
                <td style="padding:8px 12px; font-weight:bold;">Due Date</td>
                <td style="padding:8px 12px;">{due_date}</td>
            </tr>
        </table>
        <p>Please make payment by the due date to avoid any delays.</p>
        <p style="color:#666;">Thank you for your business.</p>
        <hr style="border:none; border-top:1px solid #eee; margin:24px 0;">
        <p style="color:#999; font-size:12px;">VendorBridge ERP</p>
    </div>
    """

    attachment = {
        "filename":     f"{inv_number}.pdf",
        "content_type": "application/pdf",
        "data":         pdf_bytes,
    }

    return send_email(to, subject, body, html=html, attachments=[attachment])


def send_notification_email(to: str, title: str, body: str) -> bool:
    """
    Send a generic in-app notification as an email.

    Args:
        to:   Recipient email address.
        title: Notification title (used as subject suffix).
        body: Notification message body.
    """
    subject = f"VendorBridge – {title}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; padding: 24px;">
        <h2 style="color: #1a1a2e;">{title}</h2>
        <p>{body}</p>
        <hr style="border:none; border-top:1px solid #eee; margin:24px 0;">
        <p style="color:#999; font-size:12px;">VendorBridge ERP</p>
    </div>
    """
    return send_email(to, subject, body, html=html)
