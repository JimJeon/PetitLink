from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

from petitlink.routes import api, auth


def create_app():
    app = FastAPI()

    app.include_router(api.router)
    app.include_router(auth.router)

    return app


templates = Jinja2Templates(directory='petitlink/templates')
