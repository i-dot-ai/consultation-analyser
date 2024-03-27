import json
from .. import public_schema
from ..decorators.renderable_schema import RenderableSchema
from django.conf import settings
from django.http import HttpRequest
from django.shortcuts import render


def pretty_format_json(json_string: str) -> str:
    return json.dumps(json.loads(json_string), indent=2)


def show(request: HttpRequest):
    schema_dir = settings.BASE_DIR / "consultation_analyser" / "consultations" / "public_schema"

    json_schemas = {
        "consultation": pretty_format_json(open(f"{schema_dir}/consultation_schema.json").read()),
        "consultation_response_list": pretty_format_json(
            open(f"{schema_dir}/consultation_response_list_schema.json").read()
        ),
    }

    json_examples = {
        "consultation": pretty_format_json(open(f"{schema_dir}/consultation_example.json").read()),
        "consultation_response_list": pretty_format_json(
            open(f"{schema_dir}/consultation_response_list_example.json").read()
        ),
    }

    entity_schemas = [
        RenderableSchema(public_schema.Consultation),
        RenderableSchema(public_schema.Section),
        RenderableSchema(public_schema.Question),
        RenderableSchema(public_schema.Answer),
        RenderableSchema(public_schema.ConsultationResponse),
    ]

    return render(
        request,
        "schema.html",
        {"json_schemas": json_schemas, "json_examples": json_examples, "entity_schemas": entity_schemas},
    )
