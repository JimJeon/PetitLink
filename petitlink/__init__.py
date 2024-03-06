from fastapi import FastAPI

from petitlink import api, auth


def create_app():
    app = FastAPI()

    app.include_router(api.router)
    app.include_router(auth.router)

    return app


