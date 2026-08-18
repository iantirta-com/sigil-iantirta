from . import models, report, wizard  # noqa: F401


def post_init(env):
    """Rewrite ICP's to force groups"""
    env['ir.config_parameter'].init(force=True)
