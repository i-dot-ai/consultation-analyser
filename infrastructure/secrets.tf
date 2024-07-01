resource "aws_secretsmanager_secret" "django_secret" {
  name        = "${local.name}-django-secret"
  description = "Django secret for ${local.name}"
  tags = {
    "platform:secret-purpose" = "general" # pragma: allowlist secret
  }
}

data "aws_secretsmanager_secret" "django_secret" {
  name = "${local.name}-django-secret"
}

data "aws_secretsmanager_secret_version" "django_secret" {
  secret_id = data.aws_secretsmanager_secret.django_secret.id
}

data "aws_secretsmanager_secret" "env_vars" {
  name = "${local.name}-environment-variables"
}
data "aws_secretsmanager_secret_version" "env_vars" {
  secret_id = data.aws_secretsmanager_secret.env_vars.id
}
