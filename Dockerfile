FROM python:3.12
WORKDIR /app
RUN pip install poetry

# COPY ./ /app
COPY pyproject.toml poetry.lock /petitlink/
VOLUME ["/petitlink"]

RUN poetry install --no-root
EXPOSE 8000
ENTRYPOINT [ "poetry", "run", "uvicorn", "main:app", "--reload" ]