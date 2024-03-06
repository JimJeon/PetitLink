from fastapi import Request
from fastapi.templating import Jinja2Templates

from petitlink import create_app
from petitlink.auth.routes import decode_access_token


templates = Jinja2Templates('templates')
app = create_app()


@app.get('/index')
async def index(request: Request):
    token = request.cookies.get('token')

    if token is None:
        return templates.TemplateResponse('index.html', {'request': request})

    email = decode_access_token(token)
    return templates.TemplateResponse('index.html', {'request': request, 'user_email': email})
