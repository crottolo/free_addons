# -*- coding: utf-8 -*-
{
    'name': "Partner Identity Documents",

    'summary': """
        Management of identity documents for partners
        """,

    'description': """
        This module extends the functionality of partners in Odoo by allowing the storage 
        and management of one or more identity documents for each partner. The information 
        stored for each document includes:

        - Document number
        - Document type
        - Issue date
        - Expiry date
        - Document attachment

        Main features:
        - Addition of multiple identity documents per partner
        - Viewing and managing documents in the partner form
        - Ability to attach scans or photos of documents
        - Tracking of expiry dates for proactive renewal management

        This module is useful for companies that need to maintain accurate records 
        of their partners' identity documents for legal, compliance, or security reasons.
    """,

    'author': "FL1 sro",
    'website': "https://fl1.cz",
    'maintainer': 'FL1 sro',
    'version': '16.0.0.1',
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
    'category': 'Services', # Foo / Bar will create a category Foo, a category Bar as child category of Foo, and will set Bar as the module’s category.

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    
    # Available options: Technical, Accounting, Localization, Payroll Localization, Payroll Localization, Account Charts,
    # User types, Invoicing, Sales, Human Resources, Marketing, Manufacturing, Website, Theme, Administration, Appraisals, Sign,
    # Services, Helpdesk, Field Service, Inventory, Productivity, Customizations, Administration, Extra Rights, Other Extra Rights
    



    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts'],
    'external_dependencies': {
        'python': [
  
        ],
    },


    'pre_init_hook': '',
    'uninstall_hook': '',

   
    'data': [
        
        'security/ir.model.access.csv',
        
       
        'data/data.xml',
        
       

        'views/partner_identity_views.xml',
        
    ],
    
    'demo': [
        # 'demo/demo.xml',
    ],
    
    'assets': {
        'web.assets_common': [], # Loaded everywhere (frontend, backend, point of sale).
        'web.assets_backend': [
            # ("after",  "web/path/to/target",  "my_module/path/to/file",)
            # 'partner_identity_id/static/src/js/partner_identity_document_widget.js',
            ], # Only loaded into the "backend" of the application. By backend, I'm talking about where you login as a backend user at /web/login. This bundle is excluded from the frontend website.
        'web.assets_frontend': [], # The opposite of web.assets_backend, only loaded into the frontend website.
        'web.assets_qweb': [], # Loads QWeb XML files.
        'web.assets_wysiwyg': [], # Loads assets into the backend wysiwyg text editor.
        'website.assets_editor': [], # Loads assets into the frontend website edit mode.
        'web.assets_tests': [], # Loads assets for frontend testing and tours.
        'web._assets_primary_variables': [
            # 'account/static/src/scss/variables.scss',
        ], # Used to load custom scss variables for styles.
    
}
}