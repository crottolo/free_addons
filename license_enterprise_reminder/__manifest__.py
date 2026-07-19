{
    "name": "License Enterprise Reminder",
    "summary": """
        Update reminder for enterprise license from 30 days to 60 days
        """,
    "description": """
        Update reminder for enterprise license from 30 days to 60 days
    """,
    "author": "Persevida S.L.",
    "contributors": [
        "https://persevida.com",
        "Persevida S.L.",
    ],
    "website": "https://singleflo.com",
    "maintainer": "Singleflo",
    "version": "18.0.0.1",
    "installable": True,
    "auto_install": False,
    "application": False,
    "license": "LGPL-3",
    "category": "Administration",
    "depends": ["base", "web_enterprise"],
    "assets": {
        "web.assets_backend": [
            "license_enterprise_reminder/static/src/js/enterprise_subscription_service.js",
        ],
    },
}
