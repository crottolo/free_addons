"""Le tre specie di messaggio che atterrano in una casella PEC.

Una casella PEC riceve tre cose diverse, e il gestore le RISPEDISCE TUTTE E TRE
dallo stesso indirizzo ``posta-certificata@<dominio>``. L'allowlist le cattura
gia' tutte - nulla si perde - ma senza classificazione sono indistinguibili, e
per due delle tre il contenuto utile e' nascosto dentro un allegato:

===================  ==========  ====================  =========
specie               X-Ricevuta  X-Trasporto           daticert
===================  ==========  ====================  =========
ricevuta             valorizzato posta-certificata     presente
messaggio_pec        assente     posta-certificata     presente
non_certificata      assente     errore                ASSENTE
===================  ==========  ====================  =========

Le fixture sono le stesse di ``test_parser``, spinte pero' attraverso l'INTERO
gateway con ``message_process(model, raw)`` - lo stesso metodo che
``MailCommon.format_and_process`` chiama al suo interno
(odoo_core/odoo/addons/mail/tests/common.py L217). Passare i byte grezzi invece
di un template permette di usare i file cosi' come sono, header compresi:
``X-Trasporto`` e' proprio cio' che si sta provando, e un template lo
riscriverebbe.

``model=res.partner`` e' il modello di RIPIEGO: se l'intercettazione non
scattasse, il messaggio finirebbe li' senza eccezioni e le asserzioni
fallirebbero in modo pulito.

DISCREPANZA NOTA, deliberatamente non nascosta: ``pec_posta-certificata.eml``
porta ANCHE ``X-Ricevuta: posta-certificata``, header che la busta di trasporto
autentica non ha. La fixture e' sintetica e su quel punto e' sovra-specificata.
Non viene modificata: viene usata cosi' com'e' per provare la PRECEDENZA
(X-Ricevuta vince, quindi ``ricevuta``), e in una copia priva di quell'header
per provare il ramo ``messaggio_pec`` su un messaggio di forma autentica.
"""

import email
from pathlib import Path

from odoo.tests import tagged

from odoo.addons.mail.tests.common import MailCommon

FIXTURES = Path(__file__).parent / "fixtures"
FALLBACK_MODEL = "res.partner"

RECEIPT = "pec_accettazione.eml"
CERTIFIED = "pec_posta-certificata.eml"
NOT_CERTIFIED = "pec_anomalia.eml"

# Boundary interna di pec_anomalia.eml: serve per amputare la parte
# postacert.eml lasciando la busta MIME valida.
ANOMALIA_BOUNDARY = b"------=_Mixed_opec1011"


def _raw(name):
    return (FIXTURES / name).read_bytes()


def _message_id(raw):
    return email.message_from_bytes(raw).get("Message-ID")


def _drop_header(raw, header):
    """Toglie una riga di header dai byte grezzi, senza toccare il file."""
    prefix = header.lower().encode() + b":"
    return b"".join(
        line
        for line in raw.splitlines(keepends=True)
        if not line.lower().startswith(prefix)
    )


def _drop_postacert_part(raw):
    """Amputa l'intera parte ``postacert.eml``, lasciando la busta valida."""
    parts = raw.split(ANOMALIA_BOUNDARY)
    return ANOMALIA_BOUNDARY.join(
        part for part in parts if b'filename="postacert.eml"' not in part
    )


@tagged("post_install", "-at_install")
class TestClassification(MailCommon):
    """Ogni messaggio riceve la sua specie, e l'imbustato torna a galla."""

    def _process(self, raw):
        with self.mock_mail_gateway():
            self.env["mail.thread"].sudo().message_process(FALLBACK_MODEL, raw)
        records = self.env["mailpec.mail"].search(
            [("message_id", "=", _message_id(raw))],
        )
        self.assertEqual(len(records), 1, "deve nascere un solo mailpec.mail")
        return records

    def _process_certified(self):
        """La busta di trasporto nella forma AUTENTICA: senza ``X-Ricevuta``."""
        return self._process(_drop_header(_raw(CERTIFIED), "X-Ricevuta"))

    def test_receipt_is_classified_as_ricevuta(self):
        """(a) Con ``X-Ricevuta`` la specie e' ``ricevuta``, e vince su X-Trasporto.

        La fixture porta ENTRAMBI gli header, e ``X-Trasporto`` vale
        ``posta-certificata``: se la catena fosse in ordine inverso, ogni
        ricevuta verrebbe classificata come messaggio in arrivo. E' il motivo
        per cui ``_pec_kind`` e' a priorita' e non a mutua esclusione.
        """
        records = self._process(_raw(RECEIPT))

        self.assertEqual(records.pec_kind, "ricevuta")
        self.assertEqual(records.pec_receipt_type, "accettazione")
        self.assertEqual(
            records.pec_transport,
            "posta-certificata",
            "X-Trasporto c'e' ed e' catturato: la precedenza e' una scelta, "
            "non l'effetto di un header mancante",
        )

    def test_certified_message_is_classified_as_messaggio_pec(self):
        """(b) Solo ``X-Trasporto: posta-certificata`` -> ``messaggio_pec``.

        La specie si fissa alla create dagli HEADER. Piu' tardi
        ``_pec_outcome_values`` valorizza ``pec_receipt_type`` leggendolo
        dall'XML: se la classificazione fosse rifatta dopo, il messaggio
        diventerebbe una ricevuta. L'asserzione su ``pec_kind`` accanto a
        quella su ``pec_receipt_type`` e' li' per bloccare quel difetto.
        """
        records = self._process_certified()

        self.assertEqual(records.pec_kind, "messaggio_pec")
        self.assertEqual(records.pec_transport, "posta-certificata")
        self.assertEqual(
            records.pec_receipt_type,
            "posta-certificata",
            "il tipo arriva dall'XML, ma non deve ri-classificare il messaggio",
        )
        self.assertEqual(records.state, "elaborata")

    def test_non_certified_message_is_classified_as_non_certificata(self):
        """(c) ``X-Trasporto: errore`` -> ``non_certificata``, e atterra comunque.

        E' il canale non certificato della casella: riceve posta ordinaria, e
        nei campioni reali spam e phishing. Il messaggio NON viene archiviato
        ne' scartato: resta visibile con la sua specie, quindi filtrabile.
        """
        records = self._process(_raw(NOT_CERTIFIED))

        self.assertEqual(records.pec_kind, "non_certificata")
        self.assertEqual(records.pec_transport, "errore")
        self.assertTrue(records.active, "nulla viene archiviato d'ufficio")
        self.assertFalse(
            records.pec_provider,
            "senza daticert.xml non c'e' nulla da certificare",
        )

    def test_transport_header_reaches_every_record(self):
        """(d) ``X-Trasporto`` arriva sul record in tutte e tre le specie.

        ``message_parse`` restituisce chiavi FISSE (mail_thread.py L1705-1744),
        quindi un header custom non raggiunge MAI ``message_new`` da solo: se
        ``message_route`` non lo catturasse, ``pec_transport`` resterebbe vuoto
        e due specie su tre diventerebbero indistinguibili.
        """
        self.assertEqual(
            self._process(_raw(RECEIPT)).pec_transport,
            "posta-certificata",
        )
        self.assertEqual(self._process_certified().pec_transport, "posta-certificata")
        self.assertEqual(self._process(_raw(NOT_CERTIFIED)).pec_transport, "errore")

    def test_wrapped_sender_and_subject_are_surfaced(self):
        """(e) Sul non certificato emergono mittente e oggetto VERI.

        E' il cuore del todo. La busta esterna e' del gestore
        (``posta-certificata@...``, oggetto ``ANOMALIA MESSAGGIO: ...``) ed e'
        identica per ogni messaggio: chi guarda l'elenco non ha modo di sapere
        chi ha scritto e cosa. Le due asserzioni negative sono quelle che
        contano: provano che i campi NON stanno ricopiando la busta.
        """
        records = self._process(_raw(NOT_CERTIFIED))

        self.assertEqual(records.original_email_from, "mittente-ordinario@example.com")
        self.assertEqual(records.original_subject, "Comunicazione non certificata")
        self.assertNotIn("posta-certificata@", records.original_email_from)
        self.assertNotIn("ANOMALIA MESSAGGIO", records.original_subject)
        # La busta resta comunque leggibile: non la si sostituisce, la si
        # affianca. E' il messaggio consegnato, e va conservato com'e'.
        self.assertIn("posta-certificata@pec.example.it", records.email_from)
        self.assertTrue(records.name.startswith("ANOMALIA MESSAGGIO:"))

    def test_certified_message_surfaces_the_original(self):
        """(f) Anche sul messaggio PEC l'originale imbustato torna a galla."""
        records = self._process_certified()

        self.assertEqual(records.original_email_from, "mittente@pec.example.it")
        self.assertEqual(records.original_subject, "Comunicazione di prova")

    def test_receipt_keeps_the_envelope_as_the_document(self):
        """(g) Su una ricevuta i campi dell'originale restano vuoti.

        Una ricevuta NON e' una busta attorno a qualcos'altro: e' essa stessa
        il documento con valore legale, e mittente e oggetto certificati stanno
        gia' in ``daticert.xml``. Riempirli qui duplicherebbe il dato in due
        posti che possono divergere.
        """
        records = self._process(_raw(RECEIPT))

        self.assertFalse(records.original_email_from)
        self.assertFalse(records.original_subject)

    def test_missing_postacert_falls_back_to_the_display_name(self):
        """(h) Senza ``postacert.eml`` nulla esplode: si legge il display name.

        I gestori scrivono ``"Per conto di: <indirizzo reale>"
        <posta-certificata@...>``, quindi il mittente vero si recupera dalla
        busta anche quando l'allegato non c'e' (fetchmail con «Keep
        Attachments» disattivato lo cancella prima che Odoo lo veda).
        L'oggetto NON ha ripiego: quello esterno e' del gestore, e spacciarlo
        per l'originale sarebbe peggio che lasciarlo vuoto.
        """
        raw = _drop_postacert_part(_raw(NOT_CERTIFIED))
        self.assertNotIn(b"postacert.eml", raw, "la parte deve essere davvero via")

        records = self._process(raw)

        self.assertEqual(records.pec_kind, "non_certificata")
        self.assertEqual(records.original_email_from, "mittente-ordinario@example.com")
        self.assertFalse(records.original_subject)

    def test_postacert_is_fetched_by_name_not_by_mimetype(self):
        """(i) L'allegato si cerca per NOME: rinominato, non viene piu' letto.

        Stessa regola gia' valida per ``daticert.xml``. Un recupero per
        mimetype troverebbe comunque il ``message/rfc822`` e questo test
        diventerebbe rosso: e' esattamente il difetto che deve impedire.
        """
        raw = _raw(NOT_CERTIFIED).replace(
            b'filename="postacert.eml"',
            b'filename="allegato-generico.eml"',
        )

        records = self._process(raw)

        self.assertEqual(
            records.original_email_from,
            "mittente-ordinario@example.com",
            "resta il ripiego sul display name, non la lettura dell'allegato",
        )
        self.assertFalse(records.original_subject)

    def test_unclassifiable_message_lands_with_kind_unset(self):
        """(l) Nessun header riconosciuto: specie NON valorizzata, record intatto.

        Decisione esplicita: non esiste un quarto valore "sconosciuto", perche'
        dichiarerebbe una classificazione mai avvenuta. Il messaggio atterra,
        resta visibile e si trova con il filtro «Non classificate».
        """
        raw = _drop_header(_raw(NOT_CERTIFIED), "X-Trasporto")

        records = self._process(raw)

        self.assertFalse(records.pec_kind)
        self.assertFalse(records.pec_transport)
        self.assertFalse(
            records.original_email_from,
            "senza specie non si estrae nulla: non si sa cosa si sta leggendo",
        )
        self.assertTrue(records.active, "un messaggio non classificato resta visibile")
        self.assertTrue(records.message_id, "il messaggio e' comunque a DB")
