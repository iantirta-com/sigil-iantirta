{  # noqa: B018
    'name': "web_iantirta",
    'summary': "Short (1 phrase/line) summary of the module's purpose",
    'description': """
Long description of module's purpose
    """,
    'author': "iantirta.com",
    'website': "https://www.iantirta.com.com",
    'category': 'Hidden',
    'version': '0.1',
    "license": "Other OSI approved licence",
    'depends': ['web'],
    'assets': {
        'web._assets_primary_variables': [
            ('before', 'web/static/src/scss/primary_variables.scss',
                'web_iantirta/static/src/scss/m3.variables.scss'),
            ('before', 'web/static/src/scss/primary_variables.scss',
                'web_iantirta/static/src/scss/primary_variables.scss'),
            ('after', 'web/static/src/scss/primary_variables.scss',
                'web_iantirta/static/src/**/*.variables.scss'),
        ],
        'web.assets_backend': [
        #     'web_iantirta/static/src/webclient/**/*',
        #     'web_iantirta/static/src/search/**/*',
        #     'web_iantirta/static/src/views/**/*',
            "web_iantirta/static/src/webclient/navbar/*",
            "web_iantirta/static/src/views/view.scss",
            "web_iantirta/static/src/views/list/*",
        ],
        'web._assets_core': [
            'web_iantirta/static/src/core/**/*',
        ],
        'web.assets_frontend': [
            # 'web_iantirta/static/src/core/**/*',
            "web_iantirta/static/src/login.scss"
        ],
        'web._assets_backend_helpers': [
            ('prepend', 'web_iantirta/static/src/scss/bootstrap_overridden.scss'),
        ],
        'web._assets_secondary_variables': [
            ('prepend', 'web_iantirta/static/src/scss/bootstrap_overridden.scss'),
            'web_iantirta/static/src/scss/secondary_variables.scss',
        ],
    },
    'data': [
        'data/res_company_data.xml',
        'views/webclient_templates.xml',
    ],
    'demo': [
        'demo/res_users_demo.xml',
        'demo/res_partner_demo.xml',
    ],
}

