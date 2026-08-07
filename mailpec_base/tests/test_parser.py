"""Specifica del parser di ``daticert.xml``: i test PRECEDONO il codice.

E' l'unico punto del piano in cui il test viene prima dell'implementazione, ed
e' giustificato: ``_parse_daticert`` e' una funzione pura (bytes in, dict out)
e questi test valgono come specifica del formato. Finche' il metodo non esiste
questa classe e' ROSSA per progetto.

Le fixture sono SINTETICHE, non ricevute reali. Sedici messaggi autentici di
quattro gestori (Aruba, InfoCert, Namirial, Poste) hanno fissato la struttura;
versionarli qui avrebbe significato mettere in repository dati personali di
terzi. Le fixture sintetiche hanno rischio di divulgazione nullo e coprono di
piu': il traffico reale esercitava 4 dei 10 tipi previsti, qui ci sono tutti e
10. Ogni indirizzo sta sotto example.it / example.org / example.com, riservati
da RFC 2606.

Struttura riprodotta dai campioni reali, da rispettare alla lettera:

- ``tipo`` ed ``errore`` sono ATTRIBUTI della radice ``<postacert>``, non
  elementi figli. E' la domanda che il piano vietava di risolvere per
  congettura, ed e' stata risolta sui campioni.
- ``<destinatari>`` si RIPETE, uno per destinatario, con attributo ``tipo``
  che vale ``certificato`` oppure ``esterno``.
- ``<data>`` e' SPEZZATA in ``<giorno>`` (DD/MM/YYYY) e ``<ora>`` (HH:MM:SS),
  con il fuso nell'attributo ``zona``. Non e' un timestamp ISO.
- ``<msgid>`` contiene il Message-ID originale con ``<`` e ``>`` scritti come
  entita' XML ``&lt;`` e ``&gt;``.
- ``<consegna>`` compare SOLO in ``avvenuta-consegna`` e ``mancata-consegna``.
- ``<errore-esteso>`` compare SOLO quando ``errore`` non vale ``nessuno``.
- ``<ricevuta tipo="..."/>`` e' un elemento VUOTO: porta solo l'attributo, e
  manca del tutto nella busta di trasporto ``posta-certificata``.

Contratto preteso da ``mailpec.mail._parse_daticert(xml_bytes)`` — SEMPRE un
dict con queste chiavi, mai una tupla (difetto di aiutotel_base L197), mai
un'eccezione:

===============  ==========  ================================================
chiave           tipo        origine
===============  ==========  ================================================
receipt_type     str         ``postacert/@tipo``
error            str         ``postacert/@errore``
sender           str         ``intestazione/mittente``
subject          str         ``intestazione/oggetto``
recipients       list[dict]  ``intestazione/destinatari`` -> address + type
gestore          str         ``dati/gestore-emittente``
date             datetime    ``dati/data`` (giorno+ora+zona) normalizzata a UTC
identificativo   str         ``dati/identificativo``
ref_message_id   str         ``dati/msgid``, con ``< >`` gia' de-escapati
receipt_detail   str         ``dati/ricevuta/@tipo``, "" se assente
delivery         str         ``dati/consegna``, "" se assente
extended_error   str         ``dati/errore-esteso``, "" se assente
===============  ==========  ================================================

``date`` e' un ``datetime`` naive in UTC, la convenzione dei campi Datetime di
Odoo. Convertire e' obbligatorio, non cosmetico: ignorare ``zona`` sposterebbe
di ore la data legale di una ricevuta, e sulla fixture
``preavviso-errore-consegna`` (00:30 +0200) la sposterebbe di un GIORNO.
"""

import email
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from odoo.tests import TransactionCase, tagged

FIXTURES = Path(__file__).parent / "fixtures"

# Tabella di specifica: cosa il parser deve estrarre da ciascuna fixture.
# Copre tutti e 10 i valori di `tipo`, tutti e 5 quelli di `errore` e tutti e
# 3 quelli di `ricevuta/@tipo`.
EXPECTED = {
    "accettazione": {
        "file": "pec_accettazione.eml",
        "error": "nessuno",
        "sender": "mittente@pec.example.it",
        "subject": "Comunicazione di prova",
        "recipients": [
            {"address": "destinatario@pec.example.org", "type": "certificato"},
            {"address": "esterno@example.org", "type": "esterno"},
        ],
        "gestore": "Gestore Uno S.p.A.",
        "date": datetime(2026, 8, 7, 9, 20, 46),
        "identificativo": "opec1001.20260807112045.00001.100.1.1@pec.example.it",
        "ref_message_id": "<MSGID0001@pec.example.it>",
        "receipt_detail": "completa",
        "delivery": "",
        "extended_error": "",
    },
    "non-accettazione": {
        "file": "pec_non-accettazione.eml",
        "error": "eccezione-formale",
        "sender": "mittente@pec.example.it",
        "subject": "Comunicazione con destinatario errato",
        "recipients": [
            {"address": "indirizzo-inesistente@pec.example.org", "type": "certificato"},
        ],
        "gestore": "Gestore Uno S.p.A.",
        # Unica fixture con zona="+0100": il fuso va letto dall'attributo.
        "date": datetime(2026, 1, 15, 7, 5, 12),
        "identificativo": "opec1002.20260115080512.00002.100.1.1@pec.example.it",
        "ref_message_id": "<MSGID0002@pec.example.it>",
        "receipt_detail": "completa",
        "delivery": "",
        "extended_error": (
            "Indirizzo del destinatario non conforme alla sintassi prevista: "
            "dominio non riconosciuto dal sistema di posta certificata."
        ),
    },
    "presa-in-carico": {
        "file": "pec_presa-in-carico.eml",
        "error": "nessuno",
        "sender": "mittente@pec.example.it",
        "subject": "Comunicazione di prova",
        "recipients": [
            {"address": "destinatario@pec.example.org", "type": "certificato"},
        ],
        "gestore": "Gestore Due S.r.l.",
        "date": datetime(2026, 8, 7, 9, 21, 3),
        "identificativo": "opec1003.20260807112103.00003.100.1.1@pec.example.it",
        "ref_message_id": "<MSGID0001@pec.example.it>",
        "receipt_detail": "sintetica",
        "delivery": "",
        "extended_error": "",
    },
    "avvenuta-consegna": {
        "file": "pec_avvenuta-consegna.eml",
        "error": "nessuno",
        "sender": "mittente@pec.example.it",
        "subject": "Comunicazione di prova",
        "recipients": [
            {"address": "destinatario@pec.example.org", "type": "certificato"},
        ],
        "gestore": "Gestore Due S.r.l.",
        "date": datetime(2026, 8, 7, 9, 22, 31),
        "identificativo": "opec1004.20260807112231.00004.100.1.1@pec.example.it",
        "ref_message_id": "<MSGID0001@pec.example.it>",
        "receipt_detail": "breve",
        "delivery": "destinatario@pec.example.org",
        "extended_error": "",
    },
    "mancata-consegna": {
        "file": "pec_mancata-consegna.eml",
        "error": "superamento-tempi-massimi",
        "sender": "mittente@pec.example.it",
        "subject": "Comunicazione non recapitata",
        "recipients": [
            {"address": "casella-piena@pec.example.org", "type": "certificato"},
        ],
        "gestore": "Gestore Due S.r.l.",
        "date": datetime(2026, 8, 8, 9, 20, 46),
        "identificativo": "opec1005.20260808112046.00005.100.1.1@pec.example.it",
        "ref_message_id": "<MSGID0003@pec.example.it>",
        "receipt_detail": "completa",
        # Unico caso con <consegna> ED <errore-esteso> insieme: la consegna
        # dice verso quale casella si e' fallito.
        "delivery": "casella-piena@pec.example.org",
        "extended_error": (
            "Il messaggio non e' stato consegnato entro le 24 ore previste: "
            "casella del destinatario non disponibile."
        ),
    },
    "errore-consegna": {
        "file": "pec_errore-consegna.eml",
        "error": "altro",
        "sender": "mittente@pec.example.it",
        "subject": "Comunicazione di prova",
        "recipients": [
            {"address": "destinatario@pec.example.org", "type": "certificato"},
        ],
        "gestore": "Gestore Uno S.p.A.",
        "date": datetime(2026, 8, 7, 10, 0, 0),
        "identificativo": "opec1006.20260807120000.00006.100.1.1@pec.example.it",
        "ref_message_id": "<MSGID0004@pec.example.it>",
        "receipt_detail": "completa",
        "delivery": "",
        "extended_error": (
            "Errore nella trasmissione verso il gestore del destinatario: "
            "nessuna risposta dal server remoto dopo cinque tentativi."
        ),
    },
    "preavviso-errore-consegna": {
        "file": "pec_preavviso-errore-consegna.eml",
        "error": "superamento-tempi-massimi",
        "sender": "mittente@pec.example.it",
        "subject": "Comunicazione non recapitata",
        "recipients": [
            {"address": "destinatario@pec.example.org", "type": "certificato"},
        ],
        "gestore": "Gestore Due S.r.l.",
        # 08/08/2026 00:30:12 +0200 -> 07/08/2026 22:30:12 UTC: la data
        # ARRETRA di un giorno. Vedi test_date_crosses_midnight_backwards.
        "date": datetime(2026, 8, 7, 22, 30, 12),
        "identificativo": "opec1007.20260808003012.00007.100.1.1@pec.example.it",
        "ref_message_id": "<MSGID0003@pec.example.it>",
        "receipt_detail": "completa",
        "delivery": "",
        "extended_error": (
            "Il messaggio non risulta ancora consegnato dopo dodici ore: "
            "seguira' avviso di mancata consegna se la situazione persiste."
        ),
    },
    "rilevazione-virus": {
        "file": "pec_rilevazione-virus.eml",
        "error": "virus",
        "sender": "mittente@pec.example.it",
        "subject": "Comunicazione con allegato infetto",
        "recipients": [
            {"address": "destinatario@pec.example.org", "type": "certificato"},
        ],
        "gestore": "Gestore Due S.r.l.",
        "date": datetime(2026, 8, 7, 11, 45, 9),
        "identificativo": "opec1008.20260807134509.00008.100.1.1@pec.example.it",
        "ref_message_id": "<MSGID0005@pec.example.it>",
        "receipt_detail": "completa",
        "delivery": "",
        "extended_error": (
            "Rilevato contenuto malevolo nel messaggio in transito: "
            "firma EICAR-Test-File nell'allegato documento.zip."
        ),
    },
    "non-accettazione-virus": {
        "file": "pec_non-accettazione-virus.eml",
        "error": "virus",
        "sender": "mittente@pec.example.it",
        "subject": "Comunicazione con allegato infetto",
        "recipients": [
            {"address": "destinatario@pec.example.org", "type": "certificato"},
        ],
        "gestore": "Gestore Uno S.p.A.",
        "date": datetime(2026, 8, 7, 11, 45, 11),
        "identificativo": "opec1009.20260807134511.00009.100.1.1@pec.example.it",
        "ref_message_id": "<MSGID0006@pec.example.it>",
        "receipt_detail": "completa",
        "delivery": "",
        "extended_error": (
            "Messaggio non accettato: rilevata firma EICAR-Test-File "
            "nell'allegato documento.zip."
        ),
    },
    "posta-certificata": {
        "file": "pec_posta-certificata.eml",
        "error": "nessuno",
        "sender": "mittente@pec.example.it",
        "subject": "Comunicazione di prova",
        "recipients": [
            {"address": "destinatario@pec.example.org", "type": "certificato"},
        ],
        "gestore": "Gestore Uno S.p.A.",
        "date": datetime(2026, 8, 7, 9, 20, 45),
        "identificativo": "opec1010.20260807112045.00010.100.1.1@pec.example.it",
        "ref_message_id": "<MSGID0001@pec.example.it>",
        # La busta di trasporto NON e' una ricevuta: <ricevuta> non c'e'.
        "receipt_detail": "",
        "delivery": "",
        "extended_error": "",
    },
}

# XML rotto in cinque modi diversi. Una ricevuta PEC ha valore legale: non si
# perde perche' il parsing e' fallito. Il metodo deve degradare, mai sollevare.
MALFORMED = {
    "empty": b"",
    "not_xml": b"Impossibile decodificare il contenuto della ricevuta.",
    "truncated": b'<?xml version="1.0"?><postacert tipo="accettazione"',
    "wrong_root": b"<qualcosa><altro>x</altro></qualcosa>",
    "binary_garbage": b"\x00\x01\x02\xff\xfe daticert \x00",
}

# Chiavi che il contratto impone SEMPRE presenti, anche sul dict vuoto.
CONTRACT_KEYS = {
    "receipt_type",
    "error",
    "sender",
    "subject",
    "recipients",
    "gestore",
    "date",
    "identificativo",
    "ref_message_id",
    "receipt_detail",
    "delivery",
    "extended_error",
}


def _daticert_bytes(eml_name):
    """Estrae i byte grezzi di ``daticert.xml`` dalla busta, o None se assente.

    Recupero per NOME dell'allegato, mai per mimetype: il core Odoo forza gli
    XML a text/plain (base/models/ir_attachment.py L376-381, conseguenza di
    ``attachments_mime_plainxml=True`` in mail_thread.py L1294), quindi un
    parser che filtrasse per application/xml non troverebbe nulla in
    produzione. ``get_payload(decode=True)`` normalizza qualunque
    Content-Transfer-Encoding e restituisce i byte come li vedra' il parser.
    """
    message = email.message_from_bytes((FIXTURES / eml_name).read_bytes())
    for part in message.walk():
        if part.get_filename() == "daticert.xml":
            return part.get_payload(decode=True)
    return None


@tagged("post_install", "-at_install")
class TestParser(TransactionCase):
    """``_parse_daticert`` estrae l'esito certificato da ``daticert.xml``.

    Questa classe e' scritta PRIMA del parser e deve fallire: e' la specifica
    che il todo successivo dovra' soddisfare senza modificare un solo assert.
    Il metodo NON va implementato qui.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.parser = cls.env["mailpec.mail"]

    def _parse(self, tipo):
        eml_name = EXPECTED[tipo]["file"]
        xml_bytes = _daticert_bytes(eml_name)
        self.assertIsNotNone(
            xml_bytes,
            f"la fixture {eml_name} deve contenere un daticert.xml",
        )
        return self.parser._parse_daticert(xml_bytes)

    def test_all_receipt_types_are_parsed(self):
        """(a) Tutti e 10 i valori di ``postacert@tipo`` vengono riconosciuti.

        E' il test di copertura della tassonomia: se un tipo mancasse dalle
        fixture, o il parser lo ignorasse, qui si vedrebbe subito. Vale anche
        come verifica che il dict abbia sempre le stesse chiavi.
        """
        for tipo, expected in EXPECTED.items():
            with self.subTest(tipo=tipo):
                result = self._parse(tipo)
                self.assertEqual(
                    set(result),
                    CONTRACT_KEYS,
                    "il parser deve restituire sempre le stesse chiavi",
                )
                self.assertEqual(
                    result["receipt_type"],
                    tipo,
                    "postacert@tipo e' un ATTRIBUTO della radice, non un figlio",
                )
                self.assertEqual(result["error"], expected["error"])

    def test_intestazione_and_gestore_fields(self):
        """(b) Mittente, oggetto, gestore e identificativo vengono estratti."""
        for tipo, expected in EXPECTED.items():
            with self.subTest(tipo=tipo):
                result = self._parse(tipo)
                self.assertEqual(result["sender"], expected["sender"])
                self.assertEqual(result["subject"], expected["subject"])
                self.assertEqual(result["gestore"], expected["gestore"])
                self.assertEqual(
                    result["identificativo"],
                    expected["identificativo"],
                )

    def test_recipients_carry_their_own_type(self):
        """(c) Ogni destinatario porta il proprio ``tipo``.

        ``<destinatari>`` si ripete e l'attributo distingue chi ha ricevuto
        posta certificata da chi ha ricevuto posta ordinaria: e' la differenza
        fra un recapito con valore legale e uno senza. Un parser che tenesse
        solo il primo elemento perderebbe in silenzio i destinatari successivi.
        """
        for tipo, expected in EXPECTED.items():
            with self.subTest(tipo=tipo):
                result = self._parse(tipo)
                self.assertEqual(result["recipients"], expected["recipients"])

    def test_accettazione_has_mixed_recipients(self):
        """(d) L'accettazione elenca destinatari certificati ED esterni.

        Caso reale: un invio a due indirizzi di cui uno non PEC. Il test lo
        isola perche' e' l'unica fixture con piu' di un destinatario e con i
        due valori dell'attributo presenti insieme.
        """
        result = self._parse("accettazione")

        self.assertEqual(len(result["recipients"]), 2)
        self.assertEqual(
            [recipient["type"] for recipient in result["recipients"]],
            ["certificato", "esterno"],
            "ordine e tipo dei destinatari devono essere preservati",
        )

    def test_ref_message_id_is_unescaped(self):
        """(e) Il Message-ID di riferimento arriva de-escapato, con ``< >``.

        Nell'XML sta scritto ``&lt;MSGID...&gt;``. Deve tornare
        ``<MSGID...>``: e' la forma con cui il core indicizza
        ``mail.message.message_id`` (mail_message.py L178), quindi l'unica che
        permette la correlazione al messaggio inviato. Restituirlo con le
        entita' intatte, o senza parentesi, spezza la ricerca in silenzio.
        """
        for tipo, expected in EXPECTED.items():
            with self.subTest(tipo=tipo):
                result = self._parse(tipo)
                self.assertEqual(result["ref_message_id"], expected["ref_message_id"])
                self.assertNotIn(
                    "&lt;",
                    result["ref_message_id"],
                    "le entita' XML devono essere risolte, non propagate",
                )

    def test_date_is_a_real_datetime_in_utc(self):
        """(f) ``<data>`` diventa un datetime naive in UTC.

        L'XML non ha un timestamp: ha ``<giorno>`` DD/MM/YYYY, ``<ora>``
        HH:MM:SS e il fuso nell'attributo ``zona``. Il parser deve ricomporli
        e riportarli a UTC, la convenzione dei campi Datetime di Odoo.
        Restituire la stringa, o il datetime locale, falserebbe di ore la data
        legale della ricevuta.
        """
        for tipo, expected in EXPECTED.items():
            with self.subTest(tipo=tipo):
                result = self._parse(tipo)
                self.assertIsInstance(
                    result["date"],
                    datetime,
                    "la data deve essere un datetime, non una stringa",
                )
                self.assertEqual(result["date"], expected["date"])

    def test_date_reads_the_zona_attribute(self):
        """(g) Fusi diversi danno scarti diversi: ``zona`` viene letta davvero.

        ``non-accettazione`` e' l'unica fixture con ``zona="+0100"``. Un parser
        che ignorasse l'attributo, o che assumesse sempre +0200, passerebbe
        tutti gli altri casi e fallirebbe solo qui.
        """
        result = self._parse("non-accettazione")

        # XML: giorno 15/01/2026, ora 08:05:12, zona +0100.
        self.assertEqual(result["date"], datetime(2026, 1, 15, 7, 5, 12))

    def test_date_crosses_midnight_backwards(self):
        """(h) La conversione a UTC puo' far ARRETRARE il giorno.

        ``preavviso-errore-consegna`` e' timbrata 08/08/2026 alle 00:30:12 con
        fuso +0200: in UTC e' il 07/08/2026 alle 22:30:12. Un parser che
        convertisse solo l'orario lasciando il giorno com'e' passerebbe ogni
        altra fixture e sbaglierebbe di un giorno intero proprio su una
        ricevuta di preavviso, dove il tempo e' l'oggetto stesso.
        """
        result = self._parse("preavviso-errore-consegna")

        self.assertEqual(result["date"], datetime(2026, 8, 7, 22, 30, 12))
        self.assertEqual(
            result["date"].day,
            7,
            "il giorno deve arretrare, non restare 8",
        )

    def test_delivery_only_where_the_provider_emits_it(self):
        """(i) ``<consegna>`` esiste solo nelle due ricevute di consegna.

        Ovunque altro il parser deve restituire stringa vuota: non deve
        sollevare per elemento mancante ne' inventare un indirizzo.
        """
        for tipo, expected in EXPECTED.items():
            with self.subTest(tipo=tipo):
                result = self._parse(tipo)
                self.assertEqual(result["delivery"], expected["delivery"])

        self.assertEqual(
            [tipo for tipo, expected in EXPECTED.items() if expected["delivery"]],
            ["avvenuta-consegna", "mancata-consegna"],
            "solo avvenuta-consegna e mancata-consegna portano <consegna>",
        )

    def test_extended_error_only_when_error_is_not_nessuno(self):
        """(l) ``<errore-esteso>`` accompagna ogni ``errore`` diverso da nessuno.

        E' il testo che spiega all'operatore perche' la PEC non e' arrivata: se
        il parser lo perde, sul record resta solo un codice.
        """
        for tipo, expected in EXPECTED.items():
            with self.subTest(tipo=tipo):
                result = self._parse(tipo)
                self.assertEqual(result["extended_error"], expected["extended_error"])
                if expected["error"] == "nessuno":
                    self.assertEqual(
                        result["extended_error"],
                        "",
                        "senza errore non ci puo' essere errore-esteso",
                    )
                else:
                    self.assertTrue(
                        result["extended_error"],
                        f"{tipo} ha errore={expected['error']}: serve la spiegazione",
                    )

    def test_ricevuta_type_comes_from_the_empty_element_attribute(self):
        """(m) ``<ricevuta tipo="..."/>`` e' vuoto: conta solo l'attributo.

        Un parser che ne leggesse il testo troverebbe sempre stringa vuota e
        non se ne accorgerebbe. Le fixture coprono i tre valori previsti —
        completa, sintetica, breve — e la busta di trasporto, dove l'elemento
        manca del tutto.
        """
        self.assertEqual(self._parse("accettazione")["receipt_detail"], "completa")
        self.assertEqual(self._parse("presa-in-carico")["receipt_detail"], "sintetica")
        self.assertEqual(self._parse("avvenuta-consegna")["receipt_detail"], "breve")
        self.assertEqual(
            self._parse("posta-certificata")["receipt_detail"],
            "",
            "la busta di trasporto non e' una ricevuta: <ricevuta> non c'e'",
        )

    def test_malformed_xml_returns_empty_values_without_raising(self):
        """(n) Su XML rotto: dict con valori vuoti, MAI un'eccezione.

        E' la regola piu' importante del parser. Una ricevuta PEC ha valore
        legale: se il parsing esplode, l'atterraggio del messaggio fallisce e
        la prova di consegna si perde. Il modulo replica qui la scelta gia'
        fatta in aiutotel_base/models/aiutotel_mail.py L413-419 — «non bloccare
        la creazione dell'email per errori di processing» — ma la rende parte
        del contratto invece che di un try/except del chiamante.
        """
        for label, payload in MALFORMED.items():
            with self.subTest(malformed=label):
                try:
                    result = self.parser._parse_daticert(payload)
                except Exception as error:
                    self.fail(
                        f"_parse_daticert non deve sollevare su {label}: "
                        f"{type(error).__name__}: {error}",
                    )

                self.assertEqual(
                    set(result),
                    CONTRACT_KEYS,
                    "anche in errore il dict deve avere tutte le chiavi",
                )
                self.assertFalse(result["receipt_type"])
                self.assertFalse(result["error"])
                self.assertFalse(result["ref_message_id"])
                self.assertFalse(result["delivery"])
                self.assertFalse(result["extended_error"])
                self.assertFalse(result["date"])
                self.assertEqual(result["recipients"], [])

    def test_missing_payload_returns_empty_values(self):
        """(o) Nessun daticert.xml da leggere: stesso dict vuoto, nessun crash.

        Capita davvero: un messaggio in anomalia non ne ha, e un fetchmail con
        «Keep Attachments» disattivato lo cancella prima che Odoo lo veda
        (fetchmail.py L238 -> mail_thread.py L1410-1411).
        """
        result = self.parser._parse_daticert(None)

        self.assertEqual(set(result), CONTRACT_KEYS)
        self.assertFalse(result["receipt_type"])
        self.assertEqual(result["recipients"], [])

    def test_anomalia_message_carries_no_daticert(self):
        """(p) Il messaggio NON certificato non ha daticert.xml da leggere.

        Non e' una ricevuta: ha ``X-Trasporto: errore``, nessun ``X-Ricevuta``
        e nessuna certificazione allegata. Fissare il caso limite adesso
        impedisce all'implementazione di dare per scontato che l'allegato ci
        sia sempre.
        """
        raw = (FIXTURES / "pec_anomalia.eml").read_bytes()
        message = email.message_from_bytes(raw)

        self.assertEqual(message.get("X-Trasporto"), "errore")
        self.assertIsNone(
            message.get("X-Ricevuta"),
            "un messaggio in anomalia non e' una ricevuta",
        )
        self.assertIsNone(
            _daticert_bytes("pec_anomalia.eml"),
            "il messaggio in anomalia non porta daticert.xml",
        )
        self.assertFalse(self.parser._parse_daticert(None)["receipt_type"])

    def test_fixtures_are_well_formed_and_synthetic(self):
        """(q) Autodiagnosi delle fixture: XML valido e domini riservati.

        Non prova il parser, protegge i test: una fixture rotta o con un
        dominio reale renderebbe rossi tutti gli altri casi per il motivo
        sbagliato. I domini ammessi sono quelli riservati da RFC 2606.
        """
        allowed = ("example.it", "example.org", "example.com")

        for tipo, expected in EXPECTED.items():
            with self.subTest(tipo=tipo):
                payload = _daticert_bytes(expected["file"])
                root = ET.fromstring(payload)

                self.assertEqual(root.tag, "postacert")
                self.assertEqual(root.get("tipo"), tipo)
                addresses = [
                    element.text
                    for element in root.iter()
                    if element.text and "@" in element.text
                ]
                self.assertTrue(addresses, "la fixture deve contenere indirizzi")
                for address in addresses:
                    self.assertTrue(
                        address.strip().rstrip(">").endswith(allowed),
                        f"{address} non e' sotto un dominio riservato RFC 2606",
                    )
