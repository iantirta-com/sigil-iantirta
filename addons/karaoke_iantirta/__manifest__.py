{  # noqa: B018
    'name': "karaoke_iantirta",
    'summary': "Short (1 phrase/line) summary of the module's purpose",
    'description': """
Long description of module's purpose
    """,
    'author': "iantirta.com",
    'website': "https://www.iantirta.com",
    'category': 'Hidden',
    'version': '0.1',
    "license": "Other OSI approved licence",
    'depends': ['web_iantirta'],
    "external_dependencies": {
        "python": ["kplus",],
    },
    'data': [
        'security/ir.model.access.csv',
        
        'data/ir_config_parameter_data.xml',
        
        'views/webclient_templates.xml',
        "views/karaoke_menu_views.xml",
        "views/gpu_worker_menu_views.xml",
    ],
    "assets": {
        'web.assets_frontend': [
            "karaoke_iantirta/static/src/public/**/*",
        ]
    },
}