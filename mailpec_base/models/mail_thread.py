from odoo import api, models
from odoo.tools.mail import decode_message_header


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.model
    def message_route(
        self,
        message,
        message_dict,
        model=None,
        thread_id=None,
        custom_values=None,
    ):
        """Route incoming PEC receipts to mailpec.mail.

        The PEC headers are captured HERE, not in ``message_new``, because
        ``message_parse`` returns a dict with FIXED keys
        (odoo_core/odoo/addons/mail/models/mail_thread.py L1705-1744), so custom
        headers NEVER reach ``message_new``. ``message_route`` is the only place
        still holding the raw ``message``. The core forwards ``custom_values``
        to ``message_new`` at mail_thread.py L1319.
        """
        pec_senders = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("mailpec_base.pec_senders", "")
        )
        if not pec_senders:
            return super().message_route(
                message,
                message_dict,
                model,
                thread_id,
                custom_values,
            )

        email_from = message_dict.get("email_from", "").lower()
        allowed_senders = [
            sender.strip().lower()
            for sender in pec_senders.split(",")
            if sender.strip()
        ]

        for allowed_sender in allowed_senders:
            if allowed_sender in email_from:
                # thread_id MUST stay None, do NOT "fix" it to 0: the anti-loop
                # check does `search_new = 0 in thread_ids` (mail_thread.py
                # L1001). With None it does not trigger. With 0, the threshold of
                # 20 messages per 120 minutes from the same sender (L984-985)
                # would DISCARD ALL PEC receipts, since every receipt arrives
                # from the same posta-certificata@... address.
                return [
                    (
                        "mailpec.mail",
                        None,
                        {
                            "pec_ref_message_id": decode_message_header(
                                message,
                                "X-Riferimento-Message-ID",
                            ),
                            "pec_receipt_type": decode_message_header(
                                message,
                                "X-Ricevuta",
                            ),
                            # Only discriminator between a genuine incoming
                            # PEC message and ordinary NON-certified mail:
                            # the provider re-sends both from the SAME
                            # posta-certificata@<domain> address. Captured
                            # raw; classifying is mailpec.mail._pec_kind.
                            "pec_transport": decode_message_header(
                                message,
                                "X-Trasporto",
                            ),
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
