FROM python:3.12
WORKDIR /web/
RUN pip install poetry

# COPY . /web/
COPY pyproject.toml poetry.lock /web/
VOLUME ["/web/"]

RUN poetry install --no-root
EXPOSE 8000
ENTRYPOINT [ "poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload" ]