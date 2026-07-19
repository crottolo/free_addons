{
    "name": "ABI e CAB per Banche Italiane",
    "summary": """
        Gestione e aggiornamento automatico dei codici ABI e CAB delle banche italiane
    """,
    "description": """
        Questo modulo estende le funzionalità di Odoo per la gestione delle banche italiane, aggiungendo i campi ABI e CAB.
    """,
    "author": "Persevida S.L.",
    "contributors": [
        "https://persevida.com",
        "Persevida S.L.",
    ],
    "website": "https://singleflo.com",
    "maintainer": "Singleflo",
    "version": "18.0.0.1",
    "license": "LGPL-3",
    "category": "Accounting/Localizations",
    "images": ["images/main_screenshot.png"],
    "depends": ["base", "account", "contacts"],
    "external_dependencies": {
        "python": ["schwifty"],
    },
    "data": [
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/abicab.xml",
    ],
    "assets": {},
    "installable": True,
    "application": False,
    "auto_install": False,
}
