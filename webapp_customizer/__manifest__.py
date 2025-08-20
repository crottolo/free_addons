# -*- coding: utf-8 -*-
{
    'name': "Company Favicon & PWA Customizer",

    'summary': "Company-specific favicons and Progressive Web App icon customization for enhanced branding",

    'description': """
        Company Favicon & PWA Customizer
        ================================
        
        Transform your Odoo with professional favicon and PWA icon customization.
        
        🏢 **Company-Specific Favicons**
        - Unique favicons for each company in multi-company environments
        - Automatic color-coded default favicons for new companies
        - Dynamic favicon switching when changing companies
        - Perfect for distinguishing business units and subsidiaries
        
        📱 **Progressive Web App Icons**
        - Custom PWA icons for professional mobile installations
        - Automatic resizing (192x192, 512x512) for optimal compatibility
        - Seamless integration with Odoo 18's native PWA system
        - Enhanced user experience on mobile devices
        
        ⚡ **Key Benefits**
        - Easy configuration through Settings interface
        - Clean separation: company favicons vs global PWA icons
        - Automatic fallback to default favicons
        - Performance optimized with proper caching
        - Enterprise-ready with full multi-company support
        
        Perfect for multi-company organizations, branding-conscious businesses, 
        and service providers offering white-label Odoo solutions.
    """,

    'author': "FL1 sro",
    'website': "https://fl1.cz",
    'maintainer': 'FL1 sro',
    'version': '18.0.1.0.0',
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'OPL-1',
    'category': 'Customizations',
    
    # Odoo Apps Store specific fields
    'price': 13.00,
    'currency': 'EUR',
    'live_test_url': '',
    'support': 'https://fl1.cz',
    
    # Images for store listing
    'images': [
        'static/description/03_pwa_icon_settings.png',
        'static/description/01_module_activation.png',
        'static/description/02_settings_access.png', 
        'static/description/04_companies_menu.png',
        'static/description/05_company_favicon_field.png',
        'static/description/06_pwa_installation.png',
        'static/description/icon.png',
    ],

    # Dependencies
    'depends': ['base', 'web', 'base_setup'],
    'external_dependencies': {
        'python': ['Pillow'],
    },

    # Module data files
    'data': [
        'views/res_company_views.xml',
        'views/res_config_settings_views.xml',
    ],
    
    'demo': [
        # 'demo/demo.xml',
    ],
    
    'assets': {
        'web.assets_backend': [
            'webapp_customizer/static/src/js/favicon.js',
        ],
    },
}