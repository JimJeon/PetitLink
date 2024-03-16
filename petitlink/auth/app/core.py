import jwt
import smtplib

from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from argon2 import PasswordHasher
from argon2.exceptions import HashingError
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .settings import settings
from .models import UserTable


def generate_access_token(email: str):
    payload = {
        'email': email,
        'exp': datetime.now() + timedelta(hours=24)
    }

    token = jwt.encode(
        payload,
        settings.auth_access_token_secret_key,
        algorithm='HS256'
    )

    return token


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.auth_access_token_secret_key, algorithms='HS256')
    except jwt.exceptions.InvalidSignatureError:
        raise HTTPException(status_code=401, detail='Invalid token')
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token expired')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error: {e}')

    return payload['email']


def register(db: Session, email: str, password: str):
    new_user = UserTable(email=email, password_hash=hash_password(password))
    db.add(new_user)
    db.commit()


def hash_password(password: str):
    ph = PasswordHasher()
    try:
        _hash = ph.hash(password)
    except HashingError:
        return ''
    except Exception as e:
        print(e)
        return ''
    return _hash
