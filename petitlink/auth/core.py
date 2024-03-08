import jwt
import smtplib

from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import HTTPException
from itsdangerous import URLSafeTimedSerializer

from petitlink.auth import settings


def build_email_message(to: str) -> MIMEMultipart:
    msg = MIMEMultipart()

    # Add a message header
    msg['Subject'] = 'PetitLink Login'
    msg['From'] = settings.auth_email
    msg['To'] = to

    # Create a link with serialized email
    serializer = URLSafeTimedSerializer(settings.auth_secret_key)
    link = serializer.dumps(to, salt=settings.auth_salt)
    link = 'http://local.petitlink.com:8000/verify/' + link

    # Add a message body
    msg.attach(MIMEText(f'''
        <a href="{link}">Login</a>
        ''', 'html'))

    return msg


async def send_login_email(to: str, msg: MIMEMultipart) -> None:
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()  # TLS support for security
        server.login(settings.auth_email, settings.auth_email_password)
        server.sendmail(settings.auth_email, to, msg.as_string())
        print('email sent successfully')


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
