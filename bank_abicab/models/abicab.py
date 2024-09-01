from odoo import models, fields, api, _
import requests
import json
import re
import logging

_logger = logging.getLogger(__name__)


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


class BancheItaliane(models.Model):
    _name = "bank.abicab"
    _description = "Banche Italiane"

    abi = fields.Char(size=5, string="ABI")
    cab = fields.Char(size=5, string="CAB")
    istituto = fields.Char(string="Istituto")
    sportello = fields.Char(string="Sportello")
    indirizzo = fields.Char(string="Indirizzo")
    citta = fields.Char(string="Città")
    cap = fields.Char(size=5, string="CAP")
    provincia = fields.Char(size=2, string="Provincia")


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

    @api.model
    def download_file_github(self):
        url = "https://raw.githubusercontent.com/crottolo/ABICAB/main/abi_cab.json"
        headers = {'Accept-Encoding': 'identity'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                content = response.content.decode('utf-8-sig')
                content_cleaned = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', content)
                data = json.loads(content_cleaned)
                
                if isinstance(data, dict) and 'abicab' in data:
                    banche = data['abicab']
                    if isinstance(banche, list):
                        # Elimina tutti i record esistenti
                        self.search([]).unlink()
                        _logger.info("Tutti i record esistenti sono stati eliminati.")

                        # Crea i nuovi record
                        for banca in banche:
                            self.create({
                                'abi': banca.get('ABI'),
                                'cab': banca.get('CAB'),
                                'istituto': banca.get('Istituto'),
                                'sportello': banca.get('Sportello'),
                                'indirizzo': banca.get('Indirizzo'),
                                'citta': banca.get('Citta'),
                                'cap': banca.get('CAP'),
                                'provincia': banca.get('Provincia')
                            })

                        _logger.info("Operazione completata. Totale nuovi record creati: %s", len(banche))
                    else:
                        _logger.warning("La chiave 'abicab' non contiene una lista come previsto.")
                else:
                    _logger.warning("La struttura del JSON non è come previsto.")
                
                return True
            except json.JSONDecodeError as e:
                _logger.error("Errore durante il parsing del JSON: %s", e)
                return False
            except Exception as e:
                _logger.error("Errore generico durante l'elaborazione: %s", e)
                return False
        else:
            _logger.error("Errore nel download del file. Status code: %s", response.status_code)
            return False