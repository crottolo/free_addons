# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Signup Address Fields',
    'description': """ Signup Address Fields """,
    'summary': """ Signup Address Fields """,
    'category': 'Website',
    'version': '18.0.0.1',
    'author': 'Bizople Solutions Pvt. Ltd.',
    'website': 'https://www.bizople.com/',
    'depends': [
        'portal'    
    ],
    'data': [
        'views/auth_signup_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'signup_address_fields_fl1/static/src/js/auth_signup.js',
            'signup_address_fields_fl1/static/src/scss/auth_signup.scss',
        ],
    },
    'images': [
        'static/description/banner.png'
    ],
    'installable': True,
    'application': True,
    'license': 'OPL-1',
}
