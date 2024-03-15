from string import ascii_letters
from random import choice

from redis.exceptions import WatchError
from sqlalchemy.orm import Session

from .settings import settings
from .models import PetitLink, redis_client


def generate_random_string(length: int) -> str:
    """Generate a random string using [a-zA-Z0-9] with given length l."""
    return ''.join([choice(ascii_letters) for _ in range(length)])


def create_and_save(link: str, db: Session) -> str:
    path = generate_random_string(settings.petitlink_length)

    petitlink = PetitLink(original_link=link, petitlink=path)

    _save_petitlink(petitlink, db)

    return path


def _save_petitlink(petitlink: PetitLink, db: Session):
    # Save on SQL
    try:
        db.add(petitlink)
    except Exception as e:
        print(e)
    else:
        db.commit()

    # Save on Redis
    # TODO: Add a retry logic when key already exists
    success = False
    with redis_client.pipeline(transaction=True) as p:
        while True:
            try:
                # Check if path is not occupied.
                p.watch(petitlink.petitlink)
                # Put data into pipeline.
                p.multi()
                p.setnx(petitlink.petitlink, petitlink.original_link)
                # Execute the pipeline and record the success.
                success = p.execute()[0]
                break
            except WatchError:
                continue
