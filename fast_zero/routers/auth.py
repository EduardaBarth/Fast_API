from typing import Annotated

from HTTP import HTTPStatus
from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fast_zero.database import get_session
from fast_zero.fast_zero.schemas import Token
from fast_zero.fast_zero.security import verify_password, create_access_token
from fast_zero.models import User
from fast_zero.security import (
    create_access_token,
    get_current_user,
    verify_password,
)
from fast_zero.settings import Settings
from fast_zero.tests.conftest import session

router = APIRouter(prefix='/auth', tags=['auth'])

Session = Annotated[AsyncSession, Depends(get_session)]
OAuth2Form = Annotated[OAuth2PasswordRequestForm, Depends()]

database = []
engine = create_engine(Settings().DATABASE_URL)
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post('/token', response_model=Token)
async def login_for_access_token(form_data: OAuth2Form, session: Session):
    user = await session.scalar(select(User).where(User.email == form_data.email))

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


@router.post('/refresh_token', response_model=Token)
async def refresh_access_token(user: CurrentUser):
    new_access_token = create_access_token(data={'sub': user.email})

    return {'access_token': new_access_token, 'token_type': 'bearer'}
