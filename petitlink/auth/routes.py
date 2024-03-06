import jwt
import smtplib

from datetime import datetime, timedelta
from typing import List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from petitlink.auth import router, templates, settings


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


def build_email_message(to: str) -> MIMEMultipart:
    msg = MIMEMultipart()

    # Add a message header
    msg['Subject'] = 'PetitLink Login'
    msg['From'] = settings.auth_email
    msg['To'] = to

    # Create a link with serialized email
    serializer = URLSafeTimedSerializer(settings.auth_secret_key)
    link = serializer.dumps(to, salt=settings.auth_salt)
    link = 'http://local.petitlink.com:8000/verify/' + link

    # Add a message body
    msg.attach(MIMEText(f'''
        <a href="{link}">Login</a>
        ''', 'html'))

    return msg


async def send_login_email(to: str, msg: MIMEMultipart) -> None:
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()  # TLS support for security
        server.login(settings.auth_email, settings.auth_email_password)
        server.sendmail(settings.auth_email, to, msg.as_string())
        print('email sent successfully')


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


def generate_access_token(email: str):
    payload = {
        'email': email,
        'exp': datetime.now() + timedelta(hours=24)
    }

    token = jwt.encode(
        payload,
        settings.auth_access_token_secret_key,
        algorithm='HS256'
    )

    return token


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, settings.auth_access_token_secret_key, algorithms='HS256')
    except jwt.exceptions.InvalidSignatureError:
        return HTTPException(status_code=401, detail='Invalid token')
    except jwt.ExpiredSignatureError:
        return HTTPException(status_code=401, detail='Token expired')
    except Exception as e:
        return HTTPException(status_code=500, detail=f'Error: {e}')

    return payload['email']
