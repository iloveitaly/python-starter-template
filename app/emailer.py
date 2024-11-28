"""
Simple email interface:

* Create plain text emails from markdown
* Use a consistent template for HTML and insert md => html converted emails
* Inline CSS
* Single entrypoint to allow for mutation or metrics in the future

"""

import re
from typing import TypedDict

import markdown2
from decouple import config
from mailers import Email, Mailer

from .templates import render_template

SMTP_URL = config("SMTP_URL", cast=str)
mailer = Mailer(SMTP_URL)

EMAIL_FROM_ADDRESS = config("EMAIL_FROM_ADDRESS", cast=str)


def render_email(template_path: str, context: dict) -> tuple[str, str]:
    """
    Renders an email template into HTML and plaintext versions
    Returns tuple of (html_content, plaintext_content)
    """

    # First render the markdown template with variables
    markdown_content = render_template(template_path, context)

    # Convert markdown to HTML for rich email clients
    html_content = markdown2.markdown(markdown_content)

    # https://stackoverflow.com/questions/28208186/how-to-remove-html-comments-using-regex-in-python
    html_content_comments_removed = re.sub(
        "(<!--.*?-->)", "", html_content, flags=re.DOTALL
    )

    # Use the raw markdown as plaintext version
    plaintext_content = markdown_content

    return html_content_comments_removed, plaintext_content


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

    if not from_address:
        from_address = EMAIL_FROM_ADDRESS

    message = Email(
        to=to,
        from_address=from_address,
        subject=subject,
        cc=cc,
        bcc=bcc,
        text=plain_content,
        html=html_content,
    )

    # TODO https://github.com/alex-oleshkevich/mailers/issues/14
    import asyncio

    return asyncio.run(mailer.send(message))
