from HTTP import HTTPStatus
from typing import Annotated

from fast_zero.database import get_session
from fast_zero.models import User
from fast_zero.settings import Settings
from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fast_zero.fast_zero.security import verify_password, create_access_token
from fast_zero.tests.conftest import session

router = APIRouter(prefix='/auth', tags=['auth'])

Session = Annotated[Session, Depends(get_session)]
OAuth2Form = Annotated[OAuth2PasswordRequestForm, Depends()]

database = []
engine = create_engine(Settings().DATABASE_URL)


@router.post('/token')
def login_for_access_token(form_data: OAuth2Form, session: Session):
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