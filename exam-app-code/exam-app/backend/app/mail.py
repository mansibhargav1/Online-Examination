"""Outbound email.

Sending is best-effort by design: if the mail server is misconfigured or down,
the caller still succeeds and the admin falls back to reading credentials off
the console. A broken SMTP box must never block account creation.
"""

import smtplib
import ssl
from email.message import EmailMessage

from app.config import settings


def _plain_body(full_name: str, email: str, password: str, code: str, url: str) -> str:
    return f"""Hello {full_name},

Your examination account is ready.

  Portal:             {url}
  Email:              {email}
  Password:           {password}
  Verification code:  {code}

You need both the password and the verification code to sit the exam. The code
is asked for after you sign in, on the verification screen.

Keep this message private. Anyone holding these details can sit the exam as you.

Good luck.
"""


def _html_body(full_name: str, email: str, password: str, code: str, url: str) -> str:
    return f"""<!doctype html>
<html>
  <body style="margin:0;padding:24px;background:#f7f8fa;font-family:-apple-system,Segoe UI,Roboto,sans-serif;color:#10151c;">
    <div style="max-width:520px;margin:0 auto;background:#fff;border:1px solid #dbe1e8;border-radius:4px;padding:32px;">
      <p style="margin:0 0 4px;font-size:11px;letter-spacing:0.12em;text-transform:uppercase;color:#64748b;font-family:monospace;">
        Examination portal
      </p>
      <h1 style="margin:0 0 18px;font-size:22px;font-weight:600;">Your account is ready</h1>

      <p style="margin:0 0 20px;font-size:15px;line-height:1.6;color:#38424f;">
        Hello {full_name}, an administrator has approved your application.
        You'll need both the password and the verification code below.
      </p>

      <table style="width:100%;border-collapse:collapse;font-family:monospace;font-size:14px;
                    background:#f7f8fa;border:1px solid #dbe1e8;border-radius:4px;">
        <tr>
          <td style="padding:12px 14px;color:#64748b;width:44%;">Email</td>
          <td style="padding:12px 14px;font-weight:600;">{email}</td>
        </tr>
        <tr>
          <td style="padding:12px 14px;color:#64748b;border-top:1px solid #dbe1e8;">Password</td>
          <td style="padding:12px 14px;font-weight:600;border-top:1px solid #dbe1e8;">{password}</td>
        </tr>
        <tr>
          <td style="padding:12px 14px;color:#64748b;border-top:1px solid #dbe1e8;">Verification code</td>
          <td style="padding:12px 14px;font-weight:600;letter-spacing:0.2em;border-top:1px solid #dbe1e8;">{code}</td>
        </tr>
      </table>

      <p style="margin:22px 0;">
        <a href="{url}" style="display:inline-block;background:#1d4ed8;color:#fff;text-decoration:none;
                               padding:11px 20px;border-radius:4px;font-size:14px;font-weight:500;">
          Sign in to the portal
        </a>
      </p>

      <p style="margin:0;font-size:13px;line-height:1.6;color:#64748b;border-top:1px solid #dbe1e8;padding-top:16px;">
        Keep this message private — anyone holding these details can sit the exam as you.
        The verification code is asked for after you sign in.
      </p>
    </div>
  </body>
</html>
"""


def send_credentials(full_name: str, email: str, password: str, code: str) -> tuple[bool, str]:
    """Email a new candidate their credentials.

    Returns (sent, detail). Never raises — callers depend on that.
    """
    if not settings.MAIL_ENABLED:
        return False, "Email is switched off (MAIL_ENABLED=false)."
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        return False, "SMTP is not configured."

    msg = EmailMessage()
    msg["Subject"] = "Your examination account"
    msg["From"] = settings.MAIL_FROM or settings.SMTP_USER
    msg["To"] = email
    msg.set_content(_plain_body(full_name, email, password, code, settings.PORTAL_URL))
    msg.add_alternative(_html_body(full_name, email, password, code, settings.PORTAL_URL), subtype="html")

    try:
        ctx = ssl.create_default_context()
        if settings.SMTP_PORT == 465:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=ctx, timeout=15) as s:
                s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                s.send_message(msg)
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as s:
                s.ehlo()
                if settings.SMTP_STARTTLS:
                    s.starttls(context=ctx)
                    s.ehlo()
                s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                s.send_message(msg)
        print(f"[mail] credentials sent to {email}")
        return True, "Email sent."

    except smtplib.SMTPAuthenticationError:
        detail = "SMTP rejected the login. For Gmail, use a 16-character App Password, not your account password."
    except smtplib.SMTPRecipientsRefused:
        detail = f"The mail server refused the address {email}."
    except (smtplib.SMTPException, OSError, ssl.SSLError) as e:
        detail = f"Mail server error: {type(e).__name__}: {e}"

    print(f"[mail] FAILED for {email} — {detail}")
    return False, detail
