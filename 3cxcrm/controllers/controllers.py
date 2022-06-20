from odoo import http, _
import logging
import json
from odoo.http import HttpRequest, request, JsonRequest, Response
from odoo.tools import date_utils
import datetime  
from werkzeug.exceptions import BadRequest


_logger = logging.getLogger(__name__)



def alternative_json_response(self, result=None, error=None):
  if error is not None:
      response = error
  if result is not None:
      response = result
  mime = 'application/json'
  body = json.dumps(response, default=date_utils.json_default)
  return Response(
    body, status=error and error.pop('http_status', 200) or 200,
    headers=[('Content-Type', mime), ('Content-Length', len(body))]
  )

class Odoo3cxCrm(http.Controller):
    @http.route('/api/3cx/crm', auth='public', csrf=False, type='json', methods=['POST'])
    def odoo_3cx_query (self, ** kw):
        
        token = request.env.ref('3cxcrm.token_3cx_crm').sudo().value
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
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
                    print('res_partner', res_partner)
                    b = res_partner
                    link = f"web#id={b.id}&model=res.partner&view_type=form&action={partner_action_id.id}"
                    company = ""
                    if b.company_type == "company":
                        company = b.name
                    else:
                        company = ""
                    data={
                        'partner_id': f"{b.id}",
                        'type' : b.type,
                        'firstname' :  b.firstname if b.firstname else '',
                        'lastname': b.lastname if b.lastname  else '',
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
        

    ####odoo crm.lead search lead
    #query = request.env['crm.lead'].with_user(1).search([('phone_mobile_search','ilike', '39358')])



        # dato = data.get('messages','')
        # print(dato)
        # for msg in dato:
        #     date = datetime.datetime.fromtimestamp( msg.get('date','') ) 
        #     request.env['wa.message'].sudo().create({
        #         'id_mp': msg.get('id',''),
        #         'messenger': msg.get('messenger',''),
        #         'usernumber': msg.get('usernumber',''),
        #         'date': date,
        #         'attachment': msg.get('attachment',''),
        #         'attachment_type': msg.get('attachment_type',''),
        #         'text': msg.get('text',''),
        #         'welcome': msg.get('welcome',''),
        #         'userstatus': msg.get('userstatus',''),
        #         'chatid': msg.get('chat_id',''),
        #         'is_retry': msg.get('is_retry',''),
        #         'ticket_id': msg.get('ticket_id',''),
        #         'ticket_status': msg.get('ticket_status',''),
        #         'agent_id': msg.get('agent_id',''),
        #         'inbound': True,
        #         'outbound': False
                
                
        #     })
        # sender =  msg.get('usernumber','')
        # exist_channel = request.env['mail.channel'].sudo().search([('sender', '=', sender)])
        # print('exist_channel',exist_channel)
        # if exist_channel:
        #     self.send_to_channel( msg.get('text',''), exist_channel.id)
        # else:
        #     aaa = self.search_sender(sender)
            
            
        #     new_channel = self.channel_create( aaa+" "+sender, sender, privacy='public')
            
        #     self.send_to_channel( msg.get('text',''), new_channel.get('id',''))
        #print("response", response)


   
