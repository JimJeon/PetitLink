
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from random import choice
from string import ascii_letters
from fastapi.responses import RedirectResponse
from redis.exceptions import WatchError

from petitlink.db import redis_client
from petitlink import create_app


app = create_app()


@app.get('/index')
async def index(request: Request):
    return 'hello world'


def generate_random_string(length: int):
    """Generate a random string using [a-zA-Z0-9] with given length l."""
    return ''.join([choice(ascii_letters) for _ in range(length)])


class GeneratePetitLinkDto(BaseModel):
    original_link: str


@app.post('/generate')
async def generate_petit_link(dto: GeneratePetitLinkDto):
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

