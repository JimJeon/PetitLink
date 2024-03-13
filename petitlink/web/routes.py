import httpx
from fastapi import Request, APIRouter
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from settings import settings
from forms import LoginForm, RegisterForm


templates = Jinja2Templates('templates')
router = APIRouter()


@router.get('/login')
async def login_get_view(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})


@router.post('/login')
async def login_post_view(request: Request):
    form = LoginForm(request)
    await form.load_data()
    if await form.is_valid():
        async with httpx.AsyncClient() as client:
            response = await client.post('http://auth.petitlink.com/login', json={'email': form.email, 'password': form.password})

        # Access Granted
        if response.status_code == 200:
            token = response.json().get('token')
            return RedirectResponse('http://petitlink.com/index/').set_cookie(
                key='token', value=token, httponly=True, secure=True)
        # Access Denied
        else:
            return templates.TemplateResponse('login.html', form.__dict__)
    return templates.TemplateResponse('auth/login.html', form.__dict__)


@router.get('/register/{token}')
async def register_get_handler(request: Request, token: str, expiration: int = 1200):
    serializer = URLSafeTimedSerializer(settings.email_secret_key)
    try:
        email = serializer.loads(token, salt=settings.email_salt, max_age=expiration)
    except BadSignature or SignatureExpired:
        return False
    return templates.TemplateResponse('register.html', {'request': request})


@router.post('/register/{token}')
async def register_post_handler(request: Request, token: str, expiration: int = 1200):
    serializer = URLSafeTimedSerializer(settings.email_secret_key)
    try:
        email = serializer.loads(token, salt=settings.email_salt, max_age=expiration)
    except BadSignature or SignatureExpired:
        return False

    form = RegisterForm(request)
    await form.load_data()

    if await form.is_valid():
        # Send request to api
        return True
    return templates.TemplateResponse('register.html', form.__dict__)
