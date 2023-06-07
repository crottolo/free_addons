# -*- coding: utf-8 -*-
{
    'name': 'Attachment Preview',
    'version': '15.0.1',
    'category': 'Services/Tools',
    'author': 'Odox SoftHub',
    'website': 'https://www.odoxsofthub.com',
    'support': 'support@odoxsofthub.com',
    'sequence': 2,
    'summary': """This module adds a new widget, many2many_attachment_preview, which enables the user to view attachments without downloading them.""",
    'description': """ User can preview a document without downloading. """,
    'depends': [],
    'data': [
    ],
    'assets': {
        'web.assets_backend': [
            '/odx_m2m_attachment_preview/static/src/js/odx_document_viewer_legacy.js',
            '/odx_m2m_attachment_preview/static/src/js/odx_many2many_attachment_preview.js',
        ],
        'web.assets_qweb': [
            'odx_m2m_attachment_preview/static/src/xml/odx_document_viewer_legacy.xml',
            'odx_m2m_attachment_preview/static/src/xml/odx_many2many_attachment_preview.xml',
        ],
    },
    'license': 'LGPL-3',
    'application': True,
    'installable': True,
    'images': ['static/description/thumbnail.gif'],
}
