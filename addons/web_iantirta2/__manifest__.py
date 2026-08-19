{  # noqa: B018
    'name': "web_iantirta",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "iantirta.com",
    'website': "https://www.iantirta.com.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/sigil/sigil/blob/15.0/sigil/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Hidden',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'web'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/res_company_data.xml',
        'data/ir_config_parameter_data.xml',
        'data/mail_alias_domain_data.xml',
        'data/ir_mail_server_data.xml',
        'data/fetchmail_server_data.xml',

        'views/iantirta_menu_views.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/res_partner_demo.xml',
        'demo/demo.xml',
    ],
}

