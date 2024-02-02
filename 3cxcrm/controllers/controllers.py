from odoo import http, _
import logging
import json
from odoo.http import  request, Response
from odoo.tools import date_utils
import datetime  
from werkzeug.exceptions import BadRequest


_logger = logging.getLogger(__name__)




class Odoo3cxCrm(http.Controller):
    @http.route('/api/3cx/crm', auth='public', csrf=False, type='json', methods=['POST'])
    def odoo_3cx_query (self, ** kw):
        
        token = request.env.ref('3cxcrm.token_3cx_crm').sudo().value
        data = json.loads(request.httprequest.data) 
        apikey = request.httprequest.headers.get('apikey')


        number = str(data.get('number'))
        if apikey:
            if not apikey == token:
                return BadRequest('Wrong APIKEY')
            else:
                
                res_partner = request.env['res.partner'].with_user(1).search([('phone_mobile_search','ilike', number)],limit=1)
                crm_lead = request.env['crm.lead'].with_user(1).search([('phone_mobile_search','ilike', number)],limit=1)
                
                partner_action_id = request.env.ref('contacts.action_contacts')
                crm_action_id = request.env.ref('crm.crm_lead_all_leads')
                
                if res_partner:
                    b = res_partner
                    link = f"web#id={b.id}&model=res.partner&view_type=form&action={partner_action_id.id}"
                    company = ""
                    if b.company_type == "company":
                        company = b.name
                    else:
                        company = ""
                        
                    partner_fields = request.env['res.partner'].fields_get()
                    if 'firstname' in partner_fields:
                        firstname = b.firstname if b.firstname else b.name
                        lastname = b.lastname if b.lastname else ''
                        # Qui puoi gestire il campo 'firstname' come necessario
                    else:
                        firstname = b.name
                        lastname = ''
                    data={
                        'partner_id': f"{b.id}",
                        'type' : b.type,
                        'firstname' :  firstname,
                        'lastname': lastname,
                        'mobile': b.mobile if b.mobile else '',
                        'phone' : b.phone if b.phone else '',
                        'email': b.email if b.email else '',
                        'web_url': f"{request.httprequest.url_root}{link}",
                        'company_type': b.company_type if b.company_type == "company" else '',
                        'name': company,
                        # 'link_end': 'link_end'
                    }
                    return data
                elif crm_lead:
                    print('crm_lead',crm_lead)
                    b = crm_lead
                    if b.type == 'lead':
                        link = f"web#id={b.id}&model=crm.lead&view_type=form&action={crm_action_id.id}"
                    elif b.type == 'opportunity':
                        link = f"web#id={b.id}&model=crm.lead&view_type=form&action={crm_action_id.id}"

                    data={
                        'partner_id': f"L{b.id}",
                        'type' : b.type,
                        'name' :  b.contact_name if b.contact_name else b.name,
                        'contact_name': b.name if b.name  else '',
                        'mobile': b.mobile if b.mobile else '',
                        'phone' : b.phone if b.phone else '',
                        'web_url': f"{request.httprequest.url_root}{link}",
                        'link_end': 'link_end'
                    }
                    return data
                else:
                    data ={"new_number": True}
                    return data

        return BadRequest('ApiKey not set')
        


   
