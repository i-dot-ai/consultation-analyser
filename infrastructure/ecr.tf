module "ecr" {
  source                = "../../i-ai-core-infrastructure//modules/ecr"
  project_name          = var.project_name
  container_name_suffix = null
  count                 = data.aws_ecr_repository.existing[0].repository_url != null ? 0 : 1
}

locals {
  container_name_suffix = null
  ecr_name              = local.container_name_suffix != null ? "${var.project_name}-${local.container_name_suffix}" : var.project_name
}

data "aws_ecr_repository" "existing" {
  name  = local.ecr_name
  count = var.project_name != null ? 1 : 0
}

