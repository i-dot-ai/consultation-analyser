
locals {
  batch_image_ecr_url = data.aws_ecr_repository.existing[0].repository_url != null ? data.aws_ecr_repository.existing[0].repository_url : module.ecr.ecr_repository_url
}

module "batch_compute" {
  source          = "../../i-ai-core-infrastructure/modules/batch/batch_compute_environment"
  project         = "i-dot-ai"
  name            = "consultations"
  region          = var.region
  vpc_id          = data.terraform_remote_state.vpc.outputs.vpc_id
  desired_vcpus   = 0
  min_vcpus       = 0
  max_vcpus       = 20
  private_subnets = data.terraform_remote_state.vpc.outputs.private_subnets
  state_bucket    = var.state_bucket
  instance_type   = "g5.xlarge"
}

module "batch_job_definition" {
  source                  = "../../i-ai-core-infrastructure/modules/batch/batch_job_definitons"
  project                 = "i-dot-ai"
  name                    = "consultations"
  region                  = var.region
  compute_environment_arn = [module.batch_compute.ec2_compute_environment_arn]
  state_bucket            = var.state_bucket
  image                   = "${local.batch_image_ecr_url}:${var.image_tag}"
  fargate_flag            = false
}
