from http import HTTPStatus
from fast_zero.fast_zero.schemas import UserPublic

def test_get_token(client, user):
    response = client.post(
        '/auth/token',
        data={'username': user.email,
              'password': user.clear_password}
    )
    token = response.json()

    assert response.status_code == HTTPStatus.OK
    assert token['token_type'] == 'Bearer'
    assert 'access_token' in token