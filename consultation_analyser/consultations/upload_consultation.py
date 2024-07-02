import json

from django.utils.text import slugify

from consultation_analyser.consultations.public_schema import ConsultationWithResponses

from .models import Answer, Consultation, ConsultationResponse, Question, Section


def upload_consultation(file, user):
    uploaded_json = file.read()

    consultation_data = json.loads(uploaded_json)
    consultation_with_responses = ConsultationWithResponses(**consultation_data)

    # convert to JSON and back to get a big dict
    attrs = json.loads(consultation_with_responses.json())

    responses = attrs["consultation_responses"]
    consultation_attrs = attrs["consultation"]
    sections = consultation_attrs.pop("sections")

    consultation_attrs["slug"] = slugify(consultation_attrs["name"])
    consultation = Consultation(**consultation_attrs)
    consultation.save()
    consultation.users.set([user])

    question_ids_map = {}

    for section_attrs in sections:
        section_attrs["consultation_id"] = consultation.id
        questions = section_attrs.pop("questions")
        section_attrs["slug"] = slugify(section_attrs["name"])
        section = Section(**section_attrs)
        section.save()
        for question_attrs in questions:
            supplied_id = question_attrs.pop("id")
            question_attrs["slug"] = slugify(question_attrs["text"])
            question_attrs["multiple_choice_options"] = question_attrs.pop("multiple_choice")
            question_attrs["section_id"] = section.id
            question = Question(**question_attrs)
            question.save()
            question_ids_map[supplied_id] = question.id

    for response_attrs in responses:
        answers = response_attrs.pop("answers")
        response_attrs["consultation_id"] = consultation.id
        response = ConsultationResponse(**response_attrs)
        response.save()
        for answer_attrs in answers:
            if "theme_id" in answer_attrs.keys():
                answer_attrs.pop("theme_id")  # discard this if present
            answer_attrs["consultation_response_id"] = response.id
            question_id = answer_attrs.pop("question_id")
            answer_attrs["question_id"] = question_ids_map[question_id]
            answer = Answer(**answer_attrs)
            answer.save()

    return consultation
