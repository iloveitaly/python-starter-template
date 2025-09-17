import pytest

from app.configuration.emailer import mail


@pytest.mark.asyncio(loop_scope="function")
def test_mailer():
    _result = mail(
        template_path="mail/notification.md",
        context={
            "name": "John Doe",
        },
        subject="Hello!",
        to="example@example.com",
    )
