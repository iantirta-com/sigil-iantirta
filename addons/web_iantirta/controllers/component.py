
from sigil.http import Controller, request, Response, route, content_disposition


class ComponentController(Controller):
    """ Its used for debugging component """

    @route("/web/components", type="http", auth="user", sitemap=False, readonly=True,)
    def components(self, **kwargs):
        return request.render("web_iantirta.components_page")
        