-include .env
export

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z\.\-\_]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: setup_dev_db
setup_dev_db: ## Set up the development db on a local postgres
	createdb consultations_dev
	-createuser consultations_dev
	-psql -d postgres -c 'GRANT ALL ON database consultations_dev TO consultations_dev;'

.PHONY: reset_dev_db
reset_dev_db: ## Reset the dev db
	dropdb consultations_dev
	$(MAKE) setup_dev_db

.PHONY: setup_test_db
setup_test_db:  ## Set up the test db on a local postgres
	createdb consultations_test
	-createuser consultations_test
	-psql -d postgres -c 'GRANT ALL ON database consultations_test TO consultations_test; ALTER USER consultations_test CREATEDB;'

.PHONY: reset_test_db
reset_test_db: ## Reset the test db
	dropdb consultations_test
	$(MAKE) setup_test_db

.PHONY: check_db
check_db: ## Make sure the db is addressable
	poetry run python manage.py check --database default

.PHONY: migrate
migrate: ## Apply migrations
	poetry run python manage.py migrate
	poetry run python manage.py generate_erd

.PHONY: serve
serve: ## Run the server
	poetry run gunicorn -c consultation_analyser/gunicorn.py consultation_analyser.wsgi

.PHONY: test
test: ## Run the tests
	poetry run pytest

.PHONY: govuk_frontend
govuk_frontend: ## Pull govuk-frontend
	npm install
	poetry run python manage.py collectstatic --noinput

.PHONY: dummy_data
dummy_data: ## Generate a dummy consultation. Only works in dev
	poetry run python manage.py generate_dummy_data

# Docker
AWS_REGION=eu-west-2
APP_NAME=consultations
ECR_URL=$(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
ECR_REPO_URL=$(ECR_URL)/$(ECR_REPO_NAME)
IMAGE=$(ECR_REPO_URL):$(IMAGE_TAG)

ECR_REPO_NAME=$(APP_NAME)
IMAGE_TAG=$$(git rev-parse HEAD)
tf_build_args=-var "image_tag=$(IMAGE_TAG)"

.PHONY: docker_build
docker_build: ## Build the docker container
	docker build . -t $(IMAGE)

.PHONY: docker_run
docker_run: ## Run the docker container
	docker run -e DATABASE_URL=psql://consultations_dev:@host.docker.internal:5432/consultations_dev -p 8000:8000 $(IMAGE)

.PHONY: docker_shell
docker_shell: ## Run the docker container
	docker run -e DATABASE_URL=psql://consultations_dev:@host.docker.internal:5432/consultations_dev -it $(IMAGE) /bin/bash

.PHONY: docker_test
docker_test: ## Run the tests in the docker container
	docker run -e DATABASE_URL=psql://consultations_test:@host.docker.internal:5432/consultations_test $(IMAGE) ./venv/bin/pytest

.PHONY: docker_login
docker_login:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_URL)

.PHONY: docker_push
docker_push:
	docker push $(IMAGE)

.PHONY: docker_update_tag
docker_update_tag:
	MANIFEST=$$(aws ecr batch-get-image --repository-name $(ECR_REPO_NAME) --image-ids imageTag=$(IMAGE_TAG) --query 'images[].imageManifest' --output text) && \
	aws ecr put-image --repository-name $(ECR_REPO_NAME) --image-tag $(tag) --image-manifest "$$MANIFEST"

# Ouputs the value that you're after - useful to get a value i.e. IMAGE_TAG out of the Makefile
.PHONY: docker_echo
docker_echo:
	echo $($(value))

CONFIG_DIR=../../consultation-analyser-infra-config
TF_BACKEND_CONFIG=$(CONFIG_DIR)/backend.hcl

tf_new_workspace:
	terraform -chdir=./infrastructure workspace new $(env)

tf_set_workspace:
	terraform -chdir=./infrastructure workspace select $(env)

tf_set_or_create_workspace:
	make tf_set_workspace || make tf_new_workspace

.PHONY: tf_init
tf_init: ## Initialise terraform
	terraform -chdir=./infrastructure init -backend-config=$(TF_BACKEND_CONFIG)

.PHONY: tf_plan
tf_plan: ## Plan terraform
	make tf_set_workspace && \
	terraform -chdir=./infrastructure plan -var-file=$(CONFIG_DIR)/${env}-input-params.tfvars ${tf_build_args}

.PHONY: tf_apply
tf_apply: ## Apply terraform
	make tf_set_workspace && \
	terraform -chdir=./infrastructure apply -var-file=$(CONFIG_DIR)/${env}-input-params.tfvars ${tf_build_args}

.PHONY: tf_auto_apply
tf_auto_apply: ## Apply terraform
	make tf_set_workspace && \
	terraform -chdir=./infrastructure apply -auto-approve -var-file=$(CONFIG_DIR)/${env}-input-params.tfvars ${tf_build_args}

.PHONY: tf_destroy
tf_destroy: ## Destroy terraform
	make tf_set_workspace && \
	terraform -chdir=./infrastructure destroy -var-file=$(CONFIG_DIR)/${env}-input-params.tfvars ${tf_build_args}

# Release commands to deploy your app to AWS
.PHONY: release
release: ## Deploy app
	chmod +x ./infrastructure/scripts/release.sh && ./infrastructure/scripts/release.sh $(env)
