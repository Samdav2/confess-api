import sys
import os
from app.dependencies.email_service import EmailService

# Add app to path
sys.path.append(os.getcwd())

def send_all_templates():
    recipients = [
        "adoxop1@gmail.com",
        "amiolademilade@gmail.com"
    ]

    templates = [
        ("Welcome Email", "user_welcome.html", {"title": "Welcome to Confess!", "name": "Test User"}),
        ("Waitlist", "waitlist.html", {"title": "You're on the Waitlist!", "name": "Test User"}),
        ("Email Verification", "email_verification.html", {"title": "Verify Your Email", "user_name": "Test User", "verification_link": "http://confess.com.ng/verify/abc123"}),
        ("Email Verified", "email_verified_notice.html", {"title": "Email Verified", "user_name": "Test User"}),
        ("Password Reset", "password_reset.html", {"title": "Reset Password", "user_name": "Test User", "reset_link": "http://confess.com.ng/reset/xyz789"}),
        ("Password Changed", "password_change_notice.html", {"title": "Password Changed", "user_name": "Test User"}),
        ("Email Changed", "email_change_notice.html", {"title": "Email Changed", "user_name": "Test User", "old_email": "old@example.com", "new_email": "new@example.com"}),
        ("Purchase Success", "purchase_success.html", {"title": "Purchase Successful", "user_name": "Test User", "service_name": "Premium Plan", "amount": "₦5,000", "recipient": "Test User", "transaction_ref": "TXN123456"}),
        ("Purchase Failed", "purchase_failed.html", {"title": "Purchase Failed", "user_name": "Test User", "service_name": "Premium Plan", "amount": "₦5,000", "transaction_ref": "TXN123456", "reason": "Insufficient Funds"}),
        ("Refund Processed", "refund_processed.html", {"title": "Refund Processed", "user_name": "Test User", "service_name": "Premium Plan", "amount": "₦5,000", "transaction_ref": "TXN123456"}),
        ("Ticket Created", "ticket_created.html", {"title": "Ticket Created", "name": "Test User", "ticket_id": "12345", "subject": "Help with my account", "message_preview": "I need help with..."}),
        ("Ticket Reply (Admin)", "ticket_reply_admin.html", {"title": "Ticket Reply", "name": "Test User", "ticket_id": "12345", "reply_message": "Thank you for reaching out. We have resolved your issue."}),
        ("Ticket Reply (User)", "ticket_reply_user.html", {"title": "Ticket Reply", "name": "Test User", "ticket_id": "12345", "reply_message": "Thank you for your help!"}),
    ]

    for email_to in recipients:
        print(f"\n--- Sending all templates to {email_to} ---")
        for subject, template_name, template_body in templates:
            print(f"  Sending: {subject}...")
            try:
                EmailService._send_email_async(
                    subject=f"[Sample] {subject}",
                    email_to=email_to,
                    template_body=template_body,
                    template_name=template_name
                )
                print(f"    ✓ Sent")
            except Exception as e:
                print(f"    ✗ Failed: {e}")

if __name__ == "__main__":
    send_all_templates()
