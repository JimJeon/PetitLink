import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from itsdangerous import URLSafeTimedSerializer

from .settings import settings


def build_email_message(to: str) -> MIMEMultipart:
    msg = MIMEMultipart()

    # Add a message header
    msg['Subject'] = 'PetitLink Login'
    msg['From'] = settings.petitlink_email
    msg['To'] = to

    # Create a link with serialized email
    serializer = URLSafeTimedSerializer(settings.petitlink_email_secret_key)
    link = serializer.dumps(to, salt=settings.petitlink_email_salt)
    link = 'http://petitlink.com:8000/login/' + link

    # Add a message body
    msg.attach(MIMEText(f'''
        <a href="{link}">Login</a>
        ''', 'html'))

    return msg


async def send_login_email(to: str, msg: MIMEMultipart) -> None:
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()  # TLS support for security
        server.login(settings.petitlink_email, settings.petitlink_email_pass)
        server.sendmail(settings.petitlink_email, to, msg.as_string())
        print('email sent successfully')
