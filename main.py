from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db import SessionLocal, ShortUrl


app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CreateUrlDto(BaseModel):
    original_url: str
    short_url: str


@app.get('/index')
async def index():
    return 'hello world'


@app.get('/short/{url_id}')
async def retrieve(url_id: int, db: Session = Depends(get_db)):
    return db.query(ShortUrl).filter(ShortUrl.id == url_id).first()  # type: ignore


@app.post('/short')
async def create(dto: CreateUrlDto, db: Session = Depends(get_db)):
    new_url = ShortUrl(original_url=dto.original_url, short_url=dto.short_url)
    db.add(new_url)
    db.commit()
    db.refresh(new_url)


@app.patch('/short')
async def update():
    ...


@app.delete('/short')
async def delete():
    ...
