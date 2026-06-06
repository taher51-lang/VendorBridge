"""
VendorBridge ERP – Email Sender
================================
Wraps Flask-Mail to send transactional emails.
All email dispatch goes through this module.
"""

from flask_mail import Message


def send_email(to: str, subject: str, body: str, html: str = None,
               attachments: list = None) -> bool:
    """
    Send a single email.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Plain-text body.
        html: Optional HTML body.
        attachments: Optional list of dicts, each with:
            - filename: str
            - content_type: str (e.g. 'application/pdf')
            - data: bytes

    Returns:
        True if sent successfully, False otherwise.

    Implementation:
        1. Import the mail instance from app (from app import mail)
        2. Create a Message(subject=subject, recipients=[to], body=body, html=html)
        3. For each attachment, call msg.attach(filename, content_type, data)
        4. Call mail.send(msg) inside a try/except
        5. Return True on success, False on exception
    """
    # TODO: Implement email sending via Flask-Mail
    pass


def send_password_reset(to: str, reset_link: str) -> bool:
    """
    Send a password reset email with a link.

    Args:
        to: User's email.
        reset_link: Full URL for the password reset page.

    Implementation:
        1. Build subject: "VendorBridge – Password Reset"
        2. Build body with the reset_link
        3. Call send_email()
    """
    # TODO: Implement
    pass


def send_invoice_email(to: str, subject: str, invoice_data: dict,
                       pdf_path: str) -> bool:
    """
    Send an invoice email with PDF attachment.

    Args:
        to: Recipient email.
        subject: Email subject.
        invoice_data: For the email body template.
        pdf_path: Path to the PDF file to attach.

    Implementation:
        1. Read PDF bytes from pdf_path
        2. Build HTML body with invoice summary
        3. Call send_email() with attachment
    """
    # TODO: Implement
    pass


def send_notification_email(to: str, title: str, body: str) -> bool:
    """
    Send a generic notification email.

    Implementation:
        1. Use a standard notification email template
        2. Call send_email()
    """
    # TODO: Implement
    pass
