def delete_all_users():
    import funcy_pipe as fp

    from app.configuration.clerk import clerk

    _deleted_users = (
        clerk.users.list()
        | fp.filter(
            lambda user: user.email_addresses[0].email_address
            != "mike+clerk_test@example.com"
        )
        | fp.pluck_attr("id")
        | fp.lmap(lambda uid: clerk.users.delete(user_id=uid))
    )
