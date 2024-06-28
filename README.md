# Consult

Consult is a machine learning and LLM-powered tool to automate the processing of public consultations.

> [!IMPORTANT]
> Incubation Project: This project is an incubation project; as such, we don't recommend using this for critical use cases yet. We are currently in a research stage, trialling the tool for case studies across the Civil Service. If you are a civil servant and wish to take part in our research stage, please register your interest [here](https://www.smartsurvey.co.uk/s/consultation-interest/).


## Setting up the application

### External dependencies

- PostgreSQL (`brew install postgresql`)
- GraphViz (`brew install graphviz`), for generating diagrams

### Environment variables

Populate `.env` by copying `.env.example` and filling in required values.

### Python

Ensure you have `python >= 3.12`, `poetry` and `npm` installed, then run `poetry install`.

### Database setup

```
brew services start postgresql
```
This will run the postgresql locally.

```
make dev_environment
```

This will set up dev and test databases with dummy data. See the definition of that make task for the various steps.

```
make dev_admin_user
```
This will set up the admin account to dev environment.

You will have an staff user (i.e. one that can access the admin) created with the username `email@example.com` and the password `admin`.


Confirm everything is working with

```
make check_db
```

(You can see all the available `make` commands by running bare `make` or `make help`).

### Run the application

```
make serve
```

### Run the tests

```
make test
```

## The database

### Generating dummy data

Only run this in development. Will create a consultation with 10 complete
responses in a variety of question formats. This runs as part of `make
dev_environment`, but you can run it more than once.

```
make dummy_data
```

Or go to `/support/consultations/` and generate a dummy consultation from there.

### Database migrations and schema diagram

If you use the `make migrate` command to run migrations, the diagram below will
be regenerated automatically. If you need to generate it outside that process,
you can run `manage.py generate_erd`. (You will need `graphviz` installed: see
[`pydot` docs](https://pypi.org/project/pydot/)).

![](docs/erd.png)

## Login

### Magic links

You can sign into the application using a magic link, requested via `/sign-in`.

For convenience, in local dev environments the value of the magic link will be
logged along with the rest of the server logs.

### The frontend

#### CSS

We depend on `govuk-frontend` for GOV.UK Design System styles.

`django-compressor` should work automatically to compile the govuk-frontend
SCSS on the first request and any subsequent request after the SCSS has
changed. In the meantime it will read from `frontend/CACHE`, which is
`.gitignore`d.

In production, we prepopulate `frontend/CACHE` using `manage.py compress`
which will mean that every request is served from the cache.

`django-compressor` also takes care of fingerprinting and setting cache headers
for our CSS.

#### Fonts and images

The govuk assets are versioned in the `npm` package. `make dev_environment`
includes a step to copy them to the `frontend` folder from where `runserver`
can serve them; you can rerun this with `make govuk_frontend`.

## Obtaining outputs programatically

The `generate_themes` command will accept a JSON file containing a `ConsultationWithResponses` and emit a JSON file containing a `ConsultationWithResponsesAndThemes`.

Invoke the command like this, replacing the input file with your JSON.
```
poetry run python manage.py generate_themes --input=tests/examples/chocolate.json --clean
```

Options available for this command are:

`--clean`: delete this consultation if it already exists in the database.
`--llm`: which llm to use. Pass `fake`, `sagemaker`, or `ollama/model_name`.
`--embdedding_model`: pass the model for `SentenceTransformers` to use in the `BERTopic` pipeline. If `fake` is passed, random topics will be generated.

The resulting file will be placed in `tmp/outputs` and its path will be printed on the console.

If you are using SageMaker you will need to specify the name of your endpoint in the enviroment variable `SAGEMAKER_ENDPOINT_NAME`.

If you are using Ollama, you will have to install the app (e.g. `brew install ollama`) and have it running `ollama serve`. You will need to run your models e.g. `ollama run mistral`.


## Schema documentation

The data schema for consultations supplied to the tool is defined in `consultation_analyser/consultations/public_schema/public_schema.yaml`.

To build the JSON schemas and examples from this file, run `make schema_docs`.

The `json-schema-faker-options.js` file configures (JSON Schema Faker)[https://github.com/json-schema-faker] to make the JSON examples.

## Frontend Prototype

Located at `/prototype` in this repo, using the GOV.UK Prototype Kit.

### How to run

Ensure you have a recent version of Node.js installed (v16 or greater). Then, **from the prototype directory**, run:

```
npm install
```

Then

```
npm run dev
```

The actual prototype can be accessed at http://localhost:3000/prototype
