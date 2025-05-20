from fastapi import status
from fastapi.testclient import TestClient

from app.routes.admin import SESSION_KEY_LOGIN_AS_USER
from app.server import api_app

from app.models.user import User, UserRole

from tests.routes.utils import (
    decode_cookie,
    get_clerk_admin_user,
    get_clerk_dev_user,
    get_valid_token,
)


def clerk_authorization(clerk_user):
    token_id = get_valid_token(clerk_user)

    return {
        "Authorization": f"Bearer {token_id}",
    }


def test_non_admin_role(client: TestClient):
    "is a non-admin user banned?"

    _, _, clerk_user = get_clerk_dev_user()

    response = client.get(
        api_app.url_path_for("user_list"),
        headers=clerk_authorization(clerk_user),
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_user_list(client: TestClient):
    _, _, clerk_admin = get_clerk_admin_user()

    users_to_create = 3

    # create 3 users
    for i in range(users_to_create):
        User(email=f"test{i}@example.com", clerk_id=f"user_{i}").save()

    response = client.get(
        api_app.url_path_for("user_list"),
        headers=clerk_authorization(clerk_admin),
    )

    assert response.status_code == status.HTTP_200_OK

    user_state = response.json()

    assert "current_user" in user_state

    # list should contain created user
    assert len(user_state["users"]) == users_to_create
    assert user_state["users"][-1]["email"] == "test2@example.com"
    assert user_state["users"][-1]["clerk_id"] == "user_2"


def test_login_as_authorized_good_credentials(client: TestClient):
    _, _, clerk_admin = get_clerk_admin_user()
    assert clerk_admin

    _, _, clerk_user = get_clerk_dev_user()
    assert clerk_user

    # paranoid conditions to assert on the general test structure
    local_admin = User.get(clerk_id=clerk_admin.id)
    assert local_admin and local_admin.role == UserRole.admin

    # if the login_as user DNE it will throw an error
    _user = User.find_or_create_by(clerk_id=clerk_user.id)

    response = client.post(
        api_app.url_path_for("login_as_user", user_id=clerk_user.id),
        headers=clerk_authorization(clerk_admin),
    )

    assert response.status_code == status.HTTP_200_OK

    cookie = decode_cookie(response)
    assert cookie[SESSION_KEY_LOGIN_AS_USER] == clerk_user.id

    # now that we are logged in, let's attempt to clear the session by passing ourselves as the login_as user
    response = client.post(
        api_app.url_path_for("login_as_user", user_id=clerk_admin.id),
        headers=clerk_authorization(clerk_admin),
    )

    assert response.status_code == status.HTTP_200_OK
    assert decode_cookie(response)[SESSION_KEY_LOGIN_AS_USER] is None


def test_login_as_authorized_bad_credentials(client: TestClient):
    _, _, clerk_admin = get_clerk_admin_user()
    assert clerk_admin

    _, _, clerk_user = get_clerk_dev_user()
    assert clerk_user

    # if the login_as user DNE it will throw an error
    _user = User.find_or_create_by(clerk_id=clerk_user.id)

    # attempt to login_as the non-admin user into the admin user
    response = client.post(
        api_app.url_path_for("login_as_user", user_id=clerk_admin.id),
        headers=clerk_authorization(clerk_user),
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    cookie = decode_cookie(response)
    assert SESSION_KEY_LOGIN_AS_USER not in cookie


def test_login_as_reset_credentials(client: TestClient):
    "login_as with admin creds will remove cookie"

    _, _, clerk_admin = get_clerk_admin_user()
    assert clerk_admin

    _, _, clerk_user = get_clerk_dev_user()
    assert clerk_user

    # if the login_as user DNE it will throw an error
    _user = User.find_or_create_by(clerk_id=clerk_user.id)

    response = client.post(
        api_app.url_path_for("login_as_user", user_id=clerk_user.id),
        headers=clerk_authorization(clerk_admin),
    )

    assert response.status_code == status.HTTP_200_OK
    assert decode_cookie(response)[SESSION_KEY_LOGIN_AS_USER] == clerk_user.id

    # now that we are login_as, let's attempt to reset

    response = client.post(
        api_app.url_path_for("login_as_user", user_id=clerk_admin.id),
        headers=clerk_authorization(clerk_admin),
    )

    assert response.status_code == status.HTTP_200_OK
    assert decode_cookie(response)[SESSION_KEY_LOGIN_AS_USER] is None


def test_login_as_user_route(client: TestClient):
    _, _, clerk_admin = get_clerk_admin_user()
    assert clerk_admin

    _, _, clerk_user = get_clerk_dev_user()
    assert clerk_user

    # if the login_as user DNE it will throw an error
    local_user = User.find_or_create_by(clerk_id=clerk_user.id)

    response = client.post(
        api_app.url_path_for("login_as_user", user_id=clerk_user.id),
        headers=clerk_authorization(clerk_admin),
    )

    assert response.status_code == status.HTTP_200_OK

    user_response = client.get(
        api_app.url_path_for("application_data"),
        headers=clerk_authorization(clerk_admin),
    )

    assert response.status_code == status.HTTP_200_OK
    assert user_response.json()["user_id"] == str(local_user.id)


def test_normal_route_as_admin(client: TestClient):
    _, _, clerk_admin = get_clerk_admin_user()
    assert clerk_admin

    response = client.get(
        api_app.url_path_for("application_data"),
        headers=clerk_authorization(clerk_admin),
    )

    assert response.status_code == status.HTTP_200_OK
