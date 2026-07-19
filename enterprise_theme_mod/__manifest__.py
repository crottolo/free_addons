{
    "name": "Odoo Enterprise Theme",
    "version": "18.0.0.3",
    "summary": "Odoo Enterprise Theme",
    "author": "Persevida S.L.",
    "contributors": [
        "https://persevida.com",
        "Persevida S.L.",
    ],
    "license": "AGPL-3",
    "maintainer": "Singleflo",
    "company": "Persevida S.L.",
    "website": "https://singleflo.com",
    "depends": [
        "web",
    ],
    "category": "Branding",
    "description": """
           Odoo Enterprise Theme
    """,
    "assets": {
        "web._assets_primary_variables": [
            "/enterprise_theme_mod/static/src/scss/primary_variables_custom.scss",
        ],
        "web.assets_common": [
            "/enterprise_theme_mod/static/src/scss/fields_extra_custom.scss",
        ],
        "web._assets_secondary_variables": [
            "/enterprise_theme_mod/static/src/scss/secondary_variables.scss",
        ],
    },
    "price": 0,
    "currency": "EUR",
    "installable": True,
    "auto_install": False,
    "application": True,
    "images": ["static/description/icon.png"],
}
