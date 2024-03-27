import environ

env = environ.Env()


class HostingEnvironment:
    @staticmethod
    def is_local():
        return env.str("ENVIRONMENT", "").upper() == "LOCAL"

    @staticmethod
    def is_test() -> bool:
        return env.str("ENVIRONMENT", "").upper() == "TEST"

    @staticmethod
    def is_aws_batch() -> bool:
        return env.str("IS_AWS_BATCH", "")

    @staticmethod
    def is_deployed() -> bool:  # How do we check if AWS?
        environment = env.str("ENVIRONMENT", "").upper()
        deployed_envs = ["dev", "preprod", "prod"]
        if environment in deployed_envs:
            return True
        return False
