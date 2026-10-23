

def setup_user_token(
    record,
    *,
    creds_field: str,
    client_config_field: str,
    scopes: list[str],
) -> dict:
    try:
        from iantirta.media.tools.google import GoogleApi
    except ModuleNotFoundError:
        raise ModuleNotFoundError("Cannot Continue as iantirta-media is not installed")

    if (
        not record[creds_field]
        or not (creds := GoogleApi.creds_from_user_token(
            user_token=record[creds_field]
        ))
    ):
        key = f'{record._name.replace('.', '_')}_{record.id}'
        api_state = GoogleApi.make_state({
            'model': record._name,
            'id': record.id,
            'key': key,
            'creds_field': creds_field
        })
        auth_uri, _ = GoogleApi.get_auth_url(
            key=key,
            client_config=record[client_config_field],
            redirect_uri=f"{record.get_base_url().rstrip('/')}/google_oauth/callback",
            scopes=scopes,
            state=api_state,
        )
        return {
            'type': 'ir.actions.act_url',
            'url': auth_uri,
            'target': 'self',
        }
    else:
        record.write({
            creds_field: creds.to_json()
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Google user token refreshed successfully.',
                'type': 'success',
                'sticky': False,
            }
        }
