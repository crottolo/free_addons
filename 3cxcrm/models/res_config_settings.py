from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    token_3cx_crm = fields.Char(
        string="3CX API Token",
        config_parameter="crm.3cx.auth",
        help="API key used by 3CX PBX to authenticate requests to Odoo.",
    )
