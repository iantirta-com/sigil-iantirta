
from sigil.addons.bus.controllers.websocket import WebsocketController
from sigil.addons.mail.tools.discuss import add_guest_to_context
from sigil.http import request, route, SessionExpiredException


class WebsocketControllerPresence(WebsocketController):
    """Override of websocket controller to add mail features (presence in particular)."""

    @route()
    @add_guest_to_context
    def peek_notifications(self, channels, last, is_first_poll=False):
        return super().peek_notifications(channels, last, is_first_poll)

    @route("/websocket/update_bus_presence", type="jsonrpc", auth="public", cors="*")
    def update_bus_presence(self, inactivity_period):
        """Manually update presence of current user, useful when implementing custom websocket code.
        This is mainly used by Sigil.sh."""
        if "is_websocket_session" not in request.session:
            raise SessionExpiredException()
        request.env["ir.websocket"]._update_mail_presence(int(inactivity_period))
        return {}
