from odoo import models, fields, api, _
from random import randint
from odoo.exceptions import UserError
from odoo.tools import translate


class ResPartner(models.Model):
    _inherit = 'res.partner'
    

    identity_ids = fields.One2many('partner.identity', 'partner_id', string='Identities')






#################################################################################################
#                                      CUSTOM FUNCTION                                          #
#################################################################################################

    


#################################################################################################
#################################################################################################
#################################################################################################

def _get_default_color(self):
    return randint(1, 11)


class PartnerIdentity(models.Model):
    
    _name = 'partner.identity'
    _description = 'partner.identity'
    
    color = fields.Integer(string='Color', default=_get_default_color)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id.id)
    active = fields.Boolean(string='Active', default=True)
    name = fields.Char(string='Name')
    partner_id = fields.Many2one('res.partner', string='Partner')
    document_type_id = fields.Many2one('partner.identity.type', string='Type')
    document_number = fields.Char(string='Number')
    document_expiration_date = fields.Date(string='Expiration Date')
    document_issuing_authority = fields.Char(string='Issuing Authority')
    document_issuing_date = fields.Date(string='Issuing Date')

    attachment_id = fields.Binary(string='Attachment', attachment=True)
    file_name = fields.Char(string='File Name')



#################################################################################################
#                                    ONCHANGE && COMPUTE                                        #
#################################################################################################

    @api.constrains('document_issuing_date', 'document_expiration_date')
    def _check_document_issuing_date(self):
        if self.document_issuing_date and self.document_expiration_date:
            if self.document_issuing_date > self.document_expiration_date:
                raise UserError(_('The issuing date cannot be greater than the expiration date'))

#################################################################################################
#                                 SMARTBUTTON & COUNT VALUE                                     #
#################################################################################################



#################################################################################################
#                                        BUTTON FUNCTION                                        #
#################################################################################################



#################################################################################################
#                              ORM FUNCTION DEFAULT & OVVERRIDE                                 #
#################################################################################################


    #@api.model_create_multi
    #def create(self, vals_list):
        #for values in vals_list:
            #res = super().create(values)
            #code = self.env['ir.sequence'].next_by_code('model.technical.name')
            #res.code = code
            #return res





#################################################################################################
#                                      CUSTOM FUNCTION                                          #
#################################################################################################


    
        






#################################################################################################
#################################################################################################
#################################################################################################


class PartnerIdentityType(models.Model):
    _name = 'partner.identity.type'
    _description = 'partner.identity.type'
    _order = 'sequence'
    
    
    name = fields.Char(string='Name', translate=True)
    color = fields.Integer(string='Color', default=_get_default_color)
    sequence = fields.Integer(string='Sequence')
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id.id)