from app.emailer import mail


def test_mailer():
    result = mail(
        template_path="mail/notification.md",
        context={
            "name": "John Doe",
        },
        subject="Hello!",
        to="example@example.com",
    )
