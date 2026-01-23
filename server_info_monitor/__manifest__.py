{
    "name": "Server Info Monitor",
    "version": "18.0.1.0.0",
    "summary": "REST API endpoint to monitor Odoo instances with multi-database support",
    "description": """
Server Info Monitor
===================

A lightweight module that exposes server information via a secure REST API.
Perfect for DevOps dashboards, multi-instance monitoring, and automated health checks.
Now with full multi-database support for complex Odoo deployments.

Features
--------
* Multi-database support (query any database on the same instance)
* Server version information (Community/Enterprise detection)
* License monitoring with expiration tracking and renewal status
* User statistics (internal, portal, active, inactive with last activity)
* Module inventory with upgrade status and application flags
* Addons paths configuration

Endpoint
--------
GET /api/server/info

Authentication: Bearer token via Authorization header

Query Parameters:
* ?db=database_name - Specify target database (for multi-db instances)
* ?refresh=true - Refresh module list before returning

Alternative Database Selection:
* Header: X-Odoo-Database: database_name
* Fallback: Uses config db_name if not specified

Error Codes:
* 400: Database not specified (when no default available)
* 401: Invalid or missing token
* 404: Database not found
* 500: Internal server error

Configuration
-------------
Settings > Technical > System Parameters
Key: server_info_monitor.token
Default: srvmon_a7b3c9d2e5f8 (CHANGE IN PRODUCTION!)

Usage Examples
--------------
# Basic request (single database)
curl -H "Authorization: Bearer YOUR_TOKEN" https://your-odoo.com/api/server/info

# Multi-database via query param
curl -H "Authorization: Bearer YOUR_TOKEN" "https://your-odoo.com/api/server/info?db=production"

# Multi-database via header
curl -H "Authorization: Bearer YOUR_TOKEN" -H "X-Odoo-Database: production" https://your-odoo.com/api/server/info
    """,
    "author": "FL1 sro",
    "website": "https://fl1.cz",
    "support": "info@fl1.cz",
    "category": "Technical",
    "depends": ["base"],
    "data": [
        "data/ir_config_parameter.xml",
    ],
    "images": [
        "static/description/banner.png",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
