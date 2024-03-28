# npm
# use the same base image as the others for efficiency
FROM python:3.12-slim AS npm-packages

RUN apt-get update && apt-get install --yes nodejs npm > /dev/null

WORKDIR /src

COPY package.json .
RUN npm install


# poetry
FROM python:3.12-slim AS poetry-packages

RUN apt-get update && apt-get install --yes build-essential > /dev/null

RUN pip install poetry poetry-plugin-bundle

WORKDIR /src

COPY pyproject.toml .
COPY poetry.lock .

# do this so that poetry bundle can run without the project - can't pass --no-root to bundle
RUN touch README.md

RUN poetry bundle venv ./venv


# app
FROM python:3.12-slim

RUN apt-get update && apt-get install --yes libpq-dev > /dev/null

WORKDIR /usr/src/app

COPY --from=npm-packages /src/node_modules ./node_modules
COPY --from=poetry-packages /src/venv ./venv

COPY . .

ENV DJANGO_SETTINGS_MODULE='consultation_analyser.settings.production'
ENV PYTHONPATH "${PYTHONPATH}:/."

EXPOSE 8000

CMD ["./start.sh"]
