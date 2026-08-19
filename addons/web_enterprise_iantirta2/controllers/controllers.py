# from sigil import http


# class WebEnterpriseIantirta(http.Controller):
#     @http.route('/web_enterprise_iantirta/web_enterprise_iantirta', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/web_enterprise_iantirta/web_enterprise_iantirta/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('web_enterprise_iantirta.listing', {
#             'root': '/web_enterprise_iantirta/web_enterprise_iantirta',
#             'objects': http.request.env['web_enterprise_iantirta.web_enterprise_iantirta'].search([]),
#         })

#     @http.route('/web_enterprise_iantirta/web_enterprise_iantirta/objects/<model("web_enterprise_iantirta.web_enterprise_iantirta"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('web_enterprise_iantirta.object', {
#             'object': obj
#         })

