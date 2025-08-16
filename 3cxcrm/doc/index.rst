==================
3CX CRM Integration
==================

.. |badge1| image:: https://img.shields.io/badge/maturity-Production-green.png
    :target: https://odoo-community.org/page/development-status
    :alt: Production
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-FL1--sro%2F3cxcrm-lightgray.png?logo=github
    :target: https://github.com/crottolo/free_addons/tree/main/3cxcrm
    :alt: FL1-sro/3cxcrm

|badge1| |badge2| |badge3|

Automatically identify incoming callers in your 3CX PBX system by integrating with Odoo CRM database. Display complete customer information directly in your phone interface, eliminating the need to search for caller details during conversations.

**Table of contents**

.. contents::
   :local:

Overview
========

The 3CX CRM Integration module creates a seamless connection between your 3CX PBX phone system and Odoo CRM, providing instant caller identification and access to customer information during incoming calls.

Key Features
------------

* **Real-time Phone Lookup**: Automatically searches Contacts and CRM Leads when calls arrive
* **Instant Caller Identification**: Displays caller name, company, email, and contact details
* **Direct Record Access**: One-click links to open complete customer records in Odoo
* **Secure API Communication**: Protected REST endpoint with configurable authentication
* **Dual Database Search**: Searches both res.partner (Contacts) and crm.lead (Leads/Opportunities)
* **Complete Contact Support**: Works with individual contacts and company records
* **Firstname/Lastname Integration**: Full support for partner_firstname module fields

Installation
============

Prerequisites
-------------

Before installing this module, ensure you have:

1. **Odoo Requirements**:
   - Odoo 18.0 or higher
   - CRM module installed and configured
   - Partner Firstname module from OCA (https://github.com/OCA/partner-contact)

2. **3CX Requirements**:
   - 3CX Phone System v16 or higher
   - CRM integration feature enabled
   - Administrative access to 3CX Management Console
   - Network connectivity from 3CX server to Odoo instance

Module Installation
-------------------

1. Download the module from Odoo Apps Store or GitHub repository
2. Install the module in your Odoo instance
3. The module will automatically:
   - Create the REST API endpoint ``/api/3cx/crm``
   - Configure default API authentication token
   - Enable CRM lead functionality in settings

Configuration
=============

Odoo Configuration
------------------

1. **Set API Authentication Key**:
   
   Navigate to *Settings → Technical → System Parameters* and modify:
   
   - **Key**: ``crm.3cx.auth``
   - **Value**: Your secure API key (replace default "123A" with a strong key)

2. **Verify CRM Settings**:
   
   Go to *CRM Settings* and ensure "Leads" are enabled if you want to search lead records.

3. **Test API Endpoint**:
   
   The API endpoint is available at: ``https://your-odoo-domain.com/api/3cx/crm``

3CX Configuration
-----------------

1. **Download Configuration File**:
   
   Use the provided XML configuration file from the module directory:
   ``upload_on_3cx_pbx/3cx_odoo_v20.xml``

2. **Upload to 3CX**:
   
   - Open 3CX Management Console
   - Go to *Settings → CRM Integration*
   - Click "Add" and select "Upload from file"
   - Choose the ``3cx_odoo_v20.xml`` file

3. **Configure Connection Parameters**:
   
   - **ApiKey**: Enter the same API key you set in Odoo system parameters
   - **Host odoo**: Your Odoo server URL (e.g., ``https://your-odoo-domain.com``)
   - **Country**: Your country code (IT, US, etc.)

Configuration Screenshots
^^^^^^^^^^^^^^^^^^^^^^^^^

The module includes detailed 3CX configuration screenshots in the ``static/description/images/`` directory showing each step of the setup process.

Usage
=====

Automatic Caller Lookup
------------------------

Once configured, the integration works automatically:

1. **Incoming Call Received**: When a call arrives at your 3CX system
2. **API Request Sent**: 3CX sends the caller's phone number to Odoo via the REST API
3. **Database Search**: Odoo searches both Contacts and CRM Leads for matching phone numbers
4. **Results Displayed**: Caller information appears in the 3CX interface
5. **Direct Access**: Click the provided link to open the customer record in Odoo

Search Priority
---------------

The module searches in this order:

1. **Contacts (res.partner)**: Searches mobile and phone fields using ``phone_mobile_search``
2. **CRM Leads (crm.lead)**: Searches leads and opportunities if no contact found
3. **New Number Flag**: Returns "new_number: true" if no records found

Displayed Information
---------------------

For **Contacts**:
- Partner ID and type
- First name and last name (if using partner_firstname)
- Mobile and phone numbers
- Email address
- Company name (for company type records)
- Direct link to open contact form in Odoo

For **CRM Leads**:
- Lead ID (prefixed with 'L')
- Lead type (lead or opportunity)
- Contact name and lead name
- Mobile and phone numbers
- Direct link to open lead form in Odoo

API Reference
=============

Endpoint Details
----------------

**URL**: ``/api/3cx/crm``
**Method**: POST
**Authentication**: API Key in header
**Content-Type**: application/json

Request Format
^^^^^^^^^^^^^^

.. code-block:: json

   {
     "number": "+1234567890"
   }

Headers:

.. code-block:: http

   apikey: your-configured-api-key
   Content-Type: application/json

Response Formats
^^^^^^^^^^^^^^^^

**Contact Found**:

.. code-block:: json

   {
     "partner_id": "123",
     "type": "contact",
     "firstname": "John",
     "lastname": "Smith", 
     "mobile": "+1234567890",
     "phone": "+1234567891",
     "email": "john.smith@example.com",
     "web_url": "https://your-odoo.com/web#id=123&model=res.partner&view_type=form&action=123",
     "company_type": "person",
     "name": "John Smith"
   }

**Lead Found**:

.. code-block:: json

   {
     "partner_id": "L456",
     "type": "lead",
     "name": "John Smith",
     "contact_name": "New Business Inquiry",
     "mobile": "+1234567890", 
     "phone": "+1234567891",
     "web_url": "https://your-odoo.com/web#id=456&model=crm.lead&view_type=form&action=789",
     "link_end": "link_end"
   }

**No Match Found**:

.. code-block:: json

   {
     "new_number": true
   }

Security Implementation
=======================

Authentication
--------------

The module implements secure API authentication:

- **API Key Validation**: All requests must include valid API key in header
- **Public Endpoint**: Uses ``auth='public'`` but enforces API key validation
- **CSRF Protection**: Disabled for API endpoint (``csrf=False``)
- **Sudo Access**: Uses ``sudo()`` for database queries to ensure consistent access

Error Handling
--------------

- **Missing API Key**: Returns ``BadRequest('ApiKey not set')``
- **Invalid API Key**: Returns ``BadRequest('Wrong APIKEY')``
- **JSON Parsing**: Handles malformed request data gracefully
- **Database Errors**: Proper exception handling for database access

Data Privacy
------------

- **Minimal Data Exposure**: Only returns essential contact information
- **No Sensitive Data**: Passwords, internal notes, and private fields are excluded
- **Controlled Access**: API only accessible with valid authentication

Known Issues / Roadmap
=======================

Current Limitations
-------------------

- **Phone Number Matching**: Uses ``ilike`` search which may match partial numbers
- **Single Result**: Returns only the first matching record per search type
- **No Call Logging**: Incoming call events are not logged in Odoo
- **Limited Country Support**: Phone number formatting depends on 3CX configuration

Planned Enhancements
--------------------

- **Enhanced Phone Matching**: Improve phone number normalization and matching
- **Call History Integration**: Log incoming/outgoing calls in customer records
- **Multiple Result Handling**: Support for multiple matches with selection interface
- **Advanced Search Options**: Search by company name, email, or other fields
- **Webhook Integration**: Real-time sync of contact changes

Troubleshooting
===============

Common Issues
-------------

**No Caller Information Displayed**

1. Check API key configuration in both Odoo and 3CX
2. Verify network connectivity between 3CX and Odoo servers
3. Test API endpoint manually with curl or Postman
4. Check Odoo logs for authentication or database errors

**Wrong Contact Information**

1. Verify phone number format consistency between 3CX and Odoo
2. Check if multiple contacts have similar phone numbers
3. Review ``phone_mobile_search`` field content in database

**3CX Configuration Issues**

1. Ensure 3CX version supports CRM integration
2. Verify XML configuration file uploaded correctly
3. Check 3CX logs for API request errors
4. Confirm firewall allows outbound HTTPS connections

Testing the Integration
-----------------------

**Manual API Test**:

.. code-block:: bash

   curl -X POST https://your-odoo.com/api/3cx/crm \
     -H "Content-Type: application/json" \
     -H "apikey: your-api-key" \
     -d '{"number": "+1234567890"}'

**Expected Response**: JSON with contact information or ``{"new_number": true}``

Debugging Steps
---------------

1. **Enable Developer Mode** in Odoo to access technical features
2. **Check System Parameters** for correct API key configuration
3. **Review Server Logs** for API request details and errors
4. **Test Phone Number Search** manually in Odoo contact/lead lists
5. **Verify 3CX Logs** for outbound API request status

Changelog
=========

18.0.1.0.0 (2024-12-XX)
------------------------

* **New**: Updated module name to "3CX CRM Integration"
* **New**: Enhanced manifest with complete store metadata
* **New**: Professional HTML description for Odoo Apps Store
* **New**: Comprehensive RST documentation with API reference
* **New**: Security access file for proper module permissions
* **Improvement**: Updated version to standard Odoo 18.0 format
* **Improvement**: Added external dependencies validation
* **Improvement**: Enhanced error handling and response formatting
* **Fix**: Corrected manifest dependencies and data file loading

18.0.0.1 (Previous)
-------------------

* **Initial**: Basic 3CX CRM lookup functionality
* **Initial**: REST API endpoint for phone number queries
* **Initial**: Contact and lead search capabilities
* **Initial**: 3CX XML configuration files
* **Initial**: Basic authentication and security

Credits
=======

Authors
-------

* FL1 sro

Contributors
------------

* Roberto Crotti <bo@fl1.cz>

Maintainers
-----------

This module is maintained by FL1 sro.

.. image:: https://fl1.cz/web/image/website/7/logo/FL1?unique=d1f5119
   :alt: FL1 sro
   :target: https://www.fl1.cz
   :width: 100px

FL1 sro specializes in Odoo implementation and 3CX PBX integration solutions.

Support
-------

* **Email Support**: support@fl1.cz
* **Website**: https://www.fl1.cz
* **GitHub Issues**: https://github.com/crottolo/free_addons/issues

For professional support, custom development, or enterprise implementations, 
please contact FL1 sro directly.

License
-------

This module is licensed under AGPL-3.

You are free to use, modify, and distribute this software under the terms 
of the GNU Affero General Public License version 3.