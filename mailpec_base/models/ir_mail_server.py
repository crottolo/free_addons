import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class IrMailServer(models.Model):
    _inherit = "ir.mail_server"

    is_pec = fields.Boolean(
        string="Casella PEC",
        help="Esclude il server dalla selezione automatica e forza l'envelope "
        "sender all'indirizzo PEC.",
    )
    pec_email_from = fields.Char(
        string="Indirizzo PEC",
        help="Indirizzo della casella autenticata sul server.",
    )

    def _get_test_email_from(self):
        if self.is_pec and self.pec_email_from:
            return self.pec_email_from
        return super()._get_test_email_from()

    def _find_mail_server(self, email_from, mail_servers=None):
        """Esclude sempre i server PEC dalla selezione automatica.

        Il filtro va applicato anche quando ``mail_servers`` arriva gia
        valorizzato: mail_mail.py L574-585 lo passa posizionale e non nullo,
        quindi filtrare solo il ramo ``is None`` non avrebbe effetto nel
        percorso reale, e una PEC con ``from_filter`` vuoto e ``sequence``
        bassa intercetterebbe tutta la posta ordinaria (ir_mail_server.py
        L834-835).
        """
        if mail_servers is None:
            mail_servers = self.sudo().search([], order="sequence, id")
        return super()._find_mail_server(
            email_from,
            mail_servers.filtered(lambda s: not s.is_pec),
        )
