import pytest

from collections.abc import Iterator
from email.mime.multipart import MIMEMultipart

from pytest import FixtureRequest
from pydantic_core import PydanticUndefinedType
from pydantic_settings import BaseSettings

from petitlink.auth import Settings, settings
from petitlink.auth.core import send_login_email, build_email_message


# Patching pydantic settings for pytest
# https://rednafi.com/python/patch_pydantic_settings_in_pytest/
@pytest.fixture
def patch_settings(request: FixtureRequest) -> Iterator[BaseSettings]:
    # Make a copy of an original settings
    original_settings = settings.model_copy()

    # Get the env variables to patch
    env_vars_to_patch = getattr(request, 'param', {})

    # Patch the settings to use the default values
    for k, v in settings.model_fields.items():
        if not isinstance(v.default, PydanticUndefinedType):
            setattr(settings, k, v.default)

    # Patch the settings with the parametrized env vars
    for k, v in env_vars_to_patch.items():
        # Raise an error if the env var is not defined in the settings
        if not hasattr(settings, k):
            raise ValueError(f'Unknown setting: {k}')

        # Raise an error if the env var has an invalid type
        expected_type = getattr(settings, k).__class__
        if not isinstance(v, expected_type):
            raise ValueError(
                f'Invalid type for {k}: {v.__class__} instead '
                f'of {expected_type}'
            )
        setattr(settings, k, v)

    yield settings

    # Restore the original settings
    settings.__dict__.update(original_settings.__dict__)


class TestBuildEmailMessage:
    @pytest.mark.parametrize(
        'patch_settings',
        [
            {'auth_email': 'from@test.com', 'auth_secret_key': 'auth-secret-key', 'auth_salt': 'auth-salt'},
        ],
        indirect=True
    )
    def test_build_email_message(self, patch_settings: Settings):
        # TODO: Add a test for serialization
        # Act
        msg = build_email_message('to@test.com')

        # Assert
        assert msg['From'] == 'from@test.com'
        assert msg['To'] == 'to@test.com'


class TestSendLoginEmail:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        'patch_settings',
        [
            {'auth_email': 'from@test.com', 'auth_email_password': 'auth-email-password'},
        ],
        indirect=True
    )
    async def test_send_login_email(self, mocker, patch_settings: Settings):
        # Arrange
        mock_smtp = mocker.MagicMock(name='petitlink.auth.core.smtplib.SMTP')
        mocker.patch('petitlink.auth.core.smtplib.SMTP', new=mock_smtp)
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
