from fastapi import Depends, HTTPException, Request, status, APIRouter
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .core import create_and_save
from .models import PetitLink, redis_client, get_db


router = APIRouter()


class CreateLinkDto(BaseModel):
    original_link: str
    short_link: str


class UpdateLinkDto(BaseModel):
    original_link: str
    short_link: str


@router.get('/short/{link_id}')
async def retrieve(link_id: int, db: Session = Depends(get_db)):
    return db.query(PetitLink).filter(PetitLink.id == link_id).first()  # type: ignore


@router.post('/short')
async def create(dto: CreateLinkDto, db: Session = Depends(get_db)):
    new_link = PetitLink(original_link=dto.original_link, short_link=dto.short_link)
    db.add(new_link)
    db.commit()
    db.refresh(new_link)


@router.patch('/short/{link_id}')
async def update(link_id: int, dto: UpdateLinkDto, db: Session = Depends(get_db)):
    link = db.query(PetitLink).filter(PetitLink.id == link_id).first()  # type: ignore
    # TODO: optional fields
    link.original_link = dto.original_link
    link.short_link = dto.short_link
    db.commit()
    db.refresh(link)


@router.delete('/short/{link_id}')
async def delete(link_id: int, db: Session = Depends(get_db)):
    link = db.query(PetitLink).filter(PetitLink.id == link_id).first()  # type: ignore
    db.delete(link)
    db.commit()


class GeneratePetitLinkDto(BaseModel):
    original_link: str


@router.get('/r/{path}')
async def redirect(path: str):
    link = redis_client.get(path)
    if link is None:
        raise HTTPException(status_code=404, detail='Link Not Found')
    else:
        return RedirectResponse(link)


@router.post('/create')
async def create_petitlink(request: Request, db: Session = Depends(get_db)):
    json_data = await request.json()

    link = json_data.get('link')

    if not link:
        return JSONResponse({'message': 'Bad Request'}, status_code=status.HTTP_400_BAD_REQUEST)

    path = create_and_save(link, db)

    return path
