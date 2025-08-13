from HTTP import HTTPStatus
from typing import Annotated

from fastapi import Depends, HTTPException, APIRouter, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fast_zero.database import get_session
from fast_zero.fast_zero.schemas import Message, UserSchema, UserPublic, UserList, FilterPage
from fast_zero.fast_zero.security import get_password_hash, get_current_user
from fast_zero.models import User
from fast_zero.settings import Settings
from fast_zero.tests.conftest import session

router = APIRouter(prefix='/users', tags=['users'])

Session = Annotated[Session, Depends(get_session)]
Current_user = Annotated[User, Depends(get_current_user)]


@router.get('/', status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return {'message': 'Olá mundo!'}


@router.post('/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(user: UserSchema, session: Session):

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


@router.get('/', status_code=HTTPStatus.OK, response_model=UserList)
def read_users(session: Session, current_user: Current_user, filter_users: Annotated[FilterPage, Query()]):
    users = session.scalars(select(User).limit(filter_users.limit).offset(filter_users.offset))
    return {'users': users}


@router.put('/{user_id}', status_code=HTTPStatus.OK, response_model=UserPublic)
def update_user(user_id: int, user: UserSchema, session: Session, current_user: Current_user):
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


@router.delete('/{user_id}', status_code=HTTPStatus.OK, response_model=Message)
def delete_user(user_id: int, session: Session):
    user_db = session.scalar(select(User).where(User.id == user_id))
    if not user_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Usuário com id {user_id} não encontrado.'
        )
    session.delete(user_db)
    session.commit()

    return {'message': 'User deleted'}


@router.get('/{user_id}', status_code=HTTPStatus.OK, response_model=UserPublic)
def read_user_by_id(user_id: int, session: Session):
    user_db = session.scalar(select(User).where(User.id == user_id))
    if not user_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Usuário com id {user_id} não encontrado.'
        )

    return user_db