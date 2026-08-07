"""Cosa produce una ricevuta PEC dopo l'atterraggio: esito e correlazione.

File separato da ``test_receive.py`` per la stessa ragione per cui il codice e'
separato: ``test_receive`` prova il ROUTING (chi viene intercettato, cosa
sopravvive), qui si prova l'INTERPRETAZIONE (``_pec_process_receipt``). Sono
due responsabilita' distinte e falliscono per motivi distinti. Il nome del file
e della classe e' inoltre quello previsto dal piano, todo 23.

Esito e correlazione stanno nella STESSA classe perche' avvengono nella stessa
``write``: separarli darebbe due classi che fanno atterrare la stessa ricevuta
con lo stesso template.

La certificazione e' passata al template come parametro ``daticert``:
``format_and_process`` inoltra i kwargs sconosciuti a ``str.format``
(odoo_core/odoo/addons/mail/tests/common.py L190-198), quindi ogni test sceglie
il proprio payload senza toccare le fixture del parser, che restano intatte.
"""

from datetime import datetime

from odoo.tests import tagged

from odoo.addons.mail.tests.common import MailCommon

PEC_SENDER = '"Per conto di: mittente@pec.example.it" <posta-certificata@pec.aruba.it>'
EMAIL_TO = "ricevute@test.mycompany.com"
FALLBACK_MODEL = "res.partner"

# Message-ID del messaggio che ABBIAMO inviato, quello che l'header
# X-Riferimento-Message-ID riporta indietro.
ORIGINAL_MESSAGE_ID = "<original-msg-42@test.mycompany.com>"
UNKNOWN_MESSAGE_ID = "<mai-inviato-999@test.mycompany.com>"

# Il <msgid> dell'XML e' DELIBERATAMENTE diverso dall'header: sui campioni
# reali coincidono (15 su 15), ma tenerli diversi qui e' l'unico modo di
# dimostrare quale dei due vince davvero.
XML_ONLY_MESSAGE_ID = "<solo-nell-xml@pec.example.it>"

DATICERT_MANCATA_CONSEGNA = """<?xml version="1.0" encoding="UTF-8"?>
<postacert tipo="mancata-consegna" errore="superamento-tempi-massimi">
    <intestazione>
        <mittente>mittente@pec.example.it</mittente>
        <destinatari tipo="certificato">casella-piena@pec.example.org</destinatari>
        <destinatari tipo="esterno">esterno@example.org</destinatari>
        <oggetto>Comunicazione non recapitata</oggetto>
    </intestazione>
    <dati>
        <gestore-emittente>Gestore Due S.r.l.</gestore-emittente>
        <data zona="+0200">
            <giorno>08/08/2026</giorno>
            <ora>11:20:46</ora>
        </data>
        <identificativo>opec2001.20260808112046.00042.100.1.1@pec.example.it</identificativo>
        <msgid>&lt;solo-nell-xml@pec.example.it&gt;</msgid>
        <ricevuta tipo="completa"/>
        <consegna>casella-piena@pec.example.org</consegna>
        <errore-esteso>Casella del destinatario non disponibile entro le 24 ore previste.</errore-esteso>
    </dati>
</postacert>"""

# Troncato a meta' tag: ET.ParseError garantita.
DATICERT_MALFORMED = '<?xml version="1.0"?><postacert tipo="mancata-consegna"'

# 08/08/2026 11:20:46 con zona +0200 -> 09:20:46 UTC.
RECEIPT_DATE_UTC = datetime(2026, 8, 8, 9, 20, 46)

TEMPLATE = """Return-Path: {return_path}
To: {to}
cc: {cc}
From: {email_from}
Subject: {subject}
MIME-Version: 1.0
Content-Type: multipart/mixed;
\tboundary="----=_Part_PEC_CORR"
Date: Sat, 8 Aug 2026 11:20:46 +0200
Message-ID: {msg_id}
{extra}

------=_Part_PEC_CORR
Content-Type: text/plain; charset=utf-8

Avviso di mancata consegna.
------=_Part_PEC_CORR
Content-Type: application/xml; name="daticert.xml"
Content-Transfer-Encoding: 8bit
Content-Disposition: attachment; filename="daticert.xml"

{daticert}
------=_Part_PEC_CORR--
"""


@tagged("post_install", "-at_install")
class TestCorrelation(MailCommon):
    """La ricevuta atterra, viene interpretata e risale al record di origine.

    Ogni test spinge un ``.eml`` grezzo attraverso l'INTERO gateway con
    ``MailCommon.format_and_process``: e' il percorso reale, override di
    ``message_route`` e ``message_new`` compresi. ``model=res.partner`` e' il
    modello di RIPIEGO: se l'intercettazione non scattasse il messaggio
    finirebbe li' senza eccezioni e le asserzioni fallirebbero in modo pulito.
    """

    def _process(self, subject, daticert, extra=""):
        with self.mock_mail_gateway():
            return self.format_and_process(
                TEMPLATE,
                PEC_SENDER,
                EMAIL_TO,
                subject=subject,
                extra=extra,
                model=FALLBACK_MODEL,
                target_model="mailpec.mail",
                daticert=daticert,
            )

    def test_outcome_fields_come_from_daticert(self):
        """(a) L'esito certificato finisce sui campi del record.

        Nessun header PEC in questo messaggio: e' il caso in cui l'XML e'
        l'unica fonte, e prova che ``daticert.xml`` viene recuperato PER NOME
        dagli allegati (il core forza gli XML a text/plain, quindi un filtro
        per mimetype non troverebbe nulla) e che tipo e riferimento ricadono
        sull'XML quando il gestore non ha emesso gli header.
        """
        records = self._process("Mancata consegna", DATICERT_MANCATA_CONSEGNA)

        self.assertEqual(len(records), 1, "deve nascere un solo mailpec.mail")
        self.assertEqual(records.state, "elaborata")
        self.assertEqual(records.pec_receipt_type, "mancata-consegna")
        self.assertEqual(records.pec_ref_message_id, XML_ONLY_MESSAGE_ID)
        self.assertEqual(records.pec_error, "superamento-tempi-massimi")
        self.assertEqual(
            records.pec_extended_error,
            "Casella del destinatario non disponibile entro le 24 ore previste.",
        )
        self.assertEqual(records.pec_receipt_detail, "completa")
        self.assertEqual(records.pec_provider, "Gestore Due S.r.l.")
        self.assertEqual(records.pec_receipt_date, RECEIPT_DATE_UTC)
        self.assertEqual(
            records.pec_identifier,
            "opec2001.20260808112046.00042.100.1.1@pec.example.it",
        )
        self.assertEqual(records.pec_delivery, "casella-piena@pec.example.org")
        # Il tipo di ogni destinatario distingue il recapito con valore legale
        # da quello senza: perderlo renderebbe la ricevuta inutilizzabile.
        self.assertEqual(
            records.pec_recipients,
            "casella-piena@pec.example.org (certificato)\nesterno@example.org (esterno)",
        )

    def test_receipt_links_back_to_the_message_we_sent(self):
        """(b) Dal riferimento si risale al mail.message e al record di business.

        L'aggancio e' ``mail.message.message_id``, indicizzato e sempre
        valorizzato: da li' arrivano ``model`` e ``res_id``, che puntano al
        record senza che il modulo sappia nulla di quel modello.

        L'``<msgid>`` dell'XML e' diverso dall'header: se l'implementazione
        preferisse l'XML, la ricerca cadrebbe su un Message-ID mai inviato e
        questo test diventerebbe rosso.
        """
        partner = self.env["res.partner"].create({"name": "Cliente Correlato"})
        message = self.env["mail.message"].create(
            {
                "model": "res.partner",
                "res_id": partner.id,
                "message_id": ORIGINAL_MESSAGE_ID,
                "message_type": "email",
                "subtype_id": self.env.ref("mail.mt_note").id,
                "body": "<p>Comunicazione inviata via PEC.</p>",
            },
        )

        records = self._process(
            "Mancata consegna correlata",
            DATICERT_MANCATA_CONSEGNA,
            extra=(
                f"X-Riferimento-Message-ID: {ORIGINAL_MESSAGE_ID}\n"
                "X-Ricevuta: mancata-consegna"
            ),
        )

        self.assertEqual(len(records), 1, "deve nascere un solo mailpec.mail")
        self.assertEqual(
            records.pec_ref_message_id,
            ORIGINAL_MESSAGE_ID,
            "l'header ha la precedenza sul msgid dell'XML",
        )
        self.assertEqual(records.origin_message_id, message)
        self.assertEqual(records.origin_model, "res.partner")
        self.assertEqual(records.origin_res_id, partner.id)
        self.assertEqual(records.state, "elaborata")

    def test_unmatched_reference_still_lands(self):
        """(c) Riferimento che non corrisponde a nulla: la ricevuta atterra lo stesso.

        Caso ordinario, non eccezionale: ricevute di messaggi inviati prima
        dell'installazione, o da fuori Odoo. Una ricevuta ha valore legale e
        non si scarta perche' non si sa a cosa appartiene.
        """
        records = self._process(
            "Mancata consegna orfana",
            DATICERT_MANCATA_CONSEGNA,
            extra=(
                f"X-Riferimento-Message-ID: {UNKNOWN_MESSAGE_ID}\n"
                "X-Ricevuta: mancata-consegna"
            ),
        )

        self.assertEqual(len(records), 1, "la ricevuta orfana deve esistere a DB")
        self.assertEqual(records.pec_ref_message_id, UNKNOWN_MESSAGE_ID)
        self.assertFalse(records.origin_message_id)
        self.assertFalse(records.origin_model)
        self.assertFalse(records.origin_res_id)
        self.assertEqual(
            records.state,
            "elaborata",
            "l'esito e' stato letto: non trovare l'origine non e' un errore",
        )
        self.assertEqual(records.pec_provider, "Gestore Due S.r.l.")

    def test_malformed_daticert_lands_with_error_state(self):
        """(d) Certificazione illeggibile: stato errore, nessuna eccezione.

        E' la regola che tiene in piedi tutto il blocco: se il parsing
        facesse fallire ``message_process``, la prova di consegna andrebbe
        persa. Lo stato dichiara il problema invece di nasconderlo, e il
        messaggio con la busta firmata resta consultabile.
        """
        records = self._process("Ricevuta illeggibile", DATICERT_MALFORMED)

        self.assertEqual(len(records), 1, "la ricevuta deve atterrare comunque")
        self.assertEqual(records.state, "errore")
        self.assertFalse(records.pec_provider)
        self.assertFalse(records.pec_receipt_date)
        self.assertFalse(records.pec_recipients)
        # Il corpo e la busta restano: e' il messaggio ad avere valore legale,
        # non la nostra lettura dell'XML.
        self.assertTrue(records.message_id)
