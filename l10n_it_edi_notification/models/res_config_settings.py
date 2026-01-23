from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_it_edi_notification_channel_id = fields.Many2one(
        "discuss.channel",
        string="SDI Notification Channel",
        help="Odoo channel where daily SDI summaries will be posted",
    )

    l10n_it_edi_create_activity = fields.Boolean(
        string="Create Activity for SDI Errors",
        config_parameter="l10n_it_edi_notification.create_activity",
        default=False,
        help="If enabled, creates a mail.activity for rejected invoices",
    )

    l10n_it_edi_default_notification_user_id = fields.Many2one(
        "res.users",
        string="Fallback Notification User",
        help="User who receives SDI summary emails. "
        "If not set, only the channel notification is sent.",
    )

    def set_values(self):
        super().set_values()
        params = self.env["ir.config_parameter"].sudo()

        # Save channel ID
        params.set_param(
            "l10n_it_edi_notification.notification_channel_id",
            self.l10n_it_edi_notification_channel_id.id
            if self.l10n_it_edi_notification_channel_id
            else "",
        )

        # Save fallback user ID
        params.set_param(
            "l10n_it_edi_notification.default_user_id",
            self.l10n_it_edi_default_notification_user_id.id
            if self.l10n_it_edi_default_notification_user_id
            else "",
        )

    @api.model
    def get_values(self):
        res = super().get_values()
        params = self.env["ir.config_parameter"].sudo()

        # Get channel
        channel_id = params.get_param(
            "l10n_it_edi_notification.notification_channel_id",
        )
        # Get fallback user
        user_id = params.get_param("l10n_it_edi_notification.default_user_id")

        res.update(
            l10n_it_edi_notification_channel_id=int(channel_id)
            if channel_id
            else False,
            l10n_it_edi_default_notification_user_id=int(user_id) if user_id else False,
        )
        return res
