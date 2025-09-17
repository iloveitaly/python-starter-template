"""
Simple email interface:

* Create plain text emails from markdown
* Use a consistent template for HTML and insert md => html converted emails
* Inline CSS
* Single entrypoint to allow for mutation or metrics in the future

"""

import asyncio

import markdown2
from decouple import config
from mailers import Email, Mailer
from mailers.preprocessors.cssliner import css_inliner
from mailers.preprocessors.remove_html_comments import remove_html_comments

from ..templates import render_template

_mailer: Mailer | None = None


def configure_mailer():
    SMTP_URL = config("SMTP_URL", cast=str)
    EMAIL_FROM_ADDRESS = config("EMAIL_FROM_ADDRESS", cast=str)

    global _mailer

    _mailer = Mailer(
        SMTP_URL,
        from_address=EMAIL_FROM_ADDRESS,
        preprocessors=[
            css_inliner,
            remove_html_comments,
        ],
    )


def render_email(
    template_path: str, context: dict, layout_path: str = "mail/layout.html"
) -> tuple[str, str]:
    """
    Renders an email template into HTML and plaintext versions
    Returns tuple of (html_content, plaintext_content)
    """

    # First render the markdown template with variables
    markdown_content = render_template(template_path, context)

    # Use the raw markdown as plaintext version
    plaintext_content = markdown_content

    # Convert markdown to HTML for rich email clients
    html_content = markdown2.markdown(markdown_content)

    # Now render the entire html layout, with the markdown => html content inserted
    html_content = render_template(layout_path, context | {"content": html_content})

    return html_content, plaintext_content


def mail(
    to: str,
    subject: str,
    template_path: str,
    context: dict = {},
    from_address: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
):
    assert _mailer

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

    # If we're already inside a running loop, schedule the send as a task and return it.
    # Otherwise, run the coroutine to completion in a fresh loop.
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_mailer.send(message))
    else:
        return asyncio.create_task(_mailer.send(message))
