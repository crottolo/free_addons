# -*- coding: utf-8 -*-
{
    'name': "3CX CRM lookup",

    'summary': """
        lookup for incoming call from 3cx to odoo""",

    

    "images": ["static/description/banner.png"],
    'author': "FL1 sro",
    'website': "https://fl1.cz",

    # Categories can be used to filter modules in modules listing
    
    # for the full list
    'category': 'Productivity',
    'version': '17.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','crm'],
    'license' : 'AGPL-3',
   

    # always loaded
    'data': [
     
        'data/data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        
    ],
    
}
