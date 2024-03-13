from typing import List

from fastapi import Request, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import app, templates
from models import UserTable, get_db
from core import (
    generate_access_token, register
)


@app.post('/login')
async def login_post_handler(request: Request, db: Session = Depends(get_db)):
    user_data = await request.json()
    email = user_data['email']
    password = user_data['password']

    user = UserTable.find_user_by_email(db, email)

    if user.verify_password(password):
        token = generate_access_token(email)
        return JSONResponse(status_code=status.HTTP_200_OK, content={'token': token})  # Access Granted
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED, content={'message': 'Wrong password'})  # Access Denied


@app.post('/register')
async def register_post_handler(request: Request, db: Session = Depends(get_db)):
    user_data = await request.json()
    email = user_data['email']
    password = user_data['password']
    register(db, email, password)


@app.get('/logout')
def logout(request: Request) -> None:
    msg = 'Logout Successful'
    response = templates.TemplateResponse('auth/login.html', {'request': request, 'msg': msg})
    response.delete_cookie(key='token', domain='petitlink.com')
    return response
