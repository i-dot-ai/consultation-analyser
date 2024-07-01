import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from consultation_analyser.authentication.models import User
from consultation_analyser.consultations import models
from consultation_analyser.consultations.download_consultation import consultation_to_json
from consultation_analyser.consultations.upload_consultation import upload_consultation
from consultation_analyser.pipeline.backends.bertopic import BERTopicBackend
from consultation_analyser.pipeline.backends.dummy_topic_backend import DummyTopicBackend
from consultation_analyser.pipeline.processing import get_llm_backend, process_consultation_themes

logger = logging.getLogger("pipeline")


class Command(BaseCommand):
    help = "Run the pipeline, write JSON with outputs for evaluation"

    def add_arguments(self, parser):
        parser.add_argument(
            "--input_file",
            action="store",
            help="A path to a JSON file containing a ConsultationWithResponses",
            type=str,
        )
        parser.add_argument(
            "--embedding_model",
            action="store",
            help="The embedding model to use in BERTopic. Pass 'fake' to get fake topics",
            type=str,
        )
        parser.add_argument(
            "--llm",
            action="store",
            help="The llm to use for summarising. Will be fake by default. Pass 'sagemaker' or 'ollama/model' to specify a model",
            type=str,
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Whether to delete an existing matching consultation first",
        )
        parser.add_argument(
            "--output_dir",
            action="store",
            help="The output directory - defaults to tmp/eval/$consultation-slug-$unixtime",
        )
        parser.add_argument(
            "--consultation_slug",
            action="store",
            help="The slug of the consultation to process",
        )

    def handle(self, *args, **options):
        logger.info(f"Called generate_themes with {options}")

        consultation = self.__load_consultation(
            consultation_slug=options["consultation_slug"],
            input_file=options["input_file"],
            clean=options["clean"],
        )
        output_dir = self.__get_output_dir(
            output_dir=options["output_dir"], consultation=consultation
        )
        topic_backend = self.__get_topic_backend(
            embedding_model=options["embedding_model"], persistence_path=output_dir / "bertopic"
        )
        llm_backend = get_llm_backend(llm_identifier=options["llm"])

        process_consultation_themes(
            consultation, topic_backend=topic_backend, llm_backend=llm_backend
        )

        logger.info(f"Generated themes for consultation {consultation.name}")

        self.__save_consultation_with_themes(output_dir=output_dir, consultation=consultation)

        logger.info(f"Wrote results to {output_dir}")

    def __load_consultation(self, consultation_slug: str, input_file: str, clean: Optional[bool]):
        if (not input_file and not consultation_slug) or (input_file and consultation_slug):
            raise Exception("Please specify either --input_file or --consultation_slug")

        if consultation_slug:
            return models.Consultation.objects.get(slug=consultation_slug)

        # upload, cleaning if required
        if clean:
            input_json = json.loads(open(input_file).read())
            name = input_json["consultation"]["name"]
            try:
                old_consultation = models.Consultation.objects.get(name=name)
                old_consultation.delete()
                logger.info("Removed original consultation")
            except ObjectDoesNotExist:
                logger.info("No existing consultation to clean, moving on")

        try:
            user = User.objects.filter(email="email@example.com").first()
            consultation = upload_consultation(open(input_file), user)
        except IntegrityError as e:
            logger.info(e)
            logger.info(
                "This consultation already exists. To remove it and start with a fresh copy pass --clean."
            )
            exit()

        return consultation

    def __get_topic_backend(
        self, persistence_path: Optional[Path] = None, embedding_model: Optional[str] = ""
    ):
        if embedding_model == "fake":
            logger.info("Using fake topic model")
            return DummyTopicBackend()
        elif embedding_model:
            return BERTopicBackend(
                embedding_model=embedding_model, persistence_path=persistence_path
            )
        else:
            return BERTopicBackend(persistence_path=persistence_path)

    def __get_output_dir(self, consultation: models.Consultation, output_dir: Optional[str] = None):
        if not output_dir:
            output_dir = (
                settings.BASE_DIR / "tmp" / "outputs" / f"{consultation.slug}-{int(time.time())}"
            )

        assert output_dir  # mypy
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def __save_consultation_with_themes(self, output_dir: Path, consultation: models.Consultation):
        json_with_themes = consultation_to_json(consultation)
        f = open(output_dir / "consultation_with_themes.json", "w")
        f.write(json_with_themes)
        f.close()
