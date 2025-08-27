from HTTP import HTTPStatus
from fast_zero.fast_zero.schemas import Message
from fast_zero.routers import users, auth
from fastapi import FastAPI

app = FastAPI()

app.include_router(users.router)
app.include_router(auth.router)


@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
async def read_root():
    return {'message': 'Olá Mundo!'}
