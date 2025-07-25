from HTTP import HTTPStatus
from fast_zero.database import get_session
from fast_zero.models import User
from fast_zero.settings import Settings
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fast_zero.fast_zero.schemas import Message, UserSchema, UserPublic, UserList
from fast_zero.fast_zero.security import get_password_hash, verify_password, create_access_token, get_current_user
from fast_zero.tests.conftest import session

app = FastAPI()

database = []
engine = create_engine(Settings().DATABASE_URL)


@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return {'message': 'Olá mundo!'}


@app.post('/users/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(user: UserSchema, session = Depends(get_session)):

    db_user = session.scalar(select(User).where(User.username == user.username | User.email == user.email))

    if db_user:
        if db_user.username == user.username or db_user.email == user.email:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail=f'Usuário com username {user.username} ou email {user.email} já existe.'
            )
    else:
        db_user = User(
            username=user.username,
            email=user.email,
            password= get_password_hash(user.password),
        )

    session.add(db_user)
    session.commit()
    return db_user


@app.get('/users/', status_code=HTTPStatus.OK, response_model=UserList)
def read_users(limit: int = 10, offset: int = 0, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    users = session.scalars(select(User).limit(limit).offset(offset))
    return {'users': users}


@app.put('/users/{user_id}', status_code=HTTPStatus.OK, response_model=UserPublic)
def update_user(user_id: int, user: UserSchema, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail=f'Sem permissões suficientes.'
        )

    try:
        current_user.email = user.email
        current_user.username = user.username
        current_user.password = get_password_hash(user.password)

        session.add(current_user)
        session.commit()
        session.refresh(current_user)

        return current_user
    except IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f'Username ou email já existe.'
        )


@app.delete('/users/{user_id}', status_code=HTTPStatus.OK, response_model=Message)
def delete_user(user_id: int, session: Session = Depends(get_session)):
    user_db = session.scalar(select(User).where(User.id == user_id))
    if not user_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Usuário com id {user_id} não encontrado.'
        )
    session.delete(user_db)
    session.commit()

    return {'message': 'User deleted'}


@app.get('/users/{user_id}', status_code=HTTPStatus.OK, response_model=UserPublic)
def read_user_by_id(user_id: int, session: Session = Depends(get_session)):
    user_db = session.scalar(select(User).where(User.id == user_id))
    if not user_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Usuário com id {user_id} não encontrado.'
        )

    return user_db


@app.post('/token')
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.scalar(select(User).where(User.email == form_data.email))

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Email ou senha inválidos.',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Senha inválida.',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    access_token = create_access_token({'sub': user.email})
    return {'access_token': access_token, 'token_type': 'Bearer'}