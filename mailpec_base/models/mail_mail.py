import logging

from odoo import models

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = "mail.mail"

    def _prepare_outgoing_list(
        self,
        mail_server=False,
        recipients_follower_status=None,
    ):
        """Forza il Return-Path all'indirizzo della casella PEC.

        Il core deriva sia l'header sia il context ``domain_bounce_address`` da
        questo metodo (mail_mail.py L426 e L742). Impostare l'header piu a
        valle, dentro ``send_email``, non basta: a ir_mail_server.py L651 il
        context ha la precedenza sull'header e l'envelope sender resterebbe
        l'indirizzo di bounce dell'azienda, facendo rifiutare la PEC dal gestore.
        """
        email_list = super()._prepare_outgoing_list(
            mail_server,
            recipients_follower_status,
        )
        server = mail_server or self.mail_server_id
        if server.is_pec and server.pec_email_from:
            for email in email_list:
                email["headers"]["Return-Path"] = server.pec_email_from
        return email_list
