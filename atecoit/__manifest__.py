{
    "name": "Gestione e aggiornamento codici Ateco",
    "summary": """
        Gestione e aggiornamento automatico dei codici Ateco
    """,
    "description": """
        Questo modulo estende le funzionalità di Odoo per la gestione dei codici Ateco direttamente dalla repository ufficiale italiana
        https://github.com/italia/daf-ontologie-vocabolari-controllati/tree/master/VocabolariControllati/classifications-for-organizations/ateco-2007
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
    "category": "Services",
    "images": ["images/main_screenshot.png"],
    "depends": ["base", "contacts"],
    "external_dependencies": {
        "python": [],
    },
    "data": [
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/atecoit_category.xml",
        "views/res_partner.xml",
    ],
    "assets": {
        "web.assets_backend": [],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "post_init_hook": "post_init_hook",
}
