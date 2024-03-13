FROM python:3.12
WORKDIR /petitlink/
RUN pip install poetry

COPY . /petitlink/

RUN poetry install --no-root
EXPOSE 8000
ENTRYPOINT [ "poetry", "run", "uvicorn", "app:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]