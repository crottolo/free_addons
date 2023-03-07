{
    'name': 'Odoo Enterprise Theme',
    'version': '15.0.1.0.1',
    'summary': 'Odoo Enterprise Theme',
    'author': 'fl1 sro',
    'license': 'AGPL-3',
    'maintainer': 'Fl1',
    'company': 'Fl1 sro',
    'website': 'https://fl1.cz',
    'depends': [
        'web'
    ],
    'category':'Branding',
    'description': """
           Odoo Enterprise Theme
    """,
    'assets': {
        'web._assets_primary_variables': [
            '/legion_enterprise_theme/static/src/scss/primary_variables_custom.scss',
        ],
        'web._assets_secondary_variablesweb.assets_backend': [
            '/legion_enterprise_theme/static/src/scss/fields_extra_custom.scss',
        ],
        'web._assets_secondary_variables': [
            '/legion_enterprise_theme/static/src/scss/secondary_variables.scss',
        ],
    },
    'price':0,
    'currency':'USD',
    'installable': True,
    'auto_install': False,
    'application': True,
    'images': ['static/description/icon.png','static/description/main_screenshot.png']
}
