from pydantic import BaseModel


class RenderableSchema:
    def __init__(self, schema: BaseModel):
        self.schema = schema

    def name(self):
        return self.schema.__name__

    def description(self):
        return self.schema.__doc__

    def rows(self):
        output = []
        for field_name in self.schema.model_fields.keys():
            field = self.schema.model_fields[field_name]

            field_details = {
                "name": field_name,
                "description": field.description,
            }

            output.append(field_details)

        return output
