{  # noqa: B018
    'name': "web_enterprise_iantirta",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "iantirta.com",
    'website': "https://www.iantirta.com.com",
    'depends': ['base', 'web_enterprise', 'website', 'hr'],
    'assets': {
        'web._assets_primary_variables': [
            ('before', 'web/static/src/scss/primary_variables.scss',
             'web_enterprise_iantirta/static/src/scss/primary_variables.scss'),
            ('after', 'web/static/src/scss/primary_variables.scss',
             'web_enterprise_iantirta/static/src/**/*.variables.scss'),
        ],
        'web.assets_backend': [
            'web_enterprise_iantirta/static/src/webclient/**/*',
            'web_enterprise_iantirta/static/src/search/**/*',
            'web_enterprise_iantirta/static/src/views/**/*',
        ],
        'web._assets_core': [
            'web_enterprise_iantirta/static/src/core/**/*',
        ],
        'web.assets_frontend': [
            'web_enterprise_iantirta/static/src/core/**/*',
        ],
        'web._assets_backend_helpers': [
            ('prepend', 'web_enterprise_iantirta/static/src/scss/bootstrap_overridden.scss'),
        ],
    },
    'category': 'Hidden',
    'version': '0.1',
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/res_company_views.xml',
        'views/res_users_views.xml',
        'views/res_partner_views.xml',
        'views/ir_module_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

