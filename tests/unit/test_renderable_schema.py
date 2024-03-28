from consultation_analyser.consultations.decorators.renderable_schema import RenderableSchema
from consultation_analyser.consultations import public_schema


def test_renderable_schema():
    renderable = RenderableSchema(public_schema.Consultation)

    raise Exception(public_schema.Consultation.model_json_schema())
    assert renderable.name() == "Consultation"
    # assert renderable.description() == ""
    assert renderable.example() == {}


schema = public_schema.Consultation.model_json_schema(mode="validation")
import json

print(json.dumps(schema))
