from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from random import choice
from string import ascii_letters
from fastapi.responses import RedirectResponse
from redis.exceptions import WatchError

from db import SessionLocal, PetitLink, redis_client


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
async def index():
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

