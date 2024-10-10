from odoo import models, fields, api, _
from random import randint
from odoo.exceptions import UserError
from odoo.tools import translate


class ResPartner(models.Model):
    _inherit = 'res.partner'
    

    identity_ids = fields.One2many('partner.identity', 'partner_id', string='Identities')

    doc_type = fields.Char(string='Type Document')
    doc_number = fields.Char(string='Number Document')
    doc_issuing_date = fields.Date(string='Issuing Date')
    doc_expiration_date = fields.Date(string='Expiration Date')
    doc_issuing_authority = fields.Char(string='Issuing Authority')




#################################################################################################
#                                      CUSTOM FUNCTION                                          #
#################################################################################################

    @api.depends('identity_ids')
    @api.onchange('identity_ids')
    def compute_identity_fields(self):
        self.ensure_one()
        identity = self.identity_ids.filtered(lambda x: x.is_default == True)
        if identity:
            identity = identity[0]
            self.doc_type = identity.document_type_id.name
            self.doc_number = identity.document_number
            self.doc_issuing_date = identity.document_issuing_date
            self.doc_expiration_date = identity.document_expiration_date
            self.doc_issuing_authority = identity.document_issuing_authority


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
    is_default = fields.Boolean(string='Default?', default=False)



#################################################################################################
#                                    ONCHANGE && COMPUTE                                        #
#################################################################################################

    @api.constrains('document_issuing_date', 'document_expiration_date')
    def _check_document_issuing_date(self):
        for rec in self:
            if rec.document_issuing_date and rec.document_expiration_date:
                if rec.document_issuing_date > rec.document_expiration_date:
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


    def set_default_identity(self):
        self.ensure_one()
        search_identity = self.search([('partner_id', '=', self.partner_id.id), ('is_default', '=', True), ('id', '!=', self.id)])
        # set other identity to not default
        search_identity.write({'is_default': False})
        # set current identity to default
        self.write({'is_default': True})
        self.partner_id.compute_identity_fields()
        return True






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