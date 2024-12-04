from app.configuration.clerk import clerk


def get_clerk_dev_user():
    """
    Get or generate a common dev user to login via clerk
    """

    dev_user_email = "user+clerk_test@example.com"
    password = "clerk-development-123"
    user_list = clerk.users.list(email_address=[dev_user_email])

    assert user_list is not None

    if len(user_list) == 1:
        user = user_list[0]
    else:
        user = clerk.users.create(
            request={
                "email_address": [dev_user_email],
                "password": password,
            }
        )

    assert user

    return dev_user_email, password, user
