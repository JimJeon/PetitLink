from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db import SessionLocal, PetitLink


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
