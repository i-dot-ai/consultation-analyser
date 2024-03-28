locals {
  dev_flag = var.env != "prod" ? true : false
}

module "postgres" {
  source                  = "../../i-ai-core-infrastructure//modules/postgres"
  vpc_id                  = data.terraform_remote_state.vpc.outputs.vpc_id
  public_subnet_ids_list  = data.terraform_remote_state.vpc.outputs.public_subnets
  private_subnet_ids_list = data.terraform_remote_state.vpc.outputs.private_subnets
  instance_type           = "db.t3.large"
  developer_ips           = var.developer_ips
  db_name                 = var.project_name
  kms_secrets_arn         = data.terraform_remote_state.platform.outputs.kms_key_arn
  project                 = "i-dot-ai"
  domain_name             = var.domain_name
  state_bucket            = var.state_bucket
  task_prefix             = var.project_name
  service_sg_ids          = [module.ecs.ecs_sg_id]
  dev_instance            = local.dev_flag
  prod_maintenance        = true
}
