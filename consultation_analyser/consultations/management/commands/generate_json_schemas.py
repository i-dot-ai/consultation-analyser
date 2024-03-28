import json
from django.core.management import BaseCommand

from consultation_analyser.consultations import public_schema


class Command(BaseCommand):
    help = "Generates an Entity Relationship Diagram for the repository’s README"

    def handle(self, *args, **options):
        schema_folder = "./consultation_analyser/consultations/public_schema"

        schema = public_schema.Consultation.model_json_schema()
        with open(f"{schema_folder}/consultation_schema.json", "w") as f:
            json.dump(schema, f)

        schema = public_schema.ConsultationResponseList.model_json_schema()
        with open(f"{schema_folder}/consultation_response_list_schema.json", "w") as f:
            json.dump(schema, f)
