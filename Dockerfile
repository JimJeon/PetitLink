FROM python:3.12
WORKDIR /petitlink/
RUN pip install poetry

# COPY ./ /petitlink/
COPY pyproject.toml poetry.lock /petitlink/
VOLUME ["/petitlink/"]

RUN poetry install --no-root
EXPOSE 8000
ENTRYPOINT [ "poetry", "run", "uvicorn", "main:app", "--reload" ]