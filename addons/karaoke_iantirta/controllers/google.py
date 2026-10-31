# Part of Iantirta.com
# See LICENSE file for full copyright and licensing details.

from sigil.http import Controller, request, route


class GoogleOauthController(Controller):
    @route("/google_oauth/callback", type="http", auth="user")
    def google_oauth_callback(self, error: str | None = None, **kwargs):
        """
        Redirect callback used for google oauth ``redirect_uri``.
        
        :param str | None error:
        """
        if error:
            return request.make_response(f"Authentication failed: {error}")

        try:
            from iantirta.media.tools.google import GoogleApi
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                "Cannot Continue as iantirta-media is not installed"
            )

        state = GoogleApi.parse_state(kwargs.pop('state'))

        record_id = state.get('id', None)
        model_name = state.get('model', None)
        key = state.get('key', None)
        creds_field = state.get('creds_field', None)

        if not record_id:
            return request.make_response(
                "Invalid request. Missing State Record ID."
            )

        if not model_name:
            return request.make_response(
                "Invalid request. Missing State Model Name."
            )

        if not key:
            return request.make_response(
                "Invalid request. Missing State Key."
            )

        if not creds_field:
            return request.make_response(
                "Invalid request. Missing Creds Field."
            )

        record = request.env[model_name].browse(int(record_id)).exists()
        try:
            creds = GoogleApi.creds_from_flow_token(
                key=key,
                code=kwargs.pop('code')
            )

        except Exception as e:
            return request.make_response(f"Error fetching token: {e}")

        record.write({
            creds_field: creds.to_json()
        })

        return request.redirect(
            f'/web#id={record.id}&model={model_name}&view_type=form'
        )
