"""I tre criteri che portano un messaggio su ``mailpec.mail``.

Fino alla v1.5 il criterio era UNO SOLO, il mittente ``posta-certificata@``.
L'Allegato tecnico al DM 2 novembre 2005 lo prescrive pero' solo per il ``From``
della BUSTA di trasporto (par. 6.3.4): per le RICEVUTE nessuna norma lo impone,
e la copertura era garantita solo dall'osservazione di due gestori su una
ventina accreditati.

Da qui tre criteri in OR, ciascuno che copre un buco degli altri:

===========================  ===============================  ==================
criterio                     copre                            non copre
===========================  ===============================  ==================
header X-Ricevuta/X-Trasp.   ogni gestore, ogni canale        posta di servizio
casella dichiarata PEC       gestori ignoti + posta servizio  fuori da fetch_mail
mittente posta-certificata@  ripiego storico                  gestori fuori norma
===========================  ===============================  ==================

Ogni test qui SPEGNE i criteri che non sta provando, altrimenti passerebbe per
il motivo sbagliato: una fixture PEC autentica li soddisfa tutti e tre insieme.
"""

import email
from pathlib import Path

from odoo.tests import tagged

from odoo.addons.mail.tests.common import MailCommon

FIXTURES = Path(__file__).parent / "fixtures"
FALLBACK_MODEL = "res.partner"

# Busta di anomalia: ha X-Trasporto ma NON X-Ricevuta, quindi basta togliere
# un header solo per azzerare il criterio 1.
ANOMALIA = "pec_anomalia.eml"
# Mittente di un gestore che non rispetta la convenzione sulla parte locale:
# e' il caso che il criterio storico NON sa riconoscere.
UNKNOWN_SENDER = b"From: <notifiche@gestore-mai-visto.example.it>"
PEC_SENDER_LINE = (
    b'From: "Per conto di: mittente-ordinario@example.com" '
    b"<posta-certificata@pec.example.it>"
)


def _raw(name):
    return (FIXTURES / name).read_bytes()


def _message_id(raw):
    return email.message_from_bytes(raw).get("Message-ID")


def _from_header(raw):
    """Il solo campo che conta per il criterio 3.

    Le fixture portano anche ``Return-Path: <posta-certificata@...>``, che e'
    l'envelope sender: la norma impone che resti quello del messaggio
    originale, e infatti ``message_parse`` valorizza ``email_from`` dal
    ``From`` (mail_thread.py L1749). Un controllo sui byte grezzi confonderebbe
    i due campi e darebbe un test verde per il motivo sbagliato.
    """
    return email.message_from_bytes(raw).get("From") or ""


def _drop_header(raw, header):
    prefix = header.lower().encode() + b":"
    return b"".join(
        line
        for line in raw.splitlines(keepends=True)
        if not line.lower().startswith(prefix)
    )


@tagged("post_install", "-at_install")
class TestRouting(MailCommon):
    """Quali criteri fanno atterrare un messaggio, e quali no."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pec_box = cls.env["fetchmail.server"].create(
            {"name": "Casella PEC di prova", "server_type": "imap", "is_pec": True},
        )
        cls.plain_box = cls.env["fetchmail.server"].create(
            {"name": "Casella ordinaria", "server_type": "imap"},
        )

    def _process(self, raw, server=None):
        thread = self.env["mail.thread"].sudo()
        if server is not None:
            thread = thread.with_context(mailpec_fetchmail_server_id=server.id)
        with self.mock_mail_gateway():
            thread.message_process(FALLBACK_MODEL, raw)
        return self.env["mailpec.mail"].search(
            [("message_id", "=", _message_id(raw))],
        )

    def _without_pec_sender(self):
        """Busta autentica, ma spedita da un indirizzo fuori convenzione."""
        return _raw(ANOMALIA).replace(PEC_SENDER_LINE, UNKNOWN_SENDER)

    def _without_any_pec_trait(self):
        """Ne' header PEC ne' mittente PEC: resta solo il flag sulla casella."""
        return _drop_header(self._without_pec_sender(), "X-Trasporto")

    def test_header_routes_a_gestore_we_have_never_seen(self):
        """(a) L'header basta: il mittente fuori convenzione non ferma nulla.

        E' il test che vale per i gestori mai osservati. ``X-Trasporto`` e'
        mandato dalla norma sulle buste, quindi vale per costruzione anche per
        chi non e' nel nostro campione.
        """
        raw = self._without_pec_sender()
        self.assertNotIn(
            "posta-certificata@",
            _from_header(raw),
            "il criterio 3 deve essere spento",
        )

        records = self._process(raw)

        self.assertEqual(len(records), 1, "l'header da solo deve bastare")
        self.assertEqual(records.pec_kind, "non_certificata")

    def test_declared_box_routes_mail_with_no_pec_trait_at_all(self):
        """(b) Sulla casella dichiarata PEC atterra anche cio' che PEC non e'.

        E' il caso della posta di servizio del gestore - avvisi di quota,
        rinnovi - che non ha header PEC e non arriva da ``posta-certificata@``.
        Oggi uscirebbe verso il gateway ordinario e sparirebbe dall'elenco.
        """
        raw = self._without_any_pec_trait()

        records = self._process(raw, server=self.pec_box)

        self.assertEqual(len(records), 1, "la casella dichiarata deve bastare")
        self.assertFalse(
            records.pec_kind,
            "non e' PEC: atterra NON classificato, non si inventa una specie",
        )
        self.assertEqual(
            records.fetchmail_server_id,
            self.pec_box,
            "il server resta tracciato sul record",
        )

    def test_ordinary_box_does_not_capture_ordinary_mail(self):
        """(c) Il criterio 2 e' il FLAG, non il semplice passaggio da fetchmail.

        Senza questa prova (b) potrebbe passare per il motivo sbagliato, cioe'
        perche' esiste la chiave di contesto invece che perche' il flag e'
        acceso: ogni posta ordinaria di qualunque casella finirebbe in PEC.
        """
        raw = self._without_any_pec_trait()

        records = self._process(raw, server=self.plain_box)

        self.assertFalse(records, "una casella non PEC non deve catturare nulla")

    def test_nothing_is_captured_without_any_criterion(self):
        """(d) Fuori dai tre criteri il messaggio segue il flusso normale.

        Contro-prova dell'intero instradamento: senza di essa i tre rami
        potrebbero catturare tutto e i test precedenti sarebbero vacui.
        """
        raw = self._without_any_pec_trait()

        records = self._process(raw)

        self.assertFalse(records, "nessun criterio soddisfatto, nessun record")

    def test_sender_still_routes_when_headers_are_gone(self):
        """(e) Il criterio storico resta attivo: nessuna regressione.

        Serve ai messaggi entrati per canali dove la chiave di contesto non
        esiste e a chi ha gia' traffico storico che passa solo di qui.
        """
        raw = _drop_header(_raw(ANOMALIA), "X-Trasporto")
        self.assertIn(
            "posta-certificata@",
            _from_header(raw),
            "il criterio 3 deve essere acceso",
        )

        records = self._process(raw)

        self.assertEqual(len(records), 1, "il mittente da solo deve ancora bastare")
