FROM python:3.12
WORKDIR /auth/
RUN pip install poetry

COPY . /auth/

RUN poetry install --no-root
EXPOSE 8001
ENTRYPOINT [ "poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]