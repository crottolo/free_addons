# -*- coding: utf-8 -*-
{
    'name': "ABI e CAB per Banche Italiane",
    'summary': """
        Gestione e aggiornamento automatico dei codici ABI e CAB delle banche italiane
    """,
    'description': """
        Questo modulo estende le funzionalità di Odoo per la gestione delle banche italiane, aggiungendo i campi ABI e CAB.
    """,
    'author': "FL1 sro",
    'website': "https://fl1.cz",
    'maintainer': 'FL1 sro',
    'version': '16.0.0.1',
    'license': 'LGPL-3',
    'category': 'Accounting/Localizations',
    'images': ['images/main_screenshot.png'],
    'depends': ['base', 'account', 'contacts'],
    "external_dependencies": {
        "python": ['schwifty']
    },
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/abicab.xml',
    ],
    'assets': {
        "web.assets_backend": [
            "bank_abicab/static/src/xml/list_controller.xml",
            "bank_abicab/static/src/js/list_controller.js",
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
