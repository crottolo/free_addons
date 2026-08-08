import logging
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from email import message_from_bytes, message_from_string, policy
from email.message import Message
from email.utils import parseaddr

from odoo import _, api, fields, models
from odoo.tools.mail import decode_message_header, plaintext2html

_logger = logging.getLogger(__name__)

# Display name che ogni gestore mette sulla busta esterna:
# "Per conto di: <indirizzo reale>" <posta-certificata@...>.
ON_BEHALF_PREFIX = "per conto di:"


class MailpecMail(models.Model):
    """Landing zone per le ricevute PEC in ingresso.

    Una ricevuta PEC ha valore legale: deve atterrare INTATTA prima che
    qualcuno provi a interpretarla. Prima si salva il messaggio grezzo, poi
    si legge ``daticert.xml`` e si risale al messaggio inviato. L'ordine non
    e' negoziabile: l'interpretazione puo' fallire, l'atterraggio no.
    """

    _name = "mailpec.mail"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Messaggio PEC ricevuto"
    # date_received, NON id: su un fetch massivo l'ordine di inserimento non
    # coincide con quello cronologico (156 messaggi dal 2023 al 2026 sono
    # entrati tutti in 17 secondi). id resta come spareggio deterministico.
    _order = "date_received desc, id desc"
    _primary_email = "email_from"

    color = fields.Integer(string="Color")
    # MULTI-COMPANY: il campo esiste ed e valorizzato dal default, ma in questo
    # todo NON viene creata alcuna ir.rule. Attenzione (non si risolve qui):
    # message_new gira in sudo() con with_user(related_user)
    # (odoo_core/odoo/addons/mail/models/mail_thread.py L1310), quindi
    # env.company e l'azienda dell'utente catch-all, NON quella del
    # destinatario. Derivare l'azienda dall'header To: e fuori scope.
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    user_id = fields.Many2one("res.users", string="Responsible")
    active = fields.Boolean(string="Active", default=True)
    name = fields.Char(string="Envelope Subject")
    email_from = fields.Char(string="From")
    email_to = fields.Char(string="To")
    body = fields.Html(string="Body")
    date_received = fields.Datetime(string="Received On")
    message_id = fields.Char(string="Message-Id", index="btree")
    # Stesso nome del campo core su mail.mail (mail/models/mail_mail.py L94),
    # ma NON lo stesso meccanismo: il default_fetchmail_server_id del core
    # (fetchmail.py L223) non arriva a message_new su un fetch avviato dal
    # pulsante, perche' le chiavi default_* vengono scartate lungo la strada.
    # Verificato a log su un fetch reale di 50 messaggi, e infatti il campo
    # core su mail.mail resta vuoto. Lo popola il nostro override di
    # fetchmail.server.fetch_mail via mailpec_fetchmail_server_id.
    # Resta VUOTO se il messaggio arriva per altra via: dichiarare un server
    # che non ha scaricato nulla sarebbe un dato inventato.
    fetchmail_server_id = fields.Many2one(
        "fetchmail.server",
        string="Inbound Mail Server",
        readonly=True,
        index="btree",
    )
    # Header X-Riferimento-Message-ID: collega la ricevuta al messaggio originale.
    pec_ref_message_id = fields.Char(string="PEC Reference Message-Id", index="btree")
    # Header X-Ricevuta. RESTA Char, NON va convertito in Selection: e' una
    # scelta deliberata, non un ripiego, e non va "migliorata".
    # Due ricerche indipendenti hanno prodotto elenchi di tipi DISCORDANTI.
    # Solo 4 valori sono provati da traffico reale (accettazione,
    # non-accettazione, avvenuta-consegna, posta-certificata); altri 6 vengono
    # dalla specifica e non sono verificati. Una Selection rifiuterebbe in
    # silenzio qualunque valore fuori elenco: su documenti con valore legale,
    # perdere il tipo di una ricevuta perche' il gestore ne ha emesso uno che
    # non avevamo previsto e' inaccettabile.
    pec_receipt_type = fields.Char(string="PEC Receipt Type")
    # Header X-Trasporto, grezzo. Presente sulle ricevute E sulla busta di
    # trasporto; vale "errore" sulla posta NON certificata.
    pec_transport = fields.Char(string="PEC Transport")
    # Selection chiusa, DELIBERATAMENTE al contrario di pec_receipt_type.
    # Quel campo rispecchia una tassonomia ESTERNA che non controlliamo e
    # sulla quale le fonti sono discordi: resta Char per non rifiutare in
    # silenzio un valore valido emesso da un gestore. pec_kind e' invece la
    # NOSTRA classificazione, prodotta dalla nostra logica su un insieme che
    # decidiamo noi, quindi l'enumerazione chiusa e' corretta: un valore
    # fuori elenco sarebbe un difetto del nostro codice, non del gestore.
    pec_kind = fields.Selection(
        selection=[
            ("ricevuta", "Ricevuta"),
            ("messaggio_pec", "Messaggio PEC"),
            ("non_certificata", "Non certificata"),
        ],
        string="Message Kind",
        index="btree",
    )
    # --- Messaggio originale, estratto da postacert.eml ------------------
    # Per messaggio_pec e non_certificata la busta esterna e' del gestore:
    # mittente e oggetto veri stanno DENTRO l'allegato. Sulla posta non
    # certificata questi due campi sono l'unico modo di filtrare spam e
    # phishing, che e' cio' che quel canale riceve.
    original_email_from = fields.Char(string="Original Sender")
    original_subject = fields.Char(string="Original Subject")
    # --- Esito certificato, estratto da daticert.xml ---------------------
    # Specchio dei valori che _parse_daticert sa leggere. Mittente e oggetto
    # dell'originale non sono replicati: il primo e' la nostra stessa casella,
    # il secondo e' gia' dentro `name` (l'oggetto della ricevuta cita quello
    # del messaggio), e la correlazione riporta comunque al record di origine.
    pec_error = fields.Char(string="PEC Error Code")
    pec_extended_error = fields.Text(string="PEC Extended Error")
    pec_receipt_detail = fields.Char(string="PEC Receipt Detail")
    pec_provider = fields.Char(string="PEC Issuing Provider")
    pec_receipt_date = fields.Datetime(string="PEC Receipt Date")
    pec_identifier = fields.Char(string="PEC Identifier", index="btree")
    pec_delivery = fields.Char(string="PEC Delivery Address")
    # Un destinatario per riga, "indirizzo (tipo)". Text e non modello figlio:
    # sono dati di sola lettura, mai cercati per relazione e tipicamente uno o
    # due. Il tipo certificato/esterno - che decide se il recapito ha valore
    # legale - resta leggibile accanto a ogni indirizzo.
    pec_recipients = fields.Text(string="PEC Recipients")
    # --- Correlazione al messaggio inviato -------------------------------
    # model/res_id arrivano dal mail.message trovato: puntano al record di
    # business SENZA che questo modulo debba conoscerlo. E' cio' che tiene il
    # modulo generico: niente pratiche, tutele o pagamenti qui dentro.
    origin_message_id = fields.Many2one(
        "mail.message",
        string="Original Message",
        index="btree",
    )
    origin_model = fields.Char(string="Original Model")
    origin_res_id = fields.Integer(string="Original Record ID")
    processed = fields.Boolean(string="Processed")
    state = fields.Selection(
        selection=[
            ("ricevuta", "Ricevuta"),
            ("elaborata", "Elaborata"),
            ("errore", "Errore"),
        ],
        string="Status",
        default="ricevuta",
    )
    # --- Presentazione per l'operatore -----------------------------------
    # email_from e' sempre la busta del gestore (posta-certificata@...): su
    # 156 messaggi reali assume 31 valori, tutti indirizzi di sistema. Non
    # identifica nessuno. Stored perche' e' la colonna principale della
    # lista e deve restare ordinabile, cercabile e raggruppabile.
    counterpart = fields.Char(
        string="Counterpart",
        compute="_compute_counterpart",
        store=True,
    )
    display_subject = fields.Char(
        string="Subject",
        compute="_compute_display_subject",
        store=True,
    )
    # sanitize esplicito benche' sia gia' il default: questo HTML arriva da
    # una mail ESTERNA, e la sanificazione e' l'unica difesa contro script
    # iniettati in un messaggio. Non e' una preferenza di formattazione.
    original_body = fields.Html(
        string="Original Body",
        compute="_compute_original_body",
        sanitize=True,
    )
    # Non letta = campo VUOTO. Un solo campo invece di booleano + utente:
    # l'assenza di un lettore e' gia' lo stato "da leggere", e i record gia'
    # a DB partono corretti senza migrazione.
    read_by_user_id = fields.Many2one(
        "res.users",
        string="Read By",
        readonly=True,
        index="btree",
        tracking=True,
    )

    @api.depends("pec_kind", "original_email_from", "email_from", "pec_recipients")
    def _compute_counterpart(self):
        """Con chi ha a che fare questa riga.

        Sui messaggi e' il mittente vero, sulle ricevute il destinatario del
        nostro invio: una ricevuta non ha un mittente umano, certifica una
        spedizione NOSTRA, quindi la controparte e' chi avevamo scritto.
        """
        for mail in self:
            if mail.pec_kind == "ricevuta":
                recipients = (mail.pec_recipients or "").splitlines()
                mail.counterpart = recipients[0].split(" (")[0] if recipients else ""
            else:
                source = mail.original_email_from or mail.email_from or ""
                mail.counterpart = parseaddr(source)[1] or source

    @api.depends("original_subject", "name")
    def _compute_display_subject(self):
        for mail in self:
            mail.display_subject = mail.original_subject or mail.name

    def _compute_original_body(self):
        """Corpo del solo messaggio umano, letto da ``postacert.eml``.

        NON memorizzato di proposito: il contenuto vive gia' nell'allegato,
        quindi cosi' funziona anche sui record atterrati prima che il campo
        esistesse, senza alcun riempimento retroattivo.

        ``original_email.eml`` NON va usato al suo posto, per quanto il nome
        lo suggerisca: e' l'intera busta scaricata (multipart/signed) e il suo
        corpo e' proprio il testo del gestore ("Messaggio di posta
        certificata", "Ricevuta di accettazione", "Anomalia nel messaggio").
        Il messaggio del mittente sta solo dentro postacert.eml.
        """
        # bin_size=False OBBLIGATORIO: il form legge in contesto bin_size=True e
        # in quel contesto attachment.raw restituisce la dimensione formattata
        # ("326.00 bytes") invece dei byte. Da shell non si vede, perche' quel
        # contesto non c'e': il difetto compare solo aprendo la scheda.
        attachments = (
            self.env["ir.attachment"]
            .sudo()
            .with_context(bin_size=False)
            .search(
                [
                    ("res_model", "=", self._name),
                    ("res_id", "in", self.ids),
                    ("name", "=", "postacert.eml"),
                ],
            )
        )
        by_record = {attachment.res_id: attachment for attachment in attachments}
        for mail in self:
            attachment = by_record.get(mail.id)
            mail.original_body = (
                self._pec_body_from_eml(attachment.raw) if attachment else False
            )

    @api.model
    def _pec_body_from_eml(self, raw):
        """HTML del corpo di un ``.eml``, o False se non si riesce a leggerlo.

        Solo logga: un corpo illeggibile non deve impedire l'apertura della
        scheda, dove restano comunque la busta e gli allegati originali.
        """
        try:
            message = message_from_bytes(raw, policy=policy.SMTP)
            part = message.get_body(preferencelist=("html", "plain"))
            if part is None:
                return False
            content = part.get_content()
            if part.get_content_type() == "text/plain":
                return plaintext2html(content)
            return content
        except Exception:
            _logger.exception("PEC: corpo di postacert.eml non leggibile")
            return False

    @api.model
    @api.readonly
    def web_search_read(
        self,
        domain,
        specification,
        offset=0,
        limit=None,
        order=None,
        count_limit=None,
    ):
        """Segnala a ``web_read`` che sta servendo un ELENCO, non una scheda.

        Serve perche' ``web_search_read`` del core chiama ``web_read`` al suo
        interno (web/models/models.py L46): senza questo flag, aprire la lista
        marcherebbe come lette tutte le righe caricate. Il flag viaggia nel
        contesto, che ``search_fetch`` propaga al recordset risultante.

        Resta ``@api.readonly`` come il core: con la guardia attiva questo
        ramo non scrive davvero nulla.
        """
        return super(
            MailpecMail,
            self.with_context(mailpec_listing=True),
        ).web_search_read(
            domain,
            specification,
            offset=offset,
            limit=limit,
            order=order,
            count_limit=count_limit,
        )

    def web_read(self, specification):
        """Marca il messaggio come letto quando se ne apre la scheda.

        La distinzione lista/scheda e' STRUTTURALE, non basata sui campi
        richiesti: si scrive solo quando la chiamata NON arriva da
        ``web_search_read``. Un controllo sulla presenza di ``body`` nella
        specification legherebbe il comportamento del modello al contenuto
        della vista, e si romperebbe in silenzio al primo ritocco del form.

        L'override NON ripete ``@api.readonly`` del core
        (web/models/models.py L77): questo ramo scrive, quindi readonly
        sarebbe falso. Senza quel decoratore la richiesta parte gia' in
        read/write ed evita il rollback-e-rilancia di http.py L2163-2169.

        Limite noto: un Many2one verso questo modello da un modulo esterno
        produrrebbe letture annidate di co-record (models.py L118) che
        marcherebbero come letti messaggi mai aperti. Oggi non accade: i
        consumatori si agganciano via origin_model/origin_res_id.
        """
        if not self.env.context.get("mailpec_listing"):
            unread = self.filtered(lambda mail: not mail.read_by_user_id)
            if unread:
                unread.sudo().write({"read_by_user_id": self.env.user.id})
        return super().web_read(specification)

    @api.model
    def _parse_daticert(self, xml_bytes):
        empty_result = {
            "receipt_type": "",
            "error": "",
            "sender": "",
            "subject": "",
            "recipients": [],
            "gestore": "",
            "date": False,
            "identificativo": "",
            "ref_message_id": "",
            "receipt_detail": "",
            "delivery": "",
            "extended_error": "",
        }
        if not xml_bytes:
            _logger.info("PEC daticert payload is missing")
            return empty_result

        try:
            root = ET.fromstring(xml_bytes)
            if root.tag != "postacert":
                _logger.info("PEC daticert has unexpected root element: %s", root.tag)
                return empty_result

            date_element = root.find("./dati/data")
            date_value = datetime.strptime(
                "%s %s %s"
                % (
                    date_element.findtext("giorno", default=""),
                    date_element.findtext("ora", default=""),
                    date_element.get("zona", ""),
                ),
                "%d/%m/%Y %H:%M:%S %z",
            )
            return {
                "receipt_type": root.get("tipo", ""),
                "error": root.get("errore", ""),
                "sender": root.findtext("./intestazione/mittente", default=""),
                "subject": root.findtext("./intestazione/oggetto", default=""),
                "recipients": [
                    {
                        "address": recipient.text or "",
                        "type": recipient.get("tipo", ""),
                    }
                    for recipient in root.findall("./intestazione/destinatari")
                ],
                "gestore": root.findtext("./dati/gestore-emittente", default=""),
                "date": date_value.astimezone(UTC).replace(tzinfo=None),
                "identificativo": root.findtext("./dati/identificativo", default=""),
                "ref_message_id": root.findtext("./dati/msgid", default=""),
                "receipt_detail": (
                    receipt.get("tipo", "")
                    if (receipt := root.find("./dati/ricevuta")) is not None
                    else ""
                ),
                "delivery": root.findtext("./dati/consegna", default=""),
                "extended_error": root.findtext("./dati/errore-esteso", default=""),
            }
        except (AttributeError, ET.ParseError, TypeError, ValueError) as error:
            _logger.info("PEC daticert could not be parsed: %s", error)
            return empty_result

    @api.model
    def _pec_daticert_bytes(self, msg_dict):
        """Ritorna i byte di ``daticert.xml``, o None se il messaggio non ne ha.

        Recupero PER NOME, mai per mimetype: il core forza gli XML in ingresso
        a text/plain (odoo_core/odoo/odoo/addons/base/models/ir_attachment.py
        L376-381, conseguenza di ``attachments_mime_plainxml=True`` in
        mail_thread.py L1294), quindi un filtro su application/xml non
        troverebbe nulla in produzione.

        Gli allegati si leggono da ``msg_dict`` e non da ``ir.attachment``:
        qui non esistono ancora, il core li collega dopo, in ``message_post``.
        """
        for attachment in msg_dict.get("attachments") or []:
            if attachment.fname == "daticert.xml":
                # _message_parse_extract_payload L1602 usa part.get_content():
                # str per i part text/*, bytes per gli altri. ET.fromstring
                # rifiuta una str che dichiara l'encoding, quindi si normalizza.
                content = attachment.content
                return content.encode() if isinstance(content, str) else content
        return None

    @api.model
    def _pec_kind(self, receipt_type, transport):
        """Classifica il messaggio nelle tre specie che una casella PEC riceve.

        I due header appartengono a categorie DISGIUNTE: l'Allegato tecnico al
        DM 2 novembre 2005 par. 6.3.4 definisce X-Trasporto sulle buste, ed e'
        proprio l'header con cui il punto di consegna riconosce una busta
        valida; X-Ricevuta sta su ricevute e avvisi. Riscontro sul traffico
        reale: 0 ricevute su 119 portano X-Trasporto.

        L'ordine e' quindi ridondante nei fatti, e resta come difesa: se un
        gestore emettesse entrambi gli header, una ricevuta va classificata
        ricevuta. NON e' vero - come diceva questo commento fino alla v1.6 -
        che una ricevuta porti entrambi gli header: quella motivazione era
        smentita sia dai dati sia dalla norma.

        Nessuna corrispondenza -> False, cioe' campo NON valorizzato. E' una
        decisione esplicita: NON esiste un quarto valore "sconosciuto", perche'
        aggiungerlo dichiarerebbe una classificazione che non e' avvenuta.
        Il record atterra comunque e resta visibile: nulla viene archiviato,
        scartato o dedotto per congettura. Il filtro "Non classificata" della
        vista di ricerca serve proprio a trovarli.
        """
        if receipt_type:
            return "ricevuta"
        if transport == "posta-certificata":
            return "messaggio_pec"
        if transport == "errore":
            return "non_certificata"
        _logger.info(
            "PEC: message kind undetermined (X-Ricevuta=%r, X-Trasporto=%r)",
            receipt_type,
            transport,
        )
        return False

    @api.model
    def _pec_original_message(self, msg_dict):
        """Ritorna il messaggio dentro ``postacert.eml``, o None se assente.

        Recupero PER NOME, mai per mimetype, per la stessa ragione di
        ``_pec_daticert_bytes``.

        Il contenuto e' gia' un oggetto ``Message``: su un part message/rfc822
        ``part.get_content()`` (mail_thread.py L1602) restituisce il messaggio
        annidato, non i byte, ed e' cosi' che il core lo tratta piu' avanti
        (mail_thread.py L2404-2405, ``content.as_bytes()``). I rami str/bytes
        esistono per prudenza, non perche' osservati.
        """
        for attachment in msg_dict.get("attachments") or []:
            if attachment.fname != "postacert.eml":
                continue
            content = attachment.content
            if isinstance(content, Message):
                return content
            if isinstance(content, str):
                return message_from_string(content, policy=policy.SMTP)
            return message_from_bytes(content, policy=policy.SMTP)
        return None

    def _pec_original_from_display_name(self):
        """Ripiego quando ``postacert.eml`` manca: il display name della busta.

        I gestori scrivono ``"Per conto di: <indirizzo reale>"
        <posta-certificata@...>``, quindi il mittente vero e' recuperabile
        anche senza allegato. L'oggetto NON ha ripiego: quello esterno e' del
        gestore ("ANOMALIA MESSAGGIO: ...") e spacciarlo per l'originale
        sarebbe peggio che lasciarlo vuoto.
        """
        self.ensure_one()
        display_name = parseaddr(self.email_from or "")[0]
        if not display_name.lower().startswith(ON_BEHALF_PREFIX):
            return {}
        return {"original_email_from": display_name[len(ON_BEHALF_PREFIX) :].strip()}

    def _pec_original_values(self, msg_dict):
        """Mittente e oggetto VERI dei messaggi che il gestore ha imbustato.

        Solo per messaggio_pec e non_certificata: su una ricevuta la busta
        esterna e' gia' il documento che conta.

        try/except che SOLO logga: una ricevuta ha valore legale e non si
        perde perche' l'originale non si e' potuto leggere.
        """
        self.ensure_one()
        if self.pec_kind not in ("messaggio_pec", "non_certificata"):
            return {}
        try:
            original = self._pec_original_message(msg_dict)
            if original is None:
                return self._pec_original_from_display_name()
            return {
                "original_email_from": decode_message_header(original, "From"),
                "original_subject": decode_message_header(original, "Subject"),
            }
        except Exception:
            _logger.exception(
                "PEC: original message wrapped in %s could not be read",
                self.message_id,
            )
            return {}

    def _pec_outcome_values(self, parsed):
        """Traduce il dict di ``_parse_daticert`` nei campi del record."""
        self.ensure_one()
        return {
            # Header e XML dicono la stessa cosa (verificato: msgid == header
            # su 15 campioni su 15). L'header ha la precedenza perche' e' gia'
            # sul record; l'XML vale come conferma, e come ripiego quando il
            # gestore non ha emesso l'header.
            "pec_receipt_type": self.pec_receipt_type or parsed["receipt_type"],
            "pec_ref_message_id": self.pec_ref_message_id or parsed["ref_message_id"],
            "pec_error": parsed["error"],
            "pec_extended_error": parsed["extended_error"],
            "pec_receipt_detail": parsed["receipt_detail"],
            "pec_provider": parsed["gestore"],
            "pec_receipt_date": parsed["date"],
            "pec_identifier": parsed["identificativo"],
            "pec_delivery": parsed["delivery"],
            "pec_recipients": "\n".join(
                "%s (%s)" % (recipient["address"], recipient["type"])
                for recipient in parsed["recipients"]
            ),
            "state": "elaborata",
        }

    def _pec_correlation_values(self, ref_message_id):
        """Risale al messaggio che abbiamo inviato, dal Message-ID di riferimento.

        ``mail.message.message_id`` e' indicizzato (mail_message.py L178) e
        sempre valorizzato alla create (L645-646): e' lo stesso aggancio che il
        core usa per i thread (mail_thread.py L1151-1153).

        Una sola lookup basta anche per le avvenute consegne: su campioni reali
        accettazione e avvenuta-consegna dello stesso invio portano un
        ``X-Riferimento-Message-ID`` IDENTICO. Nessuna tabella di
        corrispondenza msgid originale -> msgid della busta di trasporto.

        Solo logga: se non trova nulla la ricevuta atterra comunque, senza
        riferimento.
        """
        if not ref_message_id:
            return {}
        try:
            message = (
                self.env["mail.message"]
                .sudo()
                .search([("message_id", "=", ref_message_id)], limit=1)
            )
        except Exception:
            _logger.exception("PEC: correlation lookup failed for %s", ref_message_id)
            return {}
        if not message:
            _logger.info("PEC: no sent message matches %s", ref_message_id)
            return {}
        return {
            "origin_message_id": message.id,
            "origin_model": message.model or False,
            "origin_res_id": message.res_id or 0,
        }

    def _pec_receipt_values(self, xml_bytes):
        """Esito + correlazione da scrivere sul record, o lo stato di errore."""
        self.ensure_one()
        parsed = self._parse_daticert(xml_bytes)
        if not parsed["receipt_type"]:
            # C'e' un daticert.xml ma non e' interpretabile: lo si dichiara,
            # non lo si nasconde. Il messaggio resta comunque a DB.
            return {"state": "errore"}
        values = self._pec_outcome_values(parsed)
        values.update(self._pec_correlation_values(values["pec_ref_message_id"]))
        return values

    def _pec_process_receipt(self, msg_dict):
        """Estrae l'originale imbustato, interpreta ``daticert.xml``, correla.

        Due ``try/except`` DISTINTI e non uno solo: l'originale dentro
        ``postacert.eml`` e la certificazione sono indipendenti, e il
        fallimento del primo non deve impedire la lettura della seconda.
        Entrambi SOLO loggano, sul modello di
        aiutotel_base/models/aiutotel_mail.py L413-419: una ricevuta PEC ha
        valore legale e non si perde perche' l'interpretazione fallisce.
        Un'unica ``write`` finale, cosi' un errore non lascia il record a meta'.
        """
        self.ensure_one()
        values = self._pec_original_values(msg_dict)
        try:
            xml_bytes = self._pec_daticert_bytes(msg_dict)
            # Senza daticert.xml non c'e' nulla da certificare: e' il caso
            # normale della posta non certificata, ed e' anche cio' che
            # succede con fetchmail e "Keep Attachments" disattivato. Il
            # messaggio resta grezzo; non e' un errore di elaborazione.
            if xml_bytes:
                values.update(self._pec_receipt_values(xml_bytes))
        except Exception:
            _logger.exception(
                "PEC: outcome of receipt %s could not be read",
                self.message_id,
            )
            values["state"] = "errore"
        if values:
            self.write(values)

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """Crea la ricevuta PEC dal messaggio in ingresso.

        I valori vanno passati a super() COME custom_values, non scritti dopo:
        message_new del core fa `self.create(custom_values.copy() | {...})`
        (odoo_core/odoo/addons/mail/models/mail_thread.py L1453-1465), quindi
        un unico create() vede tutti i campi. email_from NON si imposta qui:
        lo popola il core dal mittente del messaggio (stesso file, L1461-1463)
        SOLO perche' questo modello dichiara _primary_email = "email_from"
        (requisito esplicito in mail_thread.py L103). Senza quella dichiarazione
        _mail_get_primary_email_field ritorna None e il campo resta vuoto.

        custom_values (pec_ref_message_id / pec_receipt_type, iniettati da
        message_route) sovrascrive i default: viene dagli header, ha priorita.

        L'interpretazione arriva DOPO la create, in ``_pec_process_receipt``, e
        non prima: la ricevuta esiste a DB anche se il parsing esplode.
        """
        # msg_dict["date"] NON e' una chiave garantita: message_parse la imposta
        # solo dentro `if message.get('Date')`
        # (odoo_core/odoo/addons/mail/models/mail_thread.py L1781-1797), quindi
        # senza header Date: e' ASSENTE. Quando c'e' e' una STRINGA
        # '%Y-%m-%d %H:%M:%S' gia' normalizzata a UTC dal core; to_datetime la
        # riporta a datetime naive UTC senza toccare il fuso.
        message_date = msg_dict.get("date")
        if message_date:
            date_received = fields.Datetime.to_datetime(message_date)
        else:
            date_received = fields.Datetime.now()
            _logger.info(
                "PEC message %s has no Date header: date_received falls back to "
                "ingestion time %s, which is NOT the legal date of the receipt.",
                msg_dict.get("message_id"),
                date_received,
            )

        defaults = {
            "name": msg_dict.get("subject") or _("Senza oggetto"),
            "email_to": msg_dict.get("to", ""),
            "body": msg_dict.get("body", ""),
            "message_id": msg_dict.get("message_id"),
            "date_received": date_received,
            "state": "ricevuta",
        }
        # Chiave posata dal nostro override di fetchmail.server.fetch_mail:
        # quella del core (default_fetchmail_server_id) non arriva fin qui.
        defaults["fetchmail_server_id"] = self.env.context.get(
            "mailpec_fetchmail_server_id",
            False,
        )
        defaults.update(custom_values or {})
        # Nei defaults, NON in una write successiva: _pec_original_values
        # legge self.pec_kind subito dopo la create per decidere se estrarre
        # l'originale. (message_route cattura gli header grezzi; interpretarli
        # spetta a questo modello.)
        defaults["pec_kind"] = self._pec_kind(
            defaults.get("pec_receipt_type"),
            defaults.get("pec_transport"),
        )
        record = super().message_new(msg_dict, defaults)
        record._pec_process_receipt(msg_dict)
        return record
