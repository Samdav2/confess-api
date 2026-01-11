import sys
import os
from pathlib import Path

# Add app to path
sys.path.append(os.getcwd())

from app.dependencies.email_service import EmailService

def verify_templates():
    output_dir = Path("verification_output")
    output_dir.mkdir(exist_ok=True)

    test_cases = [
        ("user_welcome.html", {"title": "Welcome", "name": "John Doe"}),
        ("email_verification.html", {"title": "Verify Email", "user_name": "John Doe", "verification_link": "http://example.com/verify"}),
        ("email_verified_notice.html", {"title": "Email Verified", "user_name": "John Doe"}),
        ("password_reset.html", {"title": "Reset Password", "user_name": "John Doe", "reset_link": "http://example.com/reset"}),
        ("password_change_notice.html", {"title": "Password Changed", "user_name": "John Doe"}),
        ("email_change_notice.html", {"title": "Email Changed", "user_name": "John Doe", "old_email": "old@example.com", "new_email": "new@example.com"}),
        ("purchase_success.html", {"title": "Purchase Success", "user_name": "John Doe", "service_name": "Data Plan", "amount": "₦1,000", "transaction_ref": "REF123", "recipient": "08012345678"}),
        ("purchase_failed.html", {"title": "Purchase Failed", "user_name": "John Doe", "service_name": "Data Plan", "amount": "₦1,000", "transaction_ref": "REF123", "reason": "Insufficient Funds"}),
        ("refund_processed.html", {"title": "Refund Processed", "user_name": "John Doe", "service_name": "Data Plan", "amount": "₦1,000", "transaction_ref": "REF123"}),
        ("ticket_created.html", {"title": "Ticket Created", "name": "John Doe", "ticket_id": "12345", "subject": "Issue with payment", "message_preview": "I cannot pay..."}),
        ("ticket_reply_admin.html", {"title": "Admin Reply", "name": "John Doe", "ticket_id": "12345", "reply_message": "We fixed it.", "site_url": "http://example.com"}),
        ("ticket_reply_user.html", {"title": "User Reply", "name": "John Doe", "ticket_id": "12345", "reply_message": "Thanks!"}),
    ]

    for template_name, context in test_cases:
        print(f"Rendering {template_name}...")
        try:
            output = EmailService._render_template(template_name, context)
            if "Error" in output and len(output) < 100:
                 print(f"FAILED: {output}")
            else:
                with open(output_dir / template_name, "w") as f:
                    f.write(output)
                print(f"SUCCESS: Saved to {output_dir / template_name}")
        except Exception as e:
            print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    verify_templates()
