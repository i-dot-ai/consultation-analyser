locals {
  name = "${var.team_name}-${terraform.workspace}-${var.project_name}"
}
module "postgres" {
  source              = "../../../i-ai-core-infrastructure//modules/postgres"
  kms_secrets_arn     = data.terraform_remote_state.platform.outputs.kms_key_arn
  name                = local.name
  db_name             = "postgres"
  db_instance_address = data.terraform_remote_state.consultations.outputs.db_instance_address
  db_master_username  = data.terraform_remote_state.consultations.outputs.db_master_username
  db_master_password  = data.terraform_remote_state.consultations.outputs.db_master_password

}


data "terraform_remote_state" "platform" {
  backend   = "s3"
  workspace = terraform.workspace
  config = {
    bucket = var.state_bucket
    key    = "platform/terraform.tfstate"
    region = var.region
  }
}

data "terraform_remote_state" "consultations" {
  backend   = "s3"
  workspace = terraform.workspace
  config = {
    bucket = var.state_bucket
    key    = "consultation-analyser/terraform.tfstate"
    region = var.region
  }
}

provider "aws" {
  default_tags {
    tags = {
      Environment = terraform.workspace
      Deployed    = "github"
    }
  }
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.53.0"
    }

    random = {
      source  = "hashicorp/random"
      version = ">=3.6.2"
    }
  }
  required_version = ">= 1.3.5"

  backend "s3" {
    key = "consultation-analyser-postgres/terraform.tfstate"
  }

}
