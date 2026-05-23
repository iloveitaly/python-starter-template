from app.configuration.emailer import EMAIL_FROM_ADDRESS, mail


def test_mailer(mailpit):
    to = "example@example.com"
    subject = "Hello!"
    name = "John Doe"

    mail(
        template_path="mail/notification.md",
        context={"name": name},
        subject=subject,
        to=to,
    )

    message = mailpit.only_last_message()

    assert message["Subject"] == subject
    assert message["From"]["Address"] == EMAIL_FROM_ADDRESS
    assert [recipient["Address"] for recipient in message["To"]] == [to]
    assert name in message["Text"]
    assert name in message["HTML"]
