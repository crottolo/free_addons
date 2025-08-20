====================================
Company Favicon & PWA Customizer
====================================

.. |badge1| image:: https://img.shields.io/badge/maturity-Production-green.png
    :target: https://odoo-community.org/page/development-status
    :alt: Production
.. |badge2| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge3| image:: https://img.shields.io/badge/price-€13.00-brightgreen.svg
    :target: https://apps.odoo.com/apps/modules/18.0/webapp_customizer/
    :alt: Price €13.00

|badge1| |badge2| |badge3|

Transform your Odoo with professional favicon and PWA icon customization. This module provides comprehensive branding solutions for multi-company environments and Progressive Web App installations.

**Table of Contents**

.. contents::
   :local:

Features
========

🏢 Company-Specific Favicons
----------------------------

* **Unique Branding**: Set different favicons for each company in multi-company environments
* **Automatic Color-Coding**: New companies get unique color-coded default favicons automatically
* **Dynamic Switching**: Favicon automatically changes when switching between companies
* **Multi-Company Support**: Perfect for distinguishing business units, subsidiaries, or different brands
* **Browser Integration**: Works with all favicon-related elements (tabs, bookmarks, shortcuts)

📱 Progressive Web App Icons
----------------------------

* **Custom PWA Icons**: Upload custom icons for Progressive Web App installations
* **Multi-Resolution Support**: Automatically generates 192x192 and 512x512 pixel versions
* **Professional Installation**: Users see your custom branding during PWA installation
* **Mobile Optimization**: Enhanced experience on mobile devices and tablets
* **Native Integration**: Seamlessly works with Odoo 18's built-in PWA system

⚡ Technical Benefits
--------------------

* **Easy Configuration**: Simple setup through familiar Settings interface
* **Clean Architecture**: Separate company favicons from global PWA icons
* **Performance Optimized**: Efficient caching and image processing
* **Enterprise Ready**: Full support for complex multi-company setups
* **Automatic Fallbacks**: Graceful degradation if custom icons aren't configured

Installation
============

Requirements
------------

* **Odoo Version**: 18.0 or higher
* **Python Dependencies**: Pillow (included with standard Odoo installation)
* **Browser Support**: All modern browsers (Chrome, Firefox, Safari, Edge)
* **PWA Compatibility**: Full PWA support in supported browsers

Installation Steps
------------------

1. **Download Module**: Purchase and download from Odoo Apps Store
2. **Upload to Server**: Copy module to your Odoo addons directory
3. **Update Module List**: Go to Apps → Update Apps List
4. **Install Module**: Search for "Company Favicon & PWA Customizer" and click Activate

.. code-block:: bash

   # Alternative: Install via command line
   python odoo-bin -c config.conf -d database -i webapp_customizer

Configuration
=============

Progressive Web App Icon Setup
-------------------------------

1. **Access Settings**:
   
   * Navigate to Settings from your Odoo home screen
   * Click on "General Settings" tab

2. **Configure PWA Icon**:
   
   * Scroll to "Progressive Web App" section
   * Click on the "PWA Icon" field
   * Upload your custom icon (recommended: PNG format, 512x512 pixels)
   * Click "Save"

.. note::
   The PWA icon will be automatically resized to 192x192 and 512x512 pixels for optimal compatibility across devices.

Company Favicon Configuration
-----------------------------

1. **Navigate to Companies**:
   
   * Go to Settings → Users & Companies → Companies
   * Select the company you want to customize

2. **Upload Company Favicon**:
   
   * Scroll to the "Company Favicon" field
   * Upload your favicon image (ICO, PNG, or JPG format recommended)
   * Save the company record

3. **Verify Configuration**:
   
   * Switch between companies to see the favicon change automatically
   * Check browser tabs and bookmarks for the new favicon

Usage
=====

Daily Operations
----------------

**Automatic Favicon Switching**:
When working in multi-company environments, the favicon automatically updates when you switch companies, providing immediate visual feedback about your current context.

**PWA Installation**:
When users install your Odoo as a Progressive Web App:

1. Browser displays installation prompt with your custom icon
2. App appears on device home screen with your branding
3. System app list shows your custom icon and name

**New Company Setup**:
When creating new companies:

1. System automatically generates a unique color-coded favicon
2. Each company gets a distinct visual identifier
3. You can later customize with company-specific branding

Multi-Company Scenarios
-----------------------

**Business Units**:
- Different divisions can have unique favicons
- Easy visual distinction between operational units
- Consistent branding across all touchpoints

**White-Label Solutions**:
- Service providers can brand Odoo for each client
- Custom PWA icons for professional mobile installations
- Client-specific favicons for web access

Best Practices
==============

Image Specifications
--------------------

**PWA Icons**:
* **Format**: PNG (recommended)
* **Size**: 512x512 pixels (optimal)
* **Quality**: High resolution for crisp display
* **Design**: Simple, recognizable symbol
* **Background**: Solid color or transparent

**Company Favicons**:
* **Format**: ICO, PNG, or JPG
* **Size**: 16x16, 32x32, or 64x64 pixels
* **File Size**: Under 100KB recommended
* **Design**: Simple, company-representative icon

Configuration Tips
------------------

1. **Consistent Branding**: Use similar color schemes between PWA icons and company favicons
2. **Testing**: Test favicon visibility across different browsers and devices
3. **Backup**: Keep original high-resolution images for future updates
4. **Documentation**: Maintain records of which companies use which favicons

Troubleshooting
===============

Common Issues
-------------

**Favicon Not Appearing**
* Clear browser cache and cookies
* Check if favicon file was uploaded correctly
* Ensure file format is supported (ICO, PNG, JPG)
* Verify company favicon field is not empty

**PWA Icon Not Showing**
* Confirm PWA icon is uploaded in Settings
* Check file format (PNG recommended)
* Verify browser PWA support
* Test PWA installation process

**Company Switching Issues**
* Check JavaScript console for errors
* Verify module assets are loaded correctly
* Confirm company switching functionality works
* Test with different browsers

**Performance Issues**
* Optimize image file sizes (under 100KB for favicons)
* Check server caching configuration
* Monitor browser network requests

Technical Details
-----------------

**Storage Locations**:
* Company favicons: Stored in res.company model
* PWA icons: Stored as ir.attachment records
* Default favicons: Generated automatically with unique colors

**Caching Behavior**:
* Browser-side caching with appropriate headers
* Server-side optimization for repeated requests
* Automatic cache busting when images change

**JavaScript Integration**:
* Real-time favicon updates without page refresh
* Integration with Odoo's company switching mechanism
* Fallback handling for missing favicons

Known Issues / Roadmap
======================

Current Limitations
-------------------

* PWA icon changes require new PWA installation to take effect
* Some older browsers may have limited favicon format support
* Large favicon files may impact initial page load time

Planned Enhancements
--------------------

* **v18.0.2.0.0**: Bulk favicon management interface
* **v18.0.3.0.0**: Favicon preview in company selection
* **Future**: Integration with theme customization
* **Future**: Automatic favicon generation from company logos

Bug Reports
-----------

For bug reports and feature requests, please contact FL1 sro support team.

Credits
=======

Authors
-------

* FL1 sro

Contributors
------------

* Development Team at FL1 sro
* Beta testers from the Odoo community

Maintainers
-----------

This module is maintained by FL1 sro.

.. image:: https://fl1.cz/logo.png
   :alt: FL1 sro
   :target: https://fl1.cz

FL1 sro specializes in Odoo customization and provides professional support for complex multi-company environments.

Support
=======

For technical support, customization requests, or questions about this module:

* **Website**: https://fl1.cz
* **Email**: Contact through website form

License
=======

This module is licensed under LGPL-3.

Changelog
=========

18.0.1.0.0 (2025-08-20)
-----------------------

**Added**
* Initial release
* Company-specific favicon support
* Progressive Web App icon customization
* Automatic color-coded default favicons
* Dynamic favicon switching
* Multi-company environment support
* Integration with Odoo 18 PWA system
* Comprehensive documentation
* Professional store listing

**Technical Features**
* WebManifest controller inheritance
* Efficient image processing with Pillow
* Automatic image resizing (192x192, 512x512)
* JavaScript-based favicon switching
* Proper HTTP caching headers
* Fallback mechanisms for missing icons