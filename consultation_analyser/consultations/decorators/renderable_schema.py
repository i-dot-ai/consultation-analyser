import json
from pydantic import BaseModel


class RenderableSchema:
    def __init__(self, schema: BaseModel):
        self.schema = schema

    def name(self):
        return self.schema.__name__

    def description(self):
        return self.schema.__doc__

    def example(self):
        result = {}

        for name, field in self.schema.model_fields.items():
            result[name] = field.json_schema_extra.get("example")

        if output := dict(result):
            return json.dumps(output, indent=4)

    def rows(self):
        output = []
        for field_name in self.schema.model_fields.keys():
            field = self.schema.model_fields[field_name]

            field_details = {
                "name": field_name,
                "description": field.description,
            }

            if field.json_schema_extra:
                example = field.json_schema_extra.get("example")
                field_details["example"] = example

            output.append(field_details)

        return output
