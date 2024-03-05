from datetime import datetime, timedelta
import jwt
import smtplib
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from random import choice
from string import ascii_letters
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from redis.exceptions import WatchError
from pydantic_settings import BaseSettings

from db import SessionLocal, PetitLink, redis_client


class AuthSettings(BaseSettings):
    auth_email: str
    auth_email_password: str
    auth_secret_key: str
    auth_salt: str
    auth_access_token_secret_key: str


settings = AuthSettings()
templates = Jinja2Templates(directory="templates")
app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CreateLinkDto(BaseModel):
    original_link: str
    short_link: str


class UpdateLinkDto(BaseModel):
    original_link: str
    short_link: str


@app.get('/index')
async def index(request: Request):
    return 'hello world'


@app.get('/short/{link_id}')
async def retrieve(link_id: int, db: Session = Depends(get_db)):
    return db.query(PetitLink).filter(PetitLink.id == link_id).first()  # type: ignore


@app.post('/short')
async def create(dto: CreateLinkDto, db: Session = Depends(get_db)):
    new_link = PetitLink(original_link=dto.original_link, short_link=dto.short_link)
    db.add(new_link)
    db.commit()
    db.refresh(new_link)


@app.patch('/short/{link_id}')
async def update(link_id: int, dto: UpdateLinkDto, db: Session = Depends(get_db)):
    link = db.query(PetitLink).filter(PetitLink.id == link_id).first()  # type: ignore
    # TODO: optional fields
    link.original_link = dto.original_link
    link.short_link = dto.short_link
    db.commit()
    db.refresh(link)


@app.delete('/short/{link_id}')
async def delete(link_id: int, db: Session = Depends(get_db)):
    link = db.query(PetitLink).filter(PetitLink.id == link_id).first()  # type: ignore
    db.delete(link)
    db.commit()


def generate_random_string(length: int):
    """Generate a random string using [a-zA-Z0-9] with given length l."""
    return ''.join([choice(ascii_letters) for _ in range(length)])


class GeneratePetitLinkDto(BaseModel):
    original_link: str


@app.post('/generate')
async def generate_petit_link(dto: GeneratePetitLinkDto, db: Session = Depends(get_db)):
    path = generate_random_string(5)

    # TODO: Add a retry logic when key already exists
    success = False
    with redis_client.pipeline(transaction=True) as p:
        while True:
            try:
                # Check if path is not occupied.
                p.watch(path)
                # Put data into pipeline.
                p.multi()
                p.setnx(path, dto.original_link)
                # Execute the pipeline and record the success.
                success = p.execute()[0]
                break
            except WatchError:
                continue

    if success:
        return path
    else:
        raise HTTPException(status_code=500, detail='Something went wrong')


@app.get('/r/{path}')
async def redirect(path: str):
    link = redis_client.get(path)
    if link is None:
        raise HTTPException(status_code=404, detail='Link Not Found')
    else:
        return RedirectResponse(link)


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


@app.get('/login')
def login(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@app.post('/login')
async def login(request: Request, db: Session = Depends(get_db)):
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


@app.get('/verify/{token}')
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
    ).encode('utf-8')

    return token
