from odoo.tests import TransactionCase, tagged

from odoo.addons.base.tests.common import MockSmtplibCase

ALIAS_DOMAIN = "test-mailpec.example.com"
BOUNCE_ADDRESS = f"bounce@{ALIAS_DOMAIN}"
EMAIL_FROM = f"mittente@{ALIAS_DOMAIN}"
EMAIL_TO = "destinatario@example.com"
PEC_ADDRESS = "azienda@pec-mailpec.example.com"


@tagged("post_install", "-at_install")
class TestSend(TransactionCase, MockSmtplibCase):
    """Verifica l'envelope sender SMTP, NON l'header Return-Path.

    L'header viene scritto comunque da ``_prepare_outgoing_list``, quindi
    asserire su di esso non prova nulla. Cio' che il gestore PEC controlla e'
    il MAIL FROM di busta, calcolato in ``_prepare_email_message``
    (base/models/ir_mail_server.py L651 e L699) dove il context
    ``domain_bounce_address`` ha la precedenza sull'header.
    In test mode il core cortocircuita l'invio (connect() torna None,
    ir_mail_server.py L397-399 e L762-764): ``mock_smtplib_connection``
    ripristina il percorso reale e cattura lo ``smtp_from`` passato a
    ``send_message``.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.alias_domain = cls.env["mail.alias.domain"].create(
            {
                "name": ALIAS_DOMAIN,
                "bounce_alias": "bounce",
                "catchall_alias": "catchall",
                "default_from": "notifications",
            },
        )
        server_values = {"smtp_host": "smtp_host", "smtp_encryption": "none"}
        # PEC senza from_filter e con sequence bassa: senza il filtro in
        # _find_mail_server intercetterebbe tutta la posta ordinaria
        # (ir_mail_server.py L834-835).
        cls.pec_catchall = cls.env["ir.mail_server"].create(
            {
                "name": "PEC catch-all",
                "sequence": 1,
                "from_filter": False,
                "is_pec": True,
                "pec_email_from": PEC_ADDRESS,
                **server_values,
            },
        )
        cls.pec_server = cls.env["ir.mail_server"].create(
            {
                "name": "PEC",
                "sequence": 2,
                "from_filter": PEC_ADDRESS,
                "is_pec": True,
                "pec_email_from": PEC_ADDRESS,
                **server_values,
            },
        )
        # Server ordinario con pec_email_from valorizzato ma is_pec=False:
        # prova che il campo da solo non deve cambiare nulla.
        cls.std_server = cls.env["ir.mail_server"].create(
            {
                "name": "Ordinario",
                "sequence": 3,
                "from_filter": ALIAS_DOMAIN,
                "is_pec": False,
                "pec_email_from": PEC_ADDRESS,
                **server_values,
            },
        )

    def _create_mail(self, server):
        return self.env["mail.mail"].create(
            {
                "email_from": EMAIL_FROM,
                "email_to": EMAIL_TO,
                "subject": "test envelope",
                "body_html": "<p>test</p>",
                "mail_server_id": server.id,
                # record_alias_domain_id attiva il context domain_bounce_address
                # (mail_mail.py L738-744), la ragione per cui non basta l'header.
                "record_alias_domain_id": self.alias_domain.id,
            },
        )

    def _send_and_capture(self, mail):
        with self.mock_smtplib_connection():
            mail.send(raise_exception=True)
        self.assertEqual(len(self.emails), 1, "deve partire una sola email")
        return self.emails[0]

    def test_pec_envelope_sender(self):
        """(a) Server PEC: il MAIL FROM di busta e' l'indirizzo PEC."""
        mail = self._create_mail(self.pec_server)

        sent = self._send_and_capture(mail)

        self.assertEqual(
            sent["smtp_from"],
            PEC_ADDRESS,
            "l'envelope sender deve essere la casella PEC autenticata",
        )
        self.assertNotEqual(sent["smtp_from"], BOUNCE_ADDRESS)
        # L'header From resta quello applicativo: se coincidesse con
        # l'envelope l'asserzione precedente non discriminerebbe.
        self.assertEqual(sent["msg_from"], EMAIL_FROM)

    def test_standard_envelope_sender_unchanged(self):
        """(b) Server non PEC: comportamento core, envelope = bounce address."""
        mail = self._create_mail(self.std_server)

        sent = self._send_and_capture(mail)

        self.assertEqual(sent["smtp_from"], BOUNCE_ADDRESS)
        self.assertNotEqual(sent["smtp_from"], PEC_ADDRESS)

    def test_find_mail_server_excludes_pec(self):
        """(c) _find_mail_server non restituisce mai un server PEC.

        Mirror di mail_mail.py L574-585: il recordset arriva posizionale e
        gia' valorizzato.
        """
        mail_servers = self.pec_catchall + self.pec_server + self.std_server

        server, _email_from = self.env["ir.mail_server"]._find_mail_server(
            EMAIL_FROM,
            mail_servers,
        )

        self.assertFalse(server.is_pec, "selezionato un server PEC")
        self.assertEqual(server, self.std_server)
