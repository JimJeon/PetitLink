from fastapi import Request

from petitlink import create_app


app = create_app()


@app.get('/index')
async def index(request: Request):
    return 'hello world'

