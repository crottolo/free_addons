from odoo import api, models
from odoo.tools.mail import decode_message_header


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _mailpec_declared_box(self):
        """La casella di ricezione e' stata dichiarata PEC dall'operatore.

        E' l'unico criterio che non deduce nulla dal messaggio, quindi l'unico
        che regge con un gestore mai visto e con la posta di servizio del
        gestore, che PEC non e' e header PEC non ne ha.

        Vale SOLO sul percorso ``fetch_mail``, perche' la chiave di contesto la
        posa il nostro override di ``fetchmail.server``. Per questo e' un ramo
        in OR e non una condizione: usarlo come requisito escluderebbe i
        messaggi entrati per altra via, cioe' esattamente la perdita silenziosa
        che questo modulo esiste per evitare.
        """
        server_id = self.env.context.get("mailpec_fetchmail_server_id")
        if not server_id:
            return False
        return self.env["fetchmail.server"].sudo().browse(server_id).is_pec

    def _mailpec_declared_sender(self, message_dict):
        """Il mittente e' la busta di un gestore.

        Normativo per le BUSTE: l'Allegato tecnico al DM 2 novembre 2005, par.
        6.3.4, prescrive alla lettera
        ``From: "Per conto di: ..." <posta-certificata@[dominio_di_posta]>``.
        Per le RICEVUTE quella prescrizione NON esiste: li' il criterio e' solo
        empirico (119 ricevute su 119 nel traffico reale, ma concentrate su due
        gestori su una ventina accreditati). Per questo non puo' piu' essere
        l'unico discriminante.

        Il confronto e' sull'header ``From``, non sull'envelope sender:
        ``message_parse`` valorizza ``email_from`` da ``From``
        (mail/models/mail_thread.py L1749), ed e' il campo giusto, perche' la
        norma impone che i dati di instradamento restino quelli del messaggio
        originale.
        """
        pec_senders = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("mailpec_base.pec_senders", "")
        )
        if not pec_senders:
            return False
        email_from = message_dict.get("email_from", "").lower()
        return any(
            sender.strip().lower() in email_from
            for sender in pec_senders.split(",")
            if sender.strip()
        )

    @api.model
    def message_route(
        self,
        message,
        message_dict,
        model=None,
        thread_id=None,
        custom_values=None,
    ):
        """Instrada i messaggi PEC in ingresso su mailpec.mail.

        Tre criteri in OR, nessuno sufficiente da solo:

        1. header PEC, mandati dall'Allegato tecnico al DM 2 novembre 2005
           ciascuno per la propria categoria (``X-Trasporto`` sulle buste,
           ``X-Ricevuta`` su ricevute e avvisi). Coprono ogni gestore per
           costruzione e valgono su qualunque canale, ma non esistono sulla
           posta di servizio del gestore;
        2. casella dichiarata PEC, che copre anche quella;
        3. mittente, che resta come ripiego.

        Gli header si leggono QUI, non in ``message_new``: ``message_parse``
        ritorna un dict a chiavi FISSE (mail/models/mail_thread.py L1705-1744),
        quindi gli header custom non ci arrivano mai. ``message_route`` e'
        l'unico punto che ha ancora il ``message`` grezzo. Il core inoltra
        ``custom_values`` a ``message_new`` a mail_thread.py L1319.
        """
        receipt_type = decode_message_header(message, "X-Ricevuta")
        # Presente sulle buste, MAI sulle ricevute (par. 6.3.4: e' l'header con
        # cui il punto di consegna riconosce una busta valida). Unico
        # discriminante fra un messaggio PEC autentico e posta ordinaria non
        # certificata, che il gestore reimbusta dallo stesso indirizzo. Vale
        # "posta-certificata" oppure "errore"; classificare spetta a
        # mailpec.mail._pec_kind.
        transport = decode_message_header(message, "X-Trasporto")

        if (
            receipt_type
            or transport
            or self._mailpec_declared_box()
            or self._mailpec_declared_sender(message_dict)
        ):
            # thread_id DEVE restare None, NON va "corretto" a 0: il controllo
            # anti-loop fa `search_new = 0 in thread_ids` (mail_thread.py
            # L1001). Con None non scatta. Con 0, la soglia di 20 messaggi in
            # 120 minuti dallo stesso mittente (L984-985) SCARTEREBBE TUTTE le
            # ricevute, che arrivano tutte dallo stesso posta-certificata@.
            return [
                (
                    "mailpec.mail",
                    None,
                    {
                        "pec_ref_message_id": decode_message_header(
                            message,
                            "X-Riferimento-Message-ID",
                        ),
                        "pec_receipt_type": receipt_type,
                        "pec_transport": transport,
                    },
                    self._uid,
                    None,
                ),
            ]

        return super().message_route(
            message,
            message_dict,
            model,
            thread_id,
            custom_values,
        )
