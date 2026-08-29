
from sigil.addons.web.controllers.webmanifest import WebManifest


class WebManifest(WebManifest):
    def _get_webmanifest(self):
        manifest = super()._get_webmanifest()
        manifest["theme_color"] =  "#475d91"
        manifest["background_color"] = "#475d91"
        return manifest
