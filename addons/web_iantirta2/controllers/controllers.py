# from sigil import http


# class WebIantirta(http.Controller):
#     @http.route('/web_iantirta/web_iantirta', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/web_iantirta/web_iantirta/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('web_iantirta.listing', {
#             'root': '/web_iantirta/web_iantirta',
#             'objects': http.request.env['web_iantirta.web_iantirta'].search([]),
#         })

#     @http.route('/web_iantirta/web_iantirta/objects/<model("web_iantirta.web_iantirta"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('web_iantirta.object', {
#             'object': obj
#         })

