from odoo import models, fields, api, _
from random import randint


def _get_default_color(self):
    return randint(1, 11)


class ResPartner(models.Model):
    _inherit = "res.partner"


    color = fields.Integer(string='Color', default=_get_default_color)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id.id)

    ateco_category_ids = fields.Many2many(
        comodel_name="atecoit.category",
        relation="ateco_category_partner_rel",
        column1="partner_id",
        column2="ateco_id",
        string="Ateco categories",
    )



#################################################################################################
#                                    ONCHANGE && COMPUTE                                        #
#################################################################################################



#################################################################################################
#                                 SMARTBUTTON & COUNT VALUE                                     #
#################################################################################################



#################################################################################################
#                                        BUTTON FUNCTION                                        #
#################################################################################################



#################################################################################################
#                              ORM FUNCTION DEFAULT & OVVERRIDE                                 #
#################################################################################################




#################################################################################################
#                                      CUSTOM FUNCTION                                          #
#################################################################################################


