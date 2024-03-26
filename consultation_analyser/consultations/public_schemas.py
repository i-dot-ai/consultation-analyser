from typing import List, Optional
from pydantic import BaseModel, Field


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
