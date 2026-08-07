import base64
from datetime import datetime
from pathlib import Path

from odoo import fields
from odoo.tests import tagged

from odoo.addons.mail.tests.common import MailCommon

# Mittente reale di una ricevuta Aruba: l'allowlist e' confrontata come
# SOTTOSTRINGA, quindi il display name non deve disturbare il match.
PEC_SENDER = '"Per conto di: mittente@example.com" <posta-certificata@pec.aruba.it>'
ORDINARY_SENDER = "Mario Rossi <mario.rossi@example.com>"
# NON e' il catchall di MailCommon (catchall.test@test.mycompany.com): un
# indirizzo catchall verrebbe deviato da _detect_write_to_catchall.
EMAIL_TO = "ricevute@test.mycompany.com"
# Modello di RIPIEGO passato a message_process: se l'intercettazione non
# scatta, il core crea un res.partner (punto 3 di message_route). E' cio' che
# rende questi test capaci di fallire in modo pulito.
FALLBACK_MODEL = "res.partner"

# Header `Date:` scritto dentro pec_receipt.eml: "Fri, 10 Aug 2012 14:16:26
# +0000". L'offset e' +0000, quindi l'UTC naive che si aspetta un
# fields.Datetime coincide cifra per cifra con l'ora dell'header.
FIXTURE_DATE = datetime(2012, 8, 10, 14, 16, 26)

DATICERT_XML = (
    b'<?xml version="1.0" encoding="UTF-8"?>\n'
    b'<postacert tipo="accettazione" errore="nessuno">'
    b"<intestazione><mittente>mittente@example.com</mittente></intestazione>"
    b"</postacert>\n"
)


def _fixture(name):
    return (Path(__file__).parent / "fixtures" / name).read_text(encoding="utf-8")


@tagged("post_install", "-at_install")
class TestReceive(MailCommon):
    """Le ricevute PEC in ingresso vengono intercettate e atterrano INTATTE.

    Ogni test spinge un ``.eml`` grezzo attraverso l'INTERO gateway con
    ``MailCommon.format_and_process`` (odoo_core/odoo/addons/mail/tests/common.py
    L200-219), che chiama ``mail.thread.message_process(model, mail)``: e' il
    percorso reale, override di ``message_route`` compreso. Firma reale::

        format_and_process(self, template, email_from, to, subject='Frogs',
                           cc='', return_path='', extra='', msg_id=False,
                           model=None, target_model='mail.test.gateway',
                           target_field='name', with_user=None, **kwargs)

    ``target_model`` e' sempre esplicito: il default ``mail.test.gateway``
    appartiene a ``test_mail``, che qui non e' installato.

    Tutti i test passano ``model=res.partner`` come modello di ripiego. Senza
    l'intercettazione il messaggio finirebbe li' senza sollevare eccezioni, e
    le asserzioni su ``mailpec.mail`` fallirebbero in modo pulito.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.template = _fixture("pec_receipt.eml")
        cls.template_attachments = _fixture("pec_receipt_attachments.eml")

    def _process(
        self,
        template,
        email_from,
        subject,
        extra="",
        target_model="mailpec.mail",
    ):
        with self.mock_mail_gateway():
            return self.format_and_process(
                template,
                email_from,
                EMAIL_TO,
                subject=subject,
                extra=extra,
                model=FALLBACK_MODEL,
                target_model=target_model,
            )

    def test_allowlisted_sender_lands(self):
        """(a) Mittente in allowlist: nasce un solo mailpec.mail in stato ricevuta."""
        subject = "Ricevuta di accettazione"

        records = self._process(self.template, PEC_SENDER, subject)

        self.assertEqual(
            len(records),
            1,
            "un mittente in allowlist deve creare esattamente un mailpec.mail",
        )
        self.assertEqual(records.state, "ricevuta")
        # Il mittente si verifica sul mail.message postato dal gateway, NON sul
        # campo email_from del record: mailpec.mail non dichiara _primary_email,
        # quindi il core non lo popola (mail/models/models.py L112-118).
        self.assertIn(
            "posta-certificata@pec.aruba.it",
            records.message_ids.mapped("email_from")[0],
            "il messaggio deve conservare il mittente PEC",
        )
        # Il ripiego res.partner NON deve scattare: l'intercettazione ha la
        # precedenza sul punto 3 di message_route.
        self.assertFalse(
            self.env["res.partner"].search([("name", "=", subject)]),
            "l'intercettazione deve vincere sul modello di ripiego",
        )

    def test_non_allowlisted_sender_does_not_land(self):
        """(b) Mittente ordinario: nessun mailpec.mail, prosegue il routing normale."""
        subject = "Messaggio ordinario"

        partners = self._process(
            self.template,
            ORDINARY_SENDER,
            subject,
            target_model=FALLBACK_MODEL,
        )

        self.assertFalse(
            self.env["mailpec.mail"].search([("name", "=", subject)]),
            "un mittente non in allowlist non deve creare alcun mailpec.mail",
        )
        self.assertEqual(
            len(partners),
            1,
            "il messaggio deve proseguire sul routing del core (ripiego res.partner)",
        )

    def test_attachments_survive(self):
        """(c) Gli allegati sopravvivono: daticert.xml collegato e integro."""
        subject = "Ricevuta con allegati"

        records = self._process(self.template_attachments, PEC_SENDER, subject)

        self.assertEqual(len(records), 1, "deve nascere un solo mailpec.mail")
        attachments = self.env["ir.attachment"].search(
            [("res_model", "=", "mailpec.mail"), ("res_id", "=", records.id)],
        )
        self.assertEqual(
            sorted(attachments.mapped("name")),
            ["allegato.pdf", "daticert.xml"],
            "gli allegati devono restare collegati al mailpec.mail",
        )
        # Asserzione sul NOME e sul contenuto, MAI sul mimetype: il core forza
        # gli XML a text/plain (base/models/ir_attachment.py L376-381, perche'
        # mail_thread.py L1294 imposta attachments_mime_plainxml=True).
        daticert = attachments.filtered(lambda att: att.name == "daticert.xml")
        self.assertEqual(
            base64.b64decode(daticert.datas),
            DATICERT_XML,
            "daticert.xml deve arrivare byte per byte",
        )

    def test_pec_headers_captured(self):
        """(d) Header PEC catturati: pec_ref_message_id e pec_receipt_type popolati.

        E' il test piu' importante: quegli header sono l'unico legame verso il
        messaggio inviato, e ``message_parse`` ritorna chiavi FISSE
        (mail_thread.py L1705-1744), quindi possono essere catturati solo in
        ``message_route``, che ha ancora il ``message`` grezzo.
        """
        subject = "Ricevuta con header PEC"
        ref_message_id = "<original-msg-42@test.mycompany.com>"
        extra = (
            f"X-Riferimento-Message-ID: {ref_message_id}\nX-Ricevuta: avvenuta-consegna"
        )

        records = self._process(self.template, PEC_SENDER, subject, extra=extra)

        self.assertEqual(len(records), 1, "deve nascere un solo mailpec.mail")
        self.assertEqual(
            records.pec_ref_message_id,
            ref_message_id,
            "X-Riferimento-Message-ID deve popolare pec_ref_message_id",
        )
        self.assertEqual(
            records.pec_receipt_type,
            "avvenuta-consegna",
            "X-Ricevuta deve popolare pec_receipt_type",
        )

    def test_email_from_populated(self):
        """(e) email_from del record e' valorizzato con il mittente PEC.

        Il core popola email_from dal messaggio SOLO perche' il modello
        dichiara _primary_email = "email_from" (mail_thread.py L103). Senza
        quella dichiarazione _mail_get_primary_email_field ritorna None e il
        campo resta False: allora questa assertIn fallirebbe con
        ``TypeError: argument of type 'bool' is not iterable``.
        """
        subject = "Ricevuta con mittente"

        records = self._process(self.template, PEC_SENDER, subject)

        self.assertEqual(len(records), 1, "deve nascere un solo mailpec.mail")
        self.assertIn(
            "posta-certificata@pec.aruba.it",
            records.email_from,
            "email_from deve contenere il mittente PEC",
        )

    def test_date_received_is_message_date(self):
        """(f) date_received e' la data della RICEVUTA, non quella di ingestione.

        La ricevuta ha valore legale: il riferimento temporale deve essere
        l'header Date: del messaggio. Con fields.Datetime.now() un cron fermo
        un giorno, o un reimport di .eml archiviati, timbrerebbe tutto a oggi.

        La fixture porta una data del 2012, quindi l'asserzione e' capace di
        fallire: e' proprio il divario con "adesso" a rendere il test una prova.
        """
        subject = "Ricevuta datata 2012"

        records = self._process(self.template, PEC_SENDER, subject)

        self.assertEqual(len(records), 1, "deve nascere un solo mailpec.mail")
        self.assertEqual(
            records.date_received,
            FIXTURE_DATE,
            "date_received deve valere l'header Date: della ricevuta",
        )
        self.assertNotEqual(
            records.date_received.date(),
            fields.Datetime.now().date(),
            "date_received non deve essere l'istante di ingestione",
        )
