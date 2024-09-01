# -*- coding: utf-8 -*-
{
    'name': "Add ABI and CAB to bank",

    'summary': """
        Add ABI and CAB to bank
        """,

    'description': """
    Modulo per la gestione e l'aggiornamento dei codici ABI e CAB delle banche italiane.
    Per maggiori dettagli, consultare la descrizione completa nel file index.html.
    """,

    'author': "FL1 sro",
    'website': "https://fl1.cz",
    'maintainer': 'FL1 sro',
    'version': '16.0.0.1',
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
    'category': 'Localization',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    
    # Available options: Technical, Accounting, Localization, Payroll Localization, Payroll Localization, Account Charts,
    # User types, Invoicing, Sales, Human Resources, Marketing, Manufacturing, Website, Theme, Administration, Appraisals, Sign,
    # Services, Helpdesk, Field Service, Inventory, Productivity, Customizations, Administration, Extra Rights, Other Extra Rights
    



    # any module necessary for this one to work correctly
    'depends': ['base'],
    'external_dependencies': {
        'python': [
  
        ],
    },


    'data': [
        
        'security/ir.model.access.csv',
        
       
        'data/data.xml',
        
       
        'views/abicab.xml',
        
    ],
    
    'demo': [
        # 'demo/demo.xml',
    ],
    
    "assets": {
        "web.assets_backend": [
            "bank_abicab/static/src/xml/list_controller.xml",
            "bank_abicab/static/src/js/list_controller.js",
        ],
    },
}