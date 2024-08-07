import json
import logging
import os
import platform
import time
from pathlib import Path
from typing import Optional

import torch
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from consultation_analyser.authentication.models import User
from consultation_analyser.consultations import models
from consultation_analyser.consultations.download_consultation import consultation_to_json
from consultation_analyser.consultations.upload_consultation import upload_consultation
from consultation_analyser.pipeline.processing import (
    get_llm_backend,
    get_topic_backend,
    process_consultation_themes,
)

logger = logging.getLogger("pipeline")


class Command(BaseCommand):
    help = "Run the pipeline, write JSON with outputs for evaluation"

    def add_arguments(self, parser):
        parser.add_argument(
            "--input",
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
            help="The llm to use for summarising. Will be fake by default. Pass 'fake', 'bedrock' or 'ollama/model' to specify a model",
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
            "--device",
            action="store",
            help="The device to target the embedding at. For example: 'cpu', 'cuda', 'mps'",
            type=str,
        )

    def handle(self, *args, **options):
        logger.info(f"Called evaluate with {options}")

        consultation = self.__load_consultation(input_file=options["input"], clean=options["clean"])
        output_dir = self.__get_output_dir(
            output_dir=options["output_dir"], consultation=consultation
        )
        device = self.__check_device(options["device"]) if options["device"] else None
        persistence_path = output_dir / "bertopic"
        embedding_model = options["embedding_model"]

        topic_backend = get_topic_backend(
            embedding_model=embedding_model, persistence_path=persistence_path, device=device
        )
        llm_backend = get_llm_backend(llm_identifier=options["llm"])

        process_consultation_themes(
            consultation, topic_backend=topic_backend, llm_backend=llm_backend
        )

        self.__save_consultation_with_themes(output_dir=output_dir, consultation=consultation)

        logger.info(f"Wrote results to {output_dir}")

    def __load_consultation(self, input_file: str, clean: Optional[bool]):
        if not input_file:
            raise Exception("You need to specify an input file")

        # upload, cleaning if required
        if clean:
            input_json = json.loads(open(input_file).read())
            name = input_json["consultation"]["name"]
            old_consultation = models.Consultation.objects.get(name=name)
            old_consultation.delete()
            logger.info("Removed original consultation")

        try:
            user = User.objects.filter(email="email@example.com").first()

            with open(input_file, mode="rb") as file:
                consultation = upload_consultation(file, user)
        except IntegrityError:
            logger.info(
                "This consultation already exists. To remove it and start with a fresh copy pass --clean."
            )
            exit()

        return consultation

    def __get_output_dir(self, consultation: models.Consultation, output_dir: Optional[str] = None):
        if not output_dir:
            output_dir = (
                settings.BASE_DIR / "tmp" / "outputs" / f"{consultation.slug}-{int(time.time())}"
            )

        assert output_dir  # mypy
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def __save_consultation_with_themes(self, output_dir: Path, consultation: models.Consultation):
        json_with_themes = consultation_to_json(consultation, consultation.latest_processing_run)
        f = open(output_dir / "consultation_with_themes.json", "w")
        f.write(json_with_themes)
        f.close()

    def __check_device(self, requested_device):
        logger.info(f"Checking '{requested_device}' is available...")
        devices = ["cpu"]

        # Check for CUDA devices
        if torch.cuda.is_available():
            devices.append("cuda")

        # Check for MPS devices (Apple Silicon) only if running on macOS
        if (
            platform.system() == "Darwin"
            and torch.backends.mps.is_available()
            and torch.backends.mps.is_built()
        ):
            devices.append("mps")

        # Return requested device if available, else return CPU
        device = requested_device if requested_device in devices else "cpu"
        if device == requested_device:
            logger.info(f"Device '{requested_device}' is available.")
        else:
            logger.info(f"Device '{requested_device}' is unavailable, defaulting to '{device}'")

        return device
