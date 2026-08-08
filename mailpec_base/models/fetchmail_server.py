from odoo import fields, models


class FetchmailServer(models.Model):
    _inherit = "fetchmail.server"

    is_pec = fields.Boolean(
        string="Casella PEC",
        help="Instrada su mailpec.mail TUTTO cio' che arriva da questo server, "
        "anche i messaggi di servizio del gestore.",
    )

    def fetch_mail(self, raise_exception=True):
        """Porta l'id del server in una chiave di contesto NON prefissata ``default_``.

        Il core lo passa come ``default_fetchmail_server_id``
        (mail/models/fetchmail.py L223), ma su un fetch avviato dal pulsante
        "Recupera ora" quella chiave non arriva a ``message_new``: verificato a
        log durante un fetch reale di 50 messaggi, dove
        ``fetchmail_cron_running=True`` passava e
        ``default_fetchmail_server_id`` risultava None con l'elenco delle
        chiavi ``default_*`` VUOTO. Il campo omonimo del core su ``mail.mail``
        resta vuoto per la stessa ragione, quindi non e' un difetto di questo
        modulo ne' qualcosa che si possa correggere restando su quel canale.

        Si itera qui un server alla volta perche' il contesto deve portare
        l'id di QUELLO in lavorazione, non dell'ultimo del recordset.
        """
        for server in self:
            super(
                FetchmailServer,
                server.with_context(mailpec_fetchmail_server_id=server.id),
            ).fetch_mail(raise_exception=raise_exception)
        return True
