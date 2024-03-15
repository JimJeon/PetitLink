from abc import ABC, abstractmethod
from typing import List

from fastapi import Request


class Form(ABC):
    @abstractmethod
    async def load_data(self):
        pass

    @abstractmethod
    async def is_valid(self):
        pass


class LoginForm(Form):
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.email: str | None = None
        self.password: str | None = None

    async def load_data(self):
        form = await self.request.form()
        self.email = form.get('email')
        self.password = form.get('password')

    async def is_valid(self):
        if not self.email or not (self.email.__contains__('@')):
            self.errors.append('Email is required')
        if not self.errors:
            return True
        return False


class RegisterForm(Form):
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.password: str | None = None

    async def load_data(self):
        form = await self.request.form()
        self.password = form.get('password')

    async def is_valid(self):
        if len(self.password) <= 8:
            self.errors.append('Password must be longer than 8 characters')
        if not self.errors:
            return True
        return False


class CreateNewPetitLinkForm(Form):
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.link: str | None = None

    async def load_data(self):
        form = await self.request.form()
        self.link = form.get('link')

    async def is_valid(self):
        pass
