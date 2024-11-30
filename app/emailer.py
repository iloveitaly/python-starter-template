"""
Simple email interface:

* Create plain text emails from markdown
* Use a consistent template for HTML and insert md => html converted emails
* Inline CSS
* Single entrypoint to allow for mutation or metrics in the future

"""

import asyncio
from typing import TypedDict

import markdown2
from decouple import config
from mailers import Email, Mailer
from mailers.preprocessors.cssliner import css_inliner
from mailers.preprocessors.remove_html_comments import remove_html_comments

from .templates import render_template

SMTP_URL = config("SMTP_URL", cast=str)
EMAIL_FROM_ADDRESS = config("EMAIL_FROM_ADDRESS", cast=str)

mailer = Mailer(
    SMTP_URL,
    from_address=EMAIL_FROM_ADDRESS,
    preprocessors=[
        css_inliner,
        remove_html_comments,
    ],
)


def render_email(template_path: str, context: dict) -> tuple[str, str]:
    """
    Renders an email template into HTML and plaintext versions
    Returns tuple of (html_content, plaintext_content)
    """

    # First render the markdown template with variables
    markdown_content = render_template(template_path, context)

    # Convert markdown to HTML for rich email clients
    html_content = markdown2.markdown(markdown_content)

    # Use the raw markdown as plaintext version
    plaintext_content = markdown_content

    return html_content, plaintext_content


class TemplateParams(TypedDict, total=False):
    premailer: str | None
    content: str | None
    subject: str | None


def mail(
    to: str,
    subject: str,
    template_path: str,
    context: dict = {},
    from_address: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
):
    if "subject" not in context:
        context["subject"] = subject

    html_content, plain_content = render_email(template_path, context)

    message = Email(
        to=to,
        from_address=from_address,
        subject=subject,
        cc=cc,
        bcc=bcc,
        text=plain_content,
        html=html_content,
    )

    # Get current event loop if one exists, otherwise create new one
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(mailer.send(message))
