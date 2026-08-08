import ast
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = "mail.mail"

    @api.model_create_multi
    def create(self, vals_list):
        """Scrive server, Reply-To e Return-Path PEC GIA' SUL RECORD.

        Correggere solo all'invio non basta: se lo SMTP e' irraggiungibile il
        messaggio resta in coda con i valori del core (catchall e bounce
        dell'alias domain), e a ogni ritentativo la correttezza dipende da quale
        server viene risolto in quel momento. Scrivendoli alla create il record
        e' corretto da subito, il ritentativo non ricalcola nulla, e cio' che si
        vede su ``mail.mail`` e' cio' che partira'.

        ``mail_server_id`` e ``reply_to`` vivono su ``mail.message``
        (``_inherits``), quindi valgono per tutte le notifiche di quel
        messaggio; ``headers`` e' invece un campo proprio di ``mail.mail``.

        ``email_from`` NON e' nei vals delle notifiche: ``base_mail_values``
        contiene solo mail_message_id, references, subject e headers
        (mail_thread.py, _notify_by_email_get_base_mail_values), e il mittente
        arriva dal messaggio. Va quindi letto da entrambe le parti.
        """
        servers = self.env["ir.mail_server"]
        # Fuori dal ciclo di proposito: dentro, una spedizione di massa
        # pagherebbe una ricerca server per ogni messaggio creato.
        pec_servers = servers.sudo().search([("is_pec", "=", True)])
        if not pec_servers:
            return super().create(vals_list)
        for vals in vals_list:
            sender = self._mailpec_sender(vals)
            if not pec_servers.filtered(
                lambda pec, sender=sender: pec._mailpec_owns_sender(sender),
            ):
                continue
            server = servers._mailpec_server_for_sender(sender)
            if not server:
                continue
            address = server._mailpec_address()
            vals["mail_server_id"] = server.id
            vals["reply_to"] = address
            vals["headers"] = self._mailpec_headers(
                vals.get("headers"),
                address,
            )
        return super().create(vals_list)

    @api.model
    def _mailpec_sender(self, vals):
        """Il mittente di una mail in creazione, dai vals o dal messaggio."""
        if vals.get("email_from"):
            return vals["email_from"]
        if vals.get("mail_message_id"):
            return (
                self.env["mail.message"]
                .sudo()
                .browse(vals["mail_message_id"])
                .email_from
            )
        return False

    @api.model
    def _mailpec_headers(self, raw, return_path):
        """Aggiunge il Return-Path agli header memorizzati, conservando gli altri.

        Gli header esistenti NON si sovrascrivono in blocco: il core ci mette
        ``X-Odoo-Objects``, che collega la mail al record e va conservato.

        Il parsing solo logga, come fa il core (mail_mail.py L410-425): un
        valore malformato non deve impedire la creazione del messaggio.
        """
        headers = {}
        if raw:
            try:
                headers = ast.literal_eval(raw)
            except Exception:
                _logger.warning("PEC: header non interpretabili, ignorati: %r", raw)
                headers = {}
        headers["Return-Path"] = return_path
        return repr(headers)

    def _prepare_outgoing_list(
        self,
        mail_server=False,
        recipients_follower_status=None,
    ):
        """Ultima difesa: riallinea Return-Path e Reply-To alla casella PEC.

        Con i valori scritti alla create questo ramo e' ridondante sui messaggi
        nuovi, e resta per i due casi in cui il record non li ha: le mail
        entrate in coda PRIMA di questa versione, e quelle create da percorsi
        che non passano per ``create`` con il mittente valorizzato.

        Il punto e' obbligato: il core deriva sia l'header sia il context
        ``domain_bounce_address`` da questo metodo (mail_mail.py L426 e L742).
        Impostare l'header piu a valle, dentro ``send_email``, non basta, perche'
        a ir_mail_server.py L651 il context ha la precedenza sull'header e
        l'envelope sender resterebbe l'indirizzo di bounce dell'azienda.
        """
        email_list = super()._prepare_outgoing_list(
            mail_server,
            recipients_follower_status,
        )
        server = mail_server or self.mail_server_id
        address = server._mailpec_address()
        if address:
            for email in email_list:
                email["headers"]["Return-Path"] = address
                email["reply_to"] = address
        return email_list
