import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name
        self.frontend_url = settings.frontend_url

    async def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = "") -> bool:
        """
        Send email using smtplib. If SMTP credentials are not configured,
        fallback to logging the email to the console for local development.
        """
        # Lowercase email normalization
        normalized_to = to_email.strip().lower()

        # Development/Fallback logging when SMTP is not configured
        if not self.smtp_host or not self.smtp_username:
            logger.info("--------- [EMAIL SERVICE DEVELOPMENT FALLBACK] ---------")
            logger.info(f"To: {normalized_to}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Text Content: {text_content or 'See HTML content'}")
            logger.info("---------------------------------------------------------")
            # Always write to stdout so the developer can see it in terminal
            print("\n=========================================================")
            print(f"   [NOTIFICATION] Email to: {normalized_to}")
            print(f"   Subject: {subject}")
            print(f"   Content:\n{text_content or html_content}")
            print("=========================================================\n", flush=True)
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = normalized_to

            if text_content:
                msg.attach(MIMEText(text_content, "plain", "utf-8"))
            if html_content:
                msg.attach(MIMEText(html_content, "html", "utf-8"))

            # Run in a synchronous context/thread pool or async friendly way
            # For simplicity in FastAPI async, we run standard smtplib
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.from_email, [normalized_to], msg.as_string())
            
            logger.info(f"Successfully sent email to {normalized_to}")
            return True
        except Exception as e:
            # Safe logging: do not log SMTP password
            logger.error(f"Failed to send email to {normalized_to}: {str(e)}")
            return False

    async def send_otp_email(self, to_email: str, name: str, otp_code: str) -> bool:
        """Send 2FA OTP code to the registered email."""
        subject = "Your 6-Digit Security Verification Code"
        text_content = f"Hello {name},\n\nYour security verification code is: {otp_code}\n\nThis code will expire in 5 minutes and is valid for a single use."
        html_content = f"""
        <html>
            <body>
                <h2>SCRB Crime Intelligence Platform</h2>
                <p>Hello <strong>{name}</strong>,</p>
                <p>A sign-in request was made for your account. Please use the following 6-digit verification code to complete your login:</p>
                <div style="font-size: 24px; font-weight: bold; letter-spacing: 4px; padding: 12px; background-color: #f1f5f9; border-radius: 6px; width: fit-content; margin: 16px 0;">
                    {otp_code}
                </div>
                <p>This code will expire in <strong>5 minutes</strong> and is valid for a single use.</p>
                <p>If you did not initiate this request, please contact the System Administrator immediately.</p>
            </body>
        </html>
        """
        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_activation_email(self, to_email: str, name: str, employee_id: str, activation_token: str) -> bool:
        """Send account creation and activation email to new user."""
        activation_url = f"{self.frontend_url}/setup-password?token={activation_token}"
        subject = "Account Created — SCRB Crime Intelligence Platform"
        text_content = (
            f"Hello {name},\n\n"
            f"Your account has been created on the SCRB Crime Intelligence Platform.\n\n"
            f"User Information:\n"
            f"- Name: {name}\n"
            f"- Employee / Police ID: {employee_id}\n"
            f"- Login Email: {to_email}\n\n"
            f"Please set your password by visiting: {activation_url}\n\n"
            f"This link is valid for 24 hours and can only be used once."
        )
        html_content = f"""
        <html>
            <body>
                <h2>SCRB Crime Intelligence Platform</h2>
                <p>Hello <strong>{name}</strong>,</p>
                <p>Your account has been successfully created. Here are your account details:</p>
                <ul>
                    <li><strong>Name:</strong> {name}</li>
                    <li><strong>Employee / Police ID:</strong> {employee_id}</li>
                    <li><strong>Login Email:</strong> {to_email}</li>
                </ul>
                <p>To set up your password and activate your account, please click the button below:</p>
                <p style="margin: 24px 0;">
                    <a href="{activation_url}" style="background-color: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: bold;">Set Your Password</a>
                </p>
                <p>Or copy and paste this URL into your browser:</p>
                <p style="color: #64748b; font-size: 13px;">{activation_url}</p>
                <p>This link is valid for <strong>24 hours</strong> and can only be used once.</p>
            </body>
        </html>
        """
        return await self.send_email(to_email, subject, html_content, text_content)
