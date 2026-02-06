import base64
from mailjet_rest import Client
from fastapi import BackgroundTasks
from pydantic import EmailStr
from typing import Dict, Any
import logging
from pathlib import Path
import jinja2
from app.config.settings import settings

logger = logging.getLogger(__name__)

TEMPLATE_FOLDER = Path("app/templates")
if not TEMPLATE_FOLDER.exists():
    logger.error(f"Email template folder not found at: {TEMPLATE_FOLDER.resolve()}")

ASSETS_FOLDER = Path("app/assets")
if not ASSETS_FOLDER.exists():
    logger.error(f"Assets folder not found at: {ASSETS_FOLDER.resolve()}")

template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_FOLDER)
template_env = jinja2.Environment(loader=template_loader, autoescape=True)

logger.info(f"SMTP Email Service initialized. Reading templates from: {TEMPLATE_FOLDER.resolve()}")

class EmailService:
    """
    Service to send all application emails asynchronously via background tasks
    using SMTP and Jinja2 for templating.
    """

    @staticmethod
    def _render_template(template_name: str, context: Dict[str, Any]) -> str:
        """Loads and renders an HTML template using Jinja2."""
        try:
            template = template_env.get_template(template_name)
            return template.render(context)
        except jinja2.TemplateNotFound:
            logger.error(f"Template not found: {template_name}")
            return f"Error: Template {template_name} not found."
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            return f"Error rendering template: {e}"

    @staticmethod
    def _send_email_async(
            subject: str,
            email_to: EmailStr,
            template_body: Dict[str, Any],
            template_name: str
    ):
        """
        Internal helper to construct and send an email message via Mailjet API.
        """
        html_part = EmailService._render_template(template_name, template_body)

        # Basic text part fallback
        text_part = f"{subject}\n\n"
        text_part += f"This email requires an HTML-compatible client. Please view this message in a modern email client."
        if template_body.get("title"):
            text_part = f"{template_body.get('title')}\n\n(Please view in an HTML-compatible client)"

        try:
            mailjet = Client(auth=(settings.MAILJET_API_KEY, settings.MAILJET_SECRET_KEY), version='v3.1')

            # Prepare inline attachments
            inlined_attachments = []
            images = [
                ("logo.png", "logo", "image/png"),
                ("image1.jpg", "image1", "image/jpeg"),
                ("image2.png", "image2", "image/png")
            ]

            for filename, cid, content_type in images:
                file_path = ASSETS_FOLDER / filename
                if file_path.exists():
                    try:
                        with open(file_path, 'rb') as f:
                            img_data = f.read()
                            b64_content = base64.b64encode(img_data).decode('utf-8')
                            inlined_attachments.append({
                                "ContentType": content_type,
                                "Filename": filename,
                                "ContentID": cid,
                                "Base64Content": b64_content
                            })
                    except Exception as e:
                        logger.error(f"Failed to process image {filename}: {e}")
                else:
                    logger.warning(f"Image not found: {file_path}")

            # Generate unique CustomID for tracking
            import hashlib
            import time
            unique_id = hashlib.md5(f"{email_to}{time.time()}".encode()).hexdigest()[:12]
            custom_id = f"confess-{template_name.replace('.html', '')}-{unique_id}"

            message_payload = {
                "From": {
                    "Email": settings.MAIL_FROM,
                    "Name": settings.MAILJET_SENDER_NAME if hasattr(settings, 'MAILJET_SENDER_NAME') else settings.MAIL_FROM_NAME
                },
                "ReplyTo": {
                    "Email": settings.MAIL_FROM,
                    "Name": settings.MAIL_FROM_NAME
                },
                "To": [
                    {
                        "Email": email_to,
                        "Name": template_body.get("name", "User")
                    }
                ],
                "Subject": subject,
                "TextPart": text_part,
                "HTMLPart": html_part,
                "CustomID": custom_id,
                "Headers": {
                    "List-Unsubscribe": f"<mailto:unsubscribe@confess.com.ng?subject=Unsubscribe>, <https://confess.com.ng/unsubscribe>"
                }
            }

            if inlined_attachments:
                message_payload["InlinedAttachments"] = inlined_attachments

            data = {
                'Messages': [message_payload]
            }

            result = mailjet.send.create(data=data)
            logger.info(f"Mailjet response status: {result.status_code}")
            logger.info(f"Mailjet response json: {result.json()}")

            if result.status_code == 200:
                logger.info(f"Email sent successfully to {email_to} with template {template_name}")
            else:
                logger.error(f"Failed to send email via Mailjet. Status: {result.status_code}, Response: {result.json()}")

        except Exception as e:
            logger.error(f"Exception while sending email to {email_to}: {e}")

    @staticmethod
    def _add_task(
            background_tasks: BackgroundTasks,
            subject: str,
            email_to: EmailStr,
            template_body: Dict[str, Any],
            template_name: str
    ):
        """Adds the email sending function to the background task queue."""
        background_tasks.add_task(
            EmailService._send_email_async,
            subject,
            email_to,
            template_body,
            template_name
        )

    @staticmethod
    def send_user_welcome_email(
            background_tasks: BackgroundTasks,
            email_to: EmailStr,
            name: str
    ):
        """1. (User) Sent on initial user registration."""
        EmailService._add_task(
            background_tasks,
            "Welcome to CONFESS!",
            email_to,
            {"title": "Welcome to CONFESS!", "name": name},
            "user_welcome.html"
        )

    @staticmethod
    def send_waitlist_email(
            background_tasks: BackgroundTasks,
            email_to: EmailStr,
            name: str
    ):
        """(User) Sent when a user joins the waitlist."""
        EmailService._add_task(
            background_tasks,
            "You're on the Waitlist!",
            email_to,
            {"title": "You're on the Waitlist!", "name": name},
            "waitlist.html"
        )

    @staticmethod
    def send_email_verification(
            background_tasks: BackgroundTasks,
            email_to: EmailStr,
            name: str,
            verification_code: str
    ):
        """2. (User) Sent to verify a new user's email address with a 6-digit code."""
        EmailService._add_task(
            background_tasks,
            "Verify Your Email Address",
            email_to,
            {"title": "Verify Your Email", "user_name": name, "verification_code": verification_code},
            "email_verification.html"
        )

    @staticmethod
    def send_email_verified_notice(
            background_tasks: BackgroundTasks,
            email_to: EmailStr,
            name: str
    ):
        """3. (User) [NEW] Sent *after* a user successfully clicks the verification link."""
        EmailService._add_task(
            background_tasks,
            "Email Verified Successfully!",
            email_to,
            {"title": "Email Verified", "user_name": name},
            "email_verified_notice.html"
        )

    @staticmethod
    def send_password_reset_email(
            background_tasks: BackgroundTasks,
            email_to: EmailStr,
            name: str,
            reset_link: str
    ):
        """3. (User/Org) Sent when a password reset is requested."""
        EmailService._add_task(
            background_tasks,
            "Reset Your Password",
            email_to,
            {"title": "Reset Your Password", "user_name": name, "reset_link": reset_link},
            "password_reset.html"
        )

    @staticmethod
    def send_password_change_notice(
            background_tasks: BackgroundTasks,
            email_to: EmailStr,
            name: str
    ):
        """4. (User/Org) Security notice sent *after* a password has been changed."""
        EmailService._add_task(
            background_tasks,
            "Security Alert: Your Password Was Changed",
            email_to,
            {"title": "Password Changed", "user_name": name},
            "password_change_notice.html"
        )

    @staticmethod
    def send_email_change_notice(
            background_tasks: BackgroundTasks,
            email_to: EmailStr,
            name: str,
            old_email: str
    ):
        """5. (User/Org) Security notice sent to the *old* email address."""
        EmailService._add_task(
            background_tasks,
            "Security Alert: Your CONFESS Email Was Changed",
            email_to,
            {"title": "Email Changed", "user_name": name, "new_email": email_to, "old_email": old_email},
            "email_change_notice.html"
        )


    @staticmethod
    def send_purchase_success_email(
            background_tasks: BackgroundTasks,
            email_to: EmailStr,
            name: str,
            service_name: str,
            amount: float,
            transaction_ref: str,
            recipient: str
    ):
        """13. (User) Sent when a service purchase is successful."""
        EmailService._add_task(
            background_tasks,
            f"Purchase Successful: {service_name}",
            email_to,
            {
                "title": "Purchase Successful",
                "user_name": name,
                "service_name": service_name,
                "amount": f"₦{amount:,.2f}",
                "transaction_ref": transaction_ref,
                "recipient": recipient
            },
            "purchase_success.html"
        )

    @staticmethod
    def send_purchase_failed_email(
            background_tasks: BackgroundTasks,
            email_to: EmailStr,
            name: str,
            service_name: str,
            amount: float,
            transaction_ref: str,
            reason: str
    ):
        """14. (User) Sent when a service purchase fails."""
        EmailService._add_task(
            background_tasks,
            f"Purchase Failed: {service_name}",
            email_to,
            {
                "title": "Purchase Failed",
                "user_name": name,
                "service_name": service_name,
                "amount": f"₦{amount:,.2f}",
                "transaction_ref": transaction_ref,
                "reason": reason
            },
            "purchase_failed.html"
        )

    @staticmethod
    def send_refund_email(
            background_tasks: BackgroundTasks,
            email_to: EmailStr,
            name: str,
            service_name: str,
            amount: float,
            transaction_ref: str
    ):
        """15. (User) Sent when a refund is processed."""
        EmailService._add_task(
            background_tasks,
            "Refund Processed",
            email_to,
            {
                "title": "Refund Processed",
                "user_name": name,
                "service_name": service_name,
                "amount": f"₦{amount:,.2f}",
                "transaction_ref": transaction_ref
            },
            "refund_processed.html"
        )

    @staticmethod
    def send_ticket_created_email(
            background_tasks: BackgroundTasks,
            email_to: str,
            name: str,
            ticket_id: str,
            subject: str,
            message_preview: str
    ) -> None:
        """
        Send email when a new support ticket is created.
        """
        subject_line = f"Ticket Created: {subject} [#{ticket_id}]"
        EmailService._add_task(
            background_tasks=background_tasks,
            subject=subject_line,
            email_to=email_to,
            template_body={
                "name": name,
                "ticket_id": ticket_id,
                "subject": subject,
                "message_preview": message_preview,
                "project_name": settings.PROJECT_NAME,
            },
            template_name="ticket_created.html"
        )

    @staticmethod
    def send_ticket_reply_email(
            background_tasks: BackgroundTasks,
            email_to: str,
            name: str,
            ticket_id: str,
            subject: str,
            reply_message: str,
            is_admin_reply: bool = True
    ) -> None:
        """
        Send email when a ticket receives a reply.
        """
        subject_line = f"New Reply: {subject} [#{ticket_id}]"
        template = "ticket_reply_admin.html" if is_admin_reply else "ticket_reply_user.html"

        EmailService._add_task(
            background_tasks=background_tasks,
            subject=subject_line,
            email_to=email_to,
            template_body={
                "name": name,
                "ticket_id": ticket_id,
                "subject": subject,
                "reply_message": reply_message,
                "project_name": settings.PROJECT_NAME,
            },
            template_name=template
        )

    @staticmethod
    def send_confess_notification(
            background_tasks: BackgroundTasks,
            email_to: str,
            name: str,
            sender_name: str,
            message: str,
            confess_type: str,
            slug: str
    ) -> None:
        """
        Send email notification for a confession.
        """
        subject_line = f"You have a new confession from {sender_name}"

        EmailService._add_task(
            background_tasks=background_tasks,
            subject=subject_line,
            email_to=email_to,
            template_body={
                "name": name,
                "sender_name": sender_name,
                "message": message,
                "confess_type": confess_type,
                "slug": slug,
                "project_name": settings.PROJECT_NAME,
                "cta_link": f"{settings.FRONTEND_URL}/confess/{slug}",
                "cta_text": "View Confession"
            },
            template_name="confess_notification.html"
        )

    @staticmethod
    def send_confess_response_notification(
            background_tasks: BackgroundTasks,
            email_to: str,
            sender_name: str,
            recipient_name: str,
            response: bool,
            confess_type: str,
            slug: str
    ) -> None:
        """
        Send email notification for a confession response.
        """
        response_text = "Accepted" if response else "Declined"
        subject_line = f"{recipient_name} has {response_text} your confession ({confess_type})"

        EmailService._add_task(
            background_tasks=background_tasks,
            subject=subject_line,
            email_to=email_to,
            template_body={
                "name": sender_name,
                "recipient_name": recipient_name,
                "response": response_text,
                "confess_type": confess_type,
                "slug": slug,
                "project_name": settings.PROJECT_NAME,
                "is_accepted": response
            },
            template_name="confess_response_notification.html"
        )

email_service = EmailService()
