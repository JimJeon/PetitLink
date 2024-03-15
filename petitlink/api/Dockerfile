FROM python:3.12
WORKDIR /api/
RUN pip install poetry

# COPY . /api/
COPY pyproject.toml poetry.lock /api/
VOLUME ["/api/"]

RUN poetry install --no-root
EXPOSE 8001
ENTRYPOINT [ "poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload" ]