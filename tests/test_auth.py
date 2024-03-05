import pytest

from main import send_login_email, AuthSettings
from email.mime.multipart import MIMEMultipart


class TestSendLoginEmail:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        'patch_settings',
        [
            {'auth_email': 'from@test.com', 'auth_email_password': 'auth-email-password'},
        ],
        indirect=True
    )
    async def test_send_login_email(self, mocker, patch_settings: AuthSettings):
        # Arrange
        mock_smtp = mocker.MagicMock(name='main.smtplib.SMTP')
        mocker.patch('main.smtplib.SMTP', new=mock_smtp)
        msg = MIMEMultipart()

        # Act
        await send_login_email('to@test.com', msg)

        # Assert
        mock_smtp.return_value.__enter__.return_value.starttls.assert_called_once()
        mock_smtp.return_value.__enter__.return_value.login.assert_called_once()
        mock_smtp.return_value.__enter__.return_value.sendmail.assert_called_once()

        mock_smtp.assert_called_with('smtp.gmail.com', 587)
        mock_smtp.return_value.__enter__.return_value.login.assert_called_with('from@test.com', 'auth-email-password')
        mock_smtp.return_value.__enter__.return_value.sendmail.assert_called_with('from@test.com', 'to@test.com', msg.as_string())


