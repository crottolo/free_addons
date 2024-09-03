from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

try:
    from schwifty import IBAN
except ImportError:
    _logger.warning(
        'schwifty not installed, BIC/SWIFT will not be available install it with "pip install schwifty"')
    IBAN = None


class ResBank(models.Model):
    _inherit = "res.bank"

    abi = fields.Char(size=5, string="ABI")
    cab = fields.Char(size=5, string="CAB")


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    bank_abi = fields.Char(size=5, string="ABI",
                           related="bank_id.abi", store=True)
    bank_cab = fields.Char(size=5, string="CAB",
                           related="bank_id.cab", store=True)
    


#################################################################################################
#                                      CUSTOM FUNCTION                                          #
#################################################################################################


    @api.model
    def cron_associate_bank_abicab(self):
        search_empty = self.search([('acc_number', 'like', 'IT'), ('bank_abi', '=', False), ('bank_cab', '=', False)])
        
        for bank in search_empty:
            try:
                acc_number = bank.acc_number.replace(' ', '')
                iban = IBAN(acc_number)
                _logger.info('iban %s', iban.bic)
                
                abi = acc_number[5:10]
                cab = acc_number[10:15]
                bank_abicab = self.env['bank.abicab'].search([('abi', '=', abi), ('cab', '=', cab)], limit=1)
                if bank_abicab:
                    _logger.info('bank_abicab: %s', bank_abicab)
                    search_bank = self.env['res.bank'].search([('abi', '=', abi), ('cab', '=', cab)], limit=1)
                    if not search_bank:
                        state_id = self.env['res.country.state'].search([('code', '=', bank_abicab.provincia)], limit=1)
                        create_bank = self.env['res.bank'].create({
                            'abi': abi,
                            'cab': cab,
                            'name': bank_abicab.name.title() if bank_abicab.name else '',
                            'street': bank_abicab.indirizzo.title() if bank_abicab.indirizzo else '',
                            'city': bank_abicab.citta.title() if bank_abicab.citta else ''  ,
                            'zip': bank_abicab.cap,
                            'state': state_id.id,
                            'country': self.env.company.country_id.id,
                            'bic': iban.bic
                        })
                        bank.bank_id = create_bank.id
                    if search_bank:
                        bank.bank_id = search_bank.id
            except Exception as e:
                # bank.message_post(body=_("Errore durante l'elaborazione della banca %s: %s", bank.id, e))
                _logger.error("Errore durante l'elaborazione della banca %s: %s", bank.id, e)
        