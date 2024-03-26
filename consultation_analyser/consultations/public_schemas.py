from typing import List, Optional

import json

from pydantic import BaseModel, Field


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


class Consultation(BaseModel):
    """
    A Consultation contains one or more Sections
    """

    name: Optional[str] = Field(
        None,
        description="The name of the consultation",
        example="Consultation on Kit Kats",
    )


class Section(BaseModel):
    """
    Each Section contains one or more Questions
    """

    name: Optional[str] = Field(
        None,
        description="The name of the section",
        example="When to enforce a Kit Kat ban",
    )


class Question(BaseModel):
    """
    Each Question will have one or more Answers
    """

    text: Optional[str] = Field(
        None,
        description="The question text",
        example="Should Kit Kats be banned on Tuesdays",
    )
    has_free_text: Optional[bool] = Field(
        None, description="Does this question have a free text component?", example=True
    )
    multiple_choice_options: Optional[List[str]] = Field(
        None,
        description="The options for the multiple choice part of this question, if it has a multiple choice component",
        example=["Yes", "No", "I don't know"],
    )


class Answer(BaseModel):
    """
    Each Answer is associated with a Question and belongs to a ConsultationResponse
    """

    multiple_choice: Optional[List[str]] = Field(
        None, description="Responses to the multiple choice part of the question, if any", example=["No"]
    )
    free_text: Optional[str] = Field(
        None,
        description="The answer to the free text part of the question, if any",
        example="No, but the Government should consider banning them on Thursdays",
    )


class ConsultationResponse(BaseModel):
    """
    Placeholder for response-level information such as demographics, responding-in-the-capacity-of, etc.
    """
