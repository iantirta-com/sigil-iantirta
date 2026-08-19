{
    'name': "Web Enterprise",
    'category': 'Hidden',
    'description': """

Sigil Enterprise Web Client.
============================

This module modifies the web addon to provide Enterprise design and responsiveness.
    """,
    'version': '1.0',
    'depends': ['web', 'base_setup'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_users_views.xml',
        'views/webclient_templates.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('before', 'web/static/src/scss/primary_variables.scss',
             'web_enterprise/static/src/scss/primary_variables.scss'),
            ('after', 'web/static/src/scss/primary_variables.scss',
             'web_enterprise/static/src/webclient/**/*.variables.scss'),
        ],
        'web._assets_secondary_variables': [
            ('prepend', 'web_enterprise/static/src/scss/secondary_variables.scss'),
        ],
        'web._assets_backend_helpers': [
            ('prepend', 'web_enterprise/static/src/scss/bootstrap_overridden.scss'),
        ],
        'web.assets_backend': [
            'web_enterprise/static/src/webclient/**/*',
            'web_enterprise/static/src/views/**/*',
            'web_enterprise/static/src/core/notebook/notebook.scss',
        ],
        'web.assets_frontend': [
            'web_enterprise/static/src/core/**/*',
        ],
        'web._assets_core': [
            'web_enterprise/static/src/core/**/*',
        ],
        'web.assets_web': [
            ('replace', 'web/static/src/main.js',
             'web_enterprise/static/src/main.js'),
        ],
    },
    'author': "iantirta.com",   
}

