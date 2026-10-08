import base64
import gc
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import httpx

from app.config import settings
from app.services.tokens import generate_unsubscribe_token

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
GMAIL_UPLOAD_SEND_URL = "https://gmail.googleapis.com/upload/gmail/v1/users/me/messages/send?uploadType=media"


def _get_access_token() -> str:
    response = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": settings.gmail_client_id,
            "client_secret": settings.gmail_client_secret,
            "refresh_token": settings.gmail_refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def _build_attachment_parts(attachments: list = None) -> list:
    """Decode and encode each attachment once, so every recipient reuses the same parts."""
    parts = []
    for att in (attachments or []):
        content_type = att["content_type"]
        main_type, sub_type = content_type.split("/", 1) if "/" in content_type else ("application", "octet-stream")
        part = MIMEBase(main_type, sub_type)
        part.set_payload(base64.b64decode(att["data_base64"]))
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{att["filename"]}"')
        parts.append(part)
        att["data_base64"] = ""  # free the large base64 string
    return parts


def send_newsletter_email(to_email: str, subject: str, html_content: str, attachments: list = None,
                          attachment_parts: list = None, access_token: str = None) -> bool:
    unsubscribe_token = generate_unsubscribe_token(to_email)
    unsubscribe_link = f"http://localhost:8000/members/unsubscribe?token={unsubscribe_token}"

    full_html = (
        f"{html_content}"
        f"<hr>"
        f'<p style="font-size: 12px; color: #888;">'
        f'You\'re receiving this because you\'re a member of the Cybersecurity & AI Club at York College. '
        f'<a href="{unsubscribe_link}">Unsubscribe</a></p>'
    )

    message = MIMEMultipart("mixed")
    message["Subject"] = subject
    message["From"] = settings.gmail_address
    message["To"] = to_email

    body = MIMEMultipart("alternative")
    body.attach(MIMEText(full_html, "html"))
    message.attach(body)

    if attachment_parts is None:
        attachment_parts = _build_attachment_parts(attachments)
    for part in attachment_parts:
        message.attach(part)

    try:
        raw_bytes = message.as_bytes()
        del message
        token = access_token or _get_access_token()
        # Raw upload avoids the extra base64 + JSON copies of the whole message in memory.
        response = httpx.post(
            GMAIL_UPLOAD_SEND_URL,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "message/rfc822"},
            content=raw_bytes,
            timeout=60,
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Failed to send to {to_email}: {e}")
        return False
    finally:
        gc.collect()


def send_newsletter_to_members(member_emails: list, subject: str, html_content: str, attachments: list = None) -> dict:
    sent = 0
    failed = 0

    attachment_parts = _build_attachment_parts(attachments)
    gc.collect()

    access_token = None
    token_time = 0.0
    for email in member_emails:
        # Gmail access tokens last about an hour; refresh every 30 minutes.
        if access_token is None or time.time() - token_time > 1800:
            try:
                access_token = _get_access_token()
                token_time = time.time()
            except Exception as e:
                print(f"Failed to get Gmail access token: {e}")
                failed += len(member_emails) - sent - failed
                break
        success = send_newsletter_email(
            email, subject, html_content,
            attachment_parts=attachment_parts, access_token=access_token,
        )
        if success:
            sent += 1
        else:
            failed += 1

    return {"sent": sent, "failed": failed}
