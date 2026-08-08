import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.mail import email_normalize

_logger = logging.getLogger(__name__)


class IrMailServer(models.Model):
    _inherit = "ir.mail_server"

    is_pec = fields.Boolean(
        string="Casella PEC",
        help="Forza envelope sender, Return-Path e Reply-To all'indirizzo "
        "indicato in 'Filtro mittente', ed esclude il server dalla selezione "
        "automatica per la posta ordinaria.",
    )

    def _mailpec_address(self):
        """Indirizzo della casella PEC, letto da ``from_filter``.

        Non esiste un campo dedicato: sarebbe un duplicato di ``from_filter``,
        che DEVE comunque contenere l'indirizzo PEC. Con due campi separati i
        valori possono divergere, ed e' cosi' che un messaggio finisce per
        uscire da una casella certificata diversa da quella dichiarata.

        La regola di lettura e' la stessa del core (``_get_test_email_from``,
        ir_mail_server.py L272-274): la prima voce che contiene una chiocciola.
        Manca invece il ripiego del core su ``noreply@<dominio>``: su una PEC un
        indirizzo inventato non e' la casella autenticata, e il gestore lo
        rifiuterebbe. Il vincolo qui sotto rende comunque il caso impossibile.

        Ritorna False su un server non PEC: ``from_filter`` esiste su tutti i
        server, e senza questo controllo il metodo restituirebbe l'indirizzo di
        una casella ordinaria smentendo il proprio nome. False anche su
        recordset vuoto, perche' ``is_pec`` vi vale False.
        """
        if not self.is_pec:
            return False
        parts = [
            part.strip() for part in (self.from_filter or "").split(",") if part.strip()
        ]
        return next((part for part in parts if "@" in part), False)

    @api.constrains("is_pec", "from_filter")
    def _check_mailpec_from_filter(self):
        """Su una casella PEC il filtro mittente e' UN SOLO indirizzo completo.

        ``from_filter`` ammette per il core una lista di indirizzi o domini.
        Su una PEC nessuna delle due varianti regge: con piu' voci non si sa
        quale casella autentichi, e un dominio nudo non e' un indirizzo. Senza
        questo vincolo il campo verrebbe letto a vuoto e il modulo smetterebbe
        di riconoscere il server, in silenzio.
        """
        for server in self:
            if not server.is_pec:
                continue
            parts = [
                part.strip()
                for part in (server.from_filter or "").split(",")
                if part.strip()
            ]
            if len(parts) != 1 or "@" not in parts[0]:
                raise ValidationError(
                    _(
                        "Sul server \"%(server)s\" il campo 'Filtro mittente' deve "
                        "contenere UN SOLO indirizzo completo, quello della casella "
                        "PEC autenticata (es. azienda@pec.esempio.it). Valore "
                        "attuale: %(value)s",
                        server=server.name or "-",
                        value=server.from_filter or _("(vuoto)"),
                    ),
                )

    def _mailpec_owns_sender(self, email_from):
        """Questo server e' la casella PEC da cui quel mittente deve uscire.

        Predicato unico, usato dalla selezione automatica, dalla create di
        ``mail.mail`` e dal riallineamento in invio: se usassero criteri
        diversi, il record dichiarerebbe un server e la spedizione ne userebbe
        un altro.

        Sicuro su recordset vuoto: ``self.is_pec`` vale False, quindi "nessun
        server" non possiede mai un mittente PEC.
        """
        sender = email_normalize(email_from)
        if not sender or not self.is_pec:
            return False
        address = self._mailpec_address()
        return bool(address and email_normalize(address) == sender)

    def _mailpec_server_for_sender(self, email_from):
        """Il server PEC da cui quel mittente deve uscire, o recordset vuoto.

        La scelta e' DELEGATA a ``_find_mail_server``, non rifatta qui con un
        filtro proprio: se le due divergessero, il record verrebbe creato
        indicando un server e l'invio ne userebbe un altro.
        """
        server, _sender = self.sudo()._find_mail_server(email_from)
        if server and server._mailpec_owns_sender(email_from):
            return server
        return self.browse()

    def _find_mail_server(self, email_from, mail_servers=None):
        """Esclude i server PEC dalla selezione automatica, TRANNE il proprio.

        Un server PEC resta candidato solo per la SUA casella, cioe' quando il
        mittente coincide con il suo indirizzo. Le due esigenze sono opposte e
        vanno tenute entrambe:

        - la posta ORDINARIA non deve mai uscire da una PEC. Il passo 4 del
          core (ir_mail_server.py L837-842) ripiega sul PRIMO server
          dell'elenco quando nessun ``from_filter`` combacia: senza esclusione
          quel ripiego puo' essere una casella certificata;
        - la posta della PEC deve trovare il suo server ANCHE senza
          ``mail_server_id`` sul template. Con l'esclusione incondizionata,
          dimenticarlo mandava il messaggio su un server qualunque con envelope
          sbagliato, e il gestore lo avrebbe rifiutato: un fallimento silenzioso
          al primo template dimenticato.

        Il filtro va applicato anche quando ``mail_servers`` arriva gia
        valorizzato: mail_mail.py L574-585 lo passa posizionale e non nullo,
        quindi agire solo sul ramo ``is None`` non avrebbe effetto nel percorso
        reale.
        """
        if mail_servers is None:
            mail_servers = self.sudo().search([], order="sequence, id")
        return super()._find_mail_server(
            email_from,
            mail_servers.filtered(
                lambda server: not server.is_pec
                or server._mailpec_owns_sender(email_from),
            ),
        )
