from typing import List

from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from petitlink.auth import router, templates, settings
from petitlink.auth.core import build_email_message, send_login_email, generate_access_token


class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.username: str | None = None

    async def load_data(self):
        form = await self.request.form()
        self.username = form.get('email')

    async def is_valid(self):
        if not self.username or not (self.username.__contains__('@')):
            self.errors.append('Email is required')
        if not self.errors:
            return True
        return False


@router.get('/login')
def login(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post('/login')
async def login(request: Request):
    form = LoginForm(request)
    await form.load_data()
    if await form.is_valid():
        try:
            msg = build_email_message(form.username)
            await send_login_email(form.username, msg)
            form.__dict__.update(msg='Login Email Sent')
            response = templates.TemplateResponse('auth/login.html', form.__dict__)
            return response
        except HTTPException:
            form.__dict__.update(msg='')
            return templates.TemplateResponse('auth/login.html', form.__dict__)
    return templates.TemplateResponse('auth/login.html', form.__dict__)


@router.get('/verify/{token}')
async def verify(token: str, expiration: int = 600):
    serializer = URLSafeTimedSerializer(settings.auth_secret_key)
    try:
        email = serializer.loads(token, salt=settings.auth_salt, max_age=expiration)
        token = generate_access_token(email)
        response = RedirectResponse('/index')
        response.set_cookie(
            key='token', value=token, httponly=True, samesite='strict', domain='petitlink.com')
        return response
    except BadSignature or SignatureExpired:
        return False


@router.get('/logout')
def logout(request: Request) -> None:
    msg = 'Logout Successful'
    response = templates.TemplateResponse('auth/login.html', {'request': request, 'msg': msg})
    response.delete_cookie(key='token', domain='petitlink.com')
    return response
