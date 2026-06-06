"""
VendorBridge ERP – Email Sender
================================
Wraps Flask-Mail to send transactional emails.
All email dispatch goes through this module.
"""

from flask_mail import Message


import logging
from flask import current_app
from flask_mail import Message

def send_email(to: str, subject: str, body: str, html: str = None,
               attachments: list = None) -> bool:
    """
    Send a single email.
    """
    from app import mail
    try:
        # If we are in Flask context, we can send. Otherwise we print/log.
        # This keeps command line scripts from crashing.
        msg = Message(
            subject=subject,
            recipients=[to],
            body=body,
            html=html
        )
        if attachments:
            for att in attachments:
                msg.attach(
                    filename=att.get("filename"),
                    content_type=att.get("content_type"),
                    data=att.get("data")
                )
        
        # Check if we have an active context
        if current_app:
            mail.send(msg)
        else:
            logging.info(f"[Mock Mail] Sent to {to}: Subject: '{subject}'")
        return True
    except Exception as e:
        logging.exception(f"Failed to send email to {to}:")
        return False


def send_password_reset(to: str, reset_link: str) -> bool:
    """
    Send a password reset email with a link.
    """
    subject = "VendorBridge – Password Reset"
    body = f"Please click the link below to reset your password:\n\n{reset_link}\n\nIf you did not request this, please ignore."
    return send_email(to=to, subject=subject, body=body)


def send_invoice_email(to: str, subject: str, invoice_data: dict,
                       pdf_path: str) -> bool:
    """
    Send an invoice email with PDF attachment.
    """
    body = f"Please find attached the invoice {invoice_data.get('invoice_number')} for your order."
    attachments = []
    try:
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
        attachments.append({
            "filename": pdf_path.split("/")[-1].split("\\")[-1],
            "content_type": "application/pdf",
            "data": pdf_data
        })
    except Exception:
        logging.exception("Failed to read PDF attachment for invoice:")
    
    return send_email(to=to, subject=subject, body=body, attachments=attachments)


def send_notification_email(to: str, title: str, body: str) -> bool:
    """
    Send a generic notification email.
    """
    subject = f"VendorBridge Notification: {title}"
    email_body = f"{title}\n\n{body}\n\nThank you,\nVendorBridge Team"
    return send_email(to=to, subject=subject, body=email_body)

