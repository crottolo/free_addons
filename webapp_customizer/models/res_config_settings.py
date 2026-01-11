# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # PWA icon field (stored as attachment)
    pwa_icon = fields.Binary(
        string="Progressive Web App Icon",
        help="Icon shown when installing Odoo as a Progressive Web App",
    )

    @api.model
    def default_get(self, fields_list):
        """Load PWA icon from attachment"""
        defaults = super().default_get(fields_list)
        if "pwa_icon" in fields_list:
            attachment = (
                self.env["ir.attachment"]
                .sudo()
                .search(
                    [
                        ("name", "=", "pwa_icon"),
                        ("res_model", "=", "ir.config_parameter"),
                        ("res_id", "=", 0),
                    ],
                    limit=1,
                )
            )
            if attachment:
                defaults["pwa_icon"] = attachment.datas
        return defaults

    def set_values(self):
        """Save PWA icon as attachment"""
        super().set_values()

        # Handle PWA icon
        if self.pwa_icon:
            # Remove existing attachment
            old_attachment = (
                self.env["ir.attachment"]
                .sudo()
                .search(
                    [
                        ("name", "=", "pwa_icon"),
                        ("res_model", "=", "ir.config_parameter"),
                        ("res_id", "=", 0),
                    ],
                )
            )
            old_attachment.unlink()

            # Create new attachment
            self.env["ir.attachment"].sudo().create(
                {
                    "name": "pwa_icon",
                    "type": "binary",
                    "datas": self.pwa_icon,
                    "res_model": "ir.config_parameter",
                    "res_id": 0,
                    "mimetype": "image/png",
                },
            )
