{
    "name": "Italian EDI - SDI Notifications",
    "summary": "Automated daily summary of Italian electronic invoicing (SDI) issues",
    "description": """
Italian EDI - SDI Notifications
===============================

This module automatically sends a daily summary to a configured Odoo Discuss channel,
highlighting all invoices with SDI (Sistema di Interscambio) related issues.

Main Features:
--------------
* Automated daily report in Discuss channel
* Monitoring of invoices requiring signature
* Monitoring of invoices rejected by SDI
* Monitoring of invoices rejected by PA partner
* Monitoring of unsent self-invoices (reverse charge)
* Dedicated filters in invoice list
* SDI State column visible by default
* Optional email to fallback user
* Optional automatic activity creation
* Multi-company support

Configuration:
--------------
Settings > Accounting > Electronic Invoicing > SDI Notifications
    """,
    "author": "Persevida S.L.",
    "contributors": [
        "https://persevida.com",
        "Persevida S.L.",
    ],
    "website": "https://singleflo.com",
    "maintainer": "Singleflo",
    "support": "support@singleflo.com",
    "version": "18.0.2.1.0",
    "installable": True,
    "auto_install": False,
    "application": False,
    "license": "LGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_it_edi", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/mail_channel.xml",
        "data/mail_activity_type.xml",
        "data/ir_cron.xml",
        "data/sdi_report_template.xml",
        "views/account_move_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "images": [
        "static/description/banner.png",
        "static/description/01_channel_daily_report.png",
        "static/description/02_invoice_filters.png",
        "static/description/03_invoice_list_sdi_column.png",
        "static/description/04_settings_configuration.png",
    ],
}
