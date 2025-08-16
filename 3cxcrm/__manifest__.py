# -*- coding: utf-8 -*-
{
    'name': "3CX CRM Integration",
    'summary': "Automatic caller identification and CRM lookup for 3CX PBX system",
    'description': """
3CX CRM Integration for Odoo
============================

Seamlessly integrate your 3CX PBX system with Odoo CRM to automatically identify incoming callers 
and display their contact information directly in your phone interface.

Key Features:
* Automatic phone number lookup in Contacts and CRM Leads
* Real-time caller identification during incoming calls
* Direct links to open contact/lead records in Odoo
* Secure API authentication with configurable keys
* Support for both individual contacts and company records
* Compatible with partner firstname/lastname fields
* Easy 3CX configuration with provided XML templates

Perfect for businesses using 3CX PBX who want to enhance their customer service 
by instantly accessing customer information during phone calls.
    """,
    'author': "FL1 sro",
    'website': "https://www.fl1.cz",
    'support': "support@fl1.cz",
    'category': 'Productivity/VoIP',
    'version': '18.0.1.0.0',
    'license': 'AGPL-3',
    'depends': ['base', 'crm', 'partner_firstname'],
    'external_dependencies': {
        'python': [],
    },
    'data': [
        # 'security/ir.model.access.csv',
        'data/data.xml',
    ],
    'images': [
        'static/description/banner.png',
        'static/description/icon.png',
        'static/description/images/git_3cx_lookup.gif',
        'static/description/images/3cx_conf1.png',
        'static/description/images/3cx_conf2.png',
        'static/description/images/3cx_conf3.png',
        'static/description/images/3cx_conf4.png',
        'static/description/images/3cx_conf5.png',
        'static/description/images/3cx_conf6.png',
        'static/description/images/3cx_conf7.png',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 0.0,
    'currency': 'EUR',
}
