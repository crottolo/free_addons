# -*- coding: utf-8 -*-

{
    'name': 'Web Font Awesome 5.3',
    'version': '16.0.0.0',
    'author': 'Exaly',
    'category': 'Productivity',
    'images': ['static/description/banner.png'],
    'summary': """Fontawesome resources. v5.3""",
    'depends': [
        'web',
    ],
    'assets': {
        'web.assets_common': [
            "exaly_font_awesome/static/src/css/fontawesome.css",
            "exaly_font_awesome/static/lib/fontawesome-5.3.1/css/all.css",
            "exaly_font_awesome/static/lib/fontawesome-5.3.1/css/v4-shims.css",
            "exaly_font_awesome/static/src/js/form_renderer.js",
            "exaly_font_awesome/static/src/js/list_renderer.js",
        ],
        'web.report_assets_common': [
            "exaly_font_awesome/static/lib/fontawesome-5.3.1/css/all.css",
            "exaly_font_awesome/static/lib/fontawesome-5.3.1/css/v4-shims.css",
        ]
    },
    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',
}
