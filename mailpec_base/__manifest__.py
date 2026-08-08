{
    "name": "PEC - Invio e Ricezione",
    "summary": "Gestione caselle PEC: envelope sender corretto in invio e ricezione ricevute",
    "description": """
Gestione delle caselle PEC (Posta Elettronica Certificata) in Odoo 18.

Invio: forza l'envelope sender all'indirizzo PEC autenticato ed esclude i
server PEC dalla selezione automatica per la posta ordinaria.

Ricezione: intercetta i messaggi dei gestori, li fa atterrare INTATTI su
mailpec.mail, interpreta daticert.xml, distingue ricevute, messaggi PEC e posta
non certificata, e li correla al messaggio inviato.

Operativita': elenco di triage con la controparte reale al posto dell'indirizzo
del gestore, oggetto senza prefissi, evidenza delle non lette e degli errori
certificati; il corpo del messaggio umano e' estratto da postacert.eml in una
pagina dedicata.

Modulo generico e indipendente dal cliente: non conosce pratiche ne' modelli di
business, si aggancia via origin_model / origin_res_id.
    """,
    "author": "Persevida S.L.",
    "contributors": [
        "https://persevida.com",
        "Persevida S.L.",
    ],
    "website": "https://singleflo.com",
    "maintainer": "Singleflo",
    "version": "18.0.1.11.0",
    "installable": True,
    "auto_install": False,
    "application": False,
    "license": "LGPL-3",
    "category": "Productivity/Discuss",
    # Obbligatoria per un SVG: get_module_icon_path cerca SOLO icon.png
    # (odoo/modules/module.py L248-252) e senza questa chiave Odoo ripiega
    # sull'icona generica. Dichiarandola, _get_icon_image usa questo percorso
    # e file_open accetta .svg (base/models/ir_module.py L280).
    "icon": "/mailpec_base/static/description/icon.svg",
    "depends": ["mail"],
    "data": [
        "security/mailpec_security.xml",
        "security/ir.model.access.csv",
        "data/mailpec_data.xml",
        "views/ir_mail_server_views.xml",
        "views/fetchmail_server_views.xml",
        "views/mailpec_mail_views.xml",
    ],
}
