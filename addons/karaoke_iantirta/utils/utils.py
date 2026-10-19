
import ast
import json

from sigil import api, fields
from sigil.http import request
from sigil.tools import consteq, float_round
from sigil.tools.misc import hmac as hmac_tool

# Access token management

def generate_access_token(*values, env=None) -> str:
    """ Generate an access token based on the provided values.

    The token allows to later verify the validity of a request, based on a given set of values.
    These will generally include the partner id, amount, currency id, transaction id or transaction
    reference.
    All values must be convertible to a string.

    :param list values: The values to use for the generation of the token
    :param api.Environment env: The environment to use for the generation of the token
    :return: The generated access token
    :rtype: str
    """
    env = env or (request and request.env)
    assert isinstance(env, api.Environment), "Environment required to generate access token."
    token_str = '|'.join(str(val) for val in values)
    access_token = hmac_tool(env(su=True), 'generate_access_token', token_str)
    return access_token


def check_access_token(access_token, *values) -> bool:
    """ Check the validity of the access token for the provided values.

    The values must be provided in the exact same order as they were to `generate_access_token`.
    All values must be convertible to a string.

    :param str access_token: The access token used to verify the provided values
    :param list values: The values to verify against the token
    :return: True if the check is successful
    :rtype: bool
    """
    authentic_token = generate_access_token(*values)
    return access_token and consteq(access_token, authentic_token)


# Log merging

def merge_log(
    current_log: str | bool | list,
    new_log: str | bool | list,
    *,
    max_items: int = 100,
) -> list:
    def _parse_log(log: str | bool | list) -> list:
        if not log:
            return []
        else:
            try:
                if isinstance(log, list):
                    return log
                else:
                    return json.loads(log)
            except json.decoder.JSONDecodeError:
                return ast.literal_eval(log)

    combined = _parse_log(current_log) + _parse_log(new_log)
    return combined[-max_items:]
