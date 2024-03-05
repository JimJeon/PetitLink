import pytest

from collections.abc import Iterator
from pytest import FixtureRequest
from pydantic_core import PydanticUndefinedType

from main import settings, AuthSettings


# Patching pydantic settings for pytest
# https://rednafi.com/python/patch_pydantic_settings_in_pytest/
@pytest.fixture
def patch_settings(request: FixtureRequest) -> Iterator[AuthSettings]:
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
