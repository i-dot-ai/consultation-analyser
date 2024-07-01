module "rds" {
  source                  = "../../i-ai-core-infrastructure//modules/rds"
  vpc_id                  = data.terraform_remote_state.vpc.outputs.vpc_id
  public_subnet_ids_list  = data.terraform_remote_state.vpc.outputs.public_subnets
  private_subnet_ids_list = data.terraform_remote_state.vpc.outputs.private_subnets
  instance_type           = "db.t3.large"
  db_name                 = var.project_name
  kms_secrets_arn         = data.terraform_remote_state.platform.outputs.kms_key_arn
  name                    = local.name
  domain_name             = var.domain_name
  state_bucket            = var.state_bucket
  service_sg_ids          = [module.ecs.ecs_sg_id]
  publicly_accessible     = var.publicly_accessible
  securelist_ips          = concat(var.developer_ips, var.internal_ips)
  secret_tags = {
    "platform:secret-purpose" : "general"
  }
}
