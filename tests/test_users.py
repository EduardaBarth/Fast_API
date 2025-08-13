from http import HTTPStatus
from fast_zero.fast_zero.schemas import UserPublic


def test_create_user(client):
    response = client.post(
        '/users/',
        json={'username': 'Alice', 'password': 'secret', 'email': 'alice@example.com'}
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'username': 'Alice',
        'email': 'alice@example.com',
        'id': 1
    }


def test_create_user_error_409_username(client, user):
    response = client.post(
        '/users/',
        json={
            'username': user.username,
            'email': 'alice@example.com',
            'password': 'secret',
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': f'Usuário com username {user.username} ou email alice@example.com já existe.'}

def test_create_user_error_409_email(client, user):
    response = client.post(
        '/users/',
        json={
            'username': 'alice',
            'email': user.email,
            'password': 'secret',
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': f'Usuário com username alice ou email {user.email} já existe.'}

def test_read_users(client):
    response = client.get('/users/')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'users': []
    }


def test_read_users_with_users(client, user, token):
    user_schema = UserPublic.model_validate(user).model_dump()
    response = client.get(
        '/users/',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.json() == {'users': [user_schema]}


def test_update_user(client, user, token):
    response = client.put(
        '/users/1',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'username': 'Bob',
            'email': 'bob@example.com',
            'password': 'secret'
        }
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': user.id,
        'username': 'Bob',
        'email': 'bob@example.com',
    }


def test_update_user_id_not_found(client):
    response = client.put(
        '/users/999',
        json={
            'username': 'Bob',
            'email': 'bob@example.com',
            'password': 'newsecret',
        },
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {
        'detail': 'Usuário com id 999 não encontrado.'
    }


def test_update_integrity_error(client, user):
    client.post(
        '/users',
        json={
            'username': 'fausto',
            'email': 'fausto@example.com',
            'password': 'secret',
        },
    )

    response = client.put(
        f'/users/{user.id}',
        json={
            'username': 'fausto',
            'email': 'bob@example.com',
            'password': 'mynewpassword',
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Username ou email já existe.'}


def test_delete_user(client, user, token):
    response = client.delete(
        f'/users/{user.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'User deleted'}


def test_delete_user_id_not_found(client):
    response = client.delete('/users/999')

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {
        'detail': 'Usuário com id 999 não encontrado.'
    }


def test_read_user_by_id(client, user):
    response = client.get(f'/users/{user.id}')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': user.id,
        'username': user.username,
        'email': user.email,
    }


def test_read_user_by_id_not_found(client):
    response = client.get('/users/999')

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {
        'detail': 'Usuário com id 999 não encontrado.'
    }