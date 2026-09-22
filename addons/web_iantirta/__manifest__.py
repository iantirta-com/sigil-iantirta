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
        'web._assets_secondary_variables': [
            ('prepend', 'web_iantirta/static/src/scss/secondary_variables.scss'),
        ],
        'web._assets_backend_helpers': [
            ('prepend', 'web_iantirta/static/src/scss/bootstrap_overridden.scss'),
        ],

        ## Components specific
        "web_iantirta._bootstrapt_assets": [
            'web/static/lib/popper/popper.js',
            'web/static/lib/bootstrap/js/dist/util/index.js',
            'web/static/lib/bootstrap/js/dist/dom/data.js',
            'web/static/lib/bootstrap/js/dist/dom/event-handler.js',
            'web/static/lib/bootstrap/js/dist/dom/manipulator.js',
            'web/static/lib/bootstrap/js/dist/dom/selector-engine.js',
            'web/static/lib/bootstrap/js/dist/util/config.js',
            'web/static/lib/bootstrap/js/dist/util/component-functions.js',
            'web/static/lib/bootstrap/js/dist/util/backdrop.js',
            'web/static/lib/bootstrap/js/dist/util/focustrap.js',
            'web/static/lib/bootstrap/js/dist/util/sanitizer.js',
            'web/static/lib/bootstrap/js/dist/util/scrollbar.js',
            'web/static/lib/bootstrap/js/dist/util/swipe.js',
            'web/static/lib/bootstrap/js/dist/util/template-factory.js',
            'web/static/lib/bootstrap/js/dist/base-component.js',
            'web/static/lib/bootstrap/js/dist/alert.js',
            'web/static/lib/bootstrap/js/dist/button.js',
            'web/static/lib/bootstrap/js/dist/carousel.js',
            'web/static/lib/bootstrap/js/dist/collapse.js',
            'web/static/lib/bootstrap/js/dist/dropdown.js',
            'web/static/lib/bootstrap/js/dist/modal.js',
            'web/static/lib/bootstrap/js/dist/offcanvas.js',
            'web/static/lib/bootstrap/js/dist/tooltip.js',
            'web/static/lib/bootstrap/js/dist/popover.js',
            'web/static/lib/bootstrap/js/dist/scrollspy.js',
            'web/static/lib/bootstrap/js/dist/tab.js',
            'web/static/lib/bootstrap/js/dist/toast.js',
            'web/static/src/libs/bootstrap.js',
        ],
        "web_iantirta._backend_component_assets": [
            'base/static/src/css/modules.css',

            'web/static/src/core/utils/transitions.scss',
            'web/static/src/model/**/*',
            'web/static/src/search/**/*',
            'web/static/src/webclient/icons.scss', # variables required in list_controller.scss
            'web/static/src/views/**/*',
            ('remove', 'web/static/src/views/graph/**'),
            ('remove', 'web/static/src/views/pivot/**'),

            'web/static/src/webclient/**/*.scss',
            #"web/static/src/webclient/navbar/*",
            #('remove', 'web/static/src/webclient/clickbot/clickbot.js'), # lazy loaded
            #('remove', 'web/static/src/views/form/button_box/*.scss'),

            # remove the report code and whitelist only what's needed
            ('remove', 'web/static/src/webclient/actions/reports/**/*'),
        ],
        "web_iantirta.assets_components_page": [
            'web/static/src/module_loader.js',
            # libs (should be loaded before framework)
            'web/static/lib/luxon/luxon.js',
            'web/static/lib/owl/owl.js',
            'web/static/lib/owl/sigil_module.js',
            
            ("include", "web.assets_backend_lazy"),
            ('include', 'web._assets_bootstrap_backend'),
            ('include', 'web._assets_core'),
            # ("remove", "web/static/src/core/browser/router.js"),
            # ("remove", "web/static/src/core/debug/**/*"),
            
            'web/static/src/polyfills/**/*.js',
            ("include", "web_iantirta._bootstrapt_assets"),
            'web/static/lib/dompurify/DOMpurify.js',
            
            ("include", "web_iantirta._backend_component_assets"),
            
            "web_iantirta/static/src/components_page/**/*",
            "web_iantirta/static/src/components_page/start.js",
        ],
        
        'web.assets_backend': [
        #     'web_iantirta/static/src/webclient/**/*',
        #     'web_iantirta/static/src/search/**/*',
        #     'web_iantirta/static/src/views/**/*',
            "web_iantirta/static/src/webclient/navbar/*",
            "web_iantirta/static/src/webclient/user_menu/*",

            'web_iantirta/static/src/search/**/*',
            "web_iantirta/static/src/views/**/*",
        ],
        'web._assets_core': [
            'web_iantirta/static/src/core/**/*',
        ],
        'web.assets_frontend': [
            'web_iantirta/static/src/core/**/*',
            "web_iantirta/static/src/login.scss",
            ("remove", "web_iantirta/static/src/core/notebook/*"),
        ],
    },
    'data': [
        'data/res_company_data.xml',
        'views/webclient_templates.xml',
        "views/res_users_views.xml",
        "views/res_users_identitycheck_views.xml",
        "views/component_views.xml",
    ],
    'demo': [
        'demo/res_users_demo.xml',
        'demo/res_currency_demo.xml',
        'demo/res_partner_demo.xml',
    ],
    "pre_init_hook": "apply_hook",
    "post_init_hook": "apply_hook",
}

