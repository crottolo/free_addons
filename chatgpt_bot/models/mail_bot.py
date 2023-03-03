from odoo import api, fields, models, _
from odoo.exceptions import UserError

import openai
import pytz
from bs4 import BeautifulSoup as BS
import datetime
import json
class ChatGptBot(models.AbstractModel):
    _inherit = 'mail.bot'
    _description = 'ChatGPT OdooBot'

   


#################################################################################################
#                                       ORM FUNCTION                                            #
#################################################################################################

 
        
#################################################################################################
#                                    ONCHANGE && COMPUTE                                        #
#################################################################################################




#################################################################################################
#                                      CUSTOM FUNCTION                                          #
#################################################################################################
    
    
    

    def _get_answer(self, record, body, values, command=False):
        odoobot_state = self.env.user.odoobot_state

        res = super(ChatGptBot, self)._get_answer(record, body, values, command=False)
        
        
        get_last_message = self.env['mail.channel'].search([('id', '=', record.id)]).message_ids.ids
        messages = self.env['mail.message'].search([('id', 'in', get_last_message)], order='id desc', limit=40).mapped('body')
        
        if body =="#enable":
            self.env.user.odoobot_state = 'chatgpt'
            return "ChatGpt enabled"
        if body =="#disable":
            self.env.user.odoobot_state = 'disabled'
            return "ChatGpt disabled"
        if body =="#clear":
            self.env['mail.message'].search([('id', 'in', get_last_message[1:])], order='id desc').unlink()
            return #"cleared last 10 messages"
        

        # if body =="#pong#":
        #     search_company = self.env['res.partner'].search([('name', 'ilike', 'douglas')])
        #     if search_company:
        #         return f'{search_company.name} lavora per {search_company.parent_id.name} e svolge il ruolo di {search_company.function}'
        #     else:
        #         return "Company not found"

        list = {'o_mail_notification', 'o_mail_redirect', 'o_channel_redirect'}
        msg_sys = [ele for ele in list if(ele in body)]
        ### parse message ###
        revert = tuple(reversed(messages))
        conv = []
        for msg in revert[:-1]: 
            if msg:
                norm = BS(msg, 'html.parser').get_text().splitlines()
                conv.append({"role": "assistant", "content": norm[0]})
        #create message

        contatti = self.env['res.partner'].search([])
        comp = len(contatti.filtered(lambda x: x.is_company == True))
        ct = len(contatti.filtered(lambda x: x.is_company == False))
        if odoobot_state == 'chatgpt' and not msg_sys:
            lang = self.env.user.lang 
            tz = self.env.user.tz
            local = pytz.timezone(tz)
            now = datetime.datetime.strftime(pytz.utc.localize(datetime.datetime.utcnow()).astimezone(local), "%Y-%m-%d %H:%M:%S")
            print(now, local)
            lang = self.env['res.lang'].search([('code', '=', lang)]).name
            app = self.env['ir.module.module'].search([('state', '=', 'installed'), ('application', '=',True)]).mapped('name')

            system = [
                {'role': 'system', 'content': 'You are a odooBot assistant'},
                {'role': 'system', 'content': 'I am '+self.env.user.name},
                {'role': 'system', 'content': 'now is '+now + ' timezone '+tz},
                {'role': 'system', 'content': 'You work for this company with name '+self.env.company.name},
                {'role': 'system', 'content': 'our have a '+str(ct)+' contacts'},
                {'role': 'system', 'content': 'our have a  '+str(comp)+' companies'},
                {'role': 'system', 'content': 'The apps installed is '+str(app)},
                {'role': 'system', 'content': 'answer always in '+lang+' language'},
                # {'role': 'system', 'content': 'ping , answer always: pong inside at ## example: #pong#'},
                
            ]
            for item in system:
                conv.append(item)

            conv.append({"role": "user", "content": body})            
            print(conv)
            self.with_delay().risposta(record, conv)
            # print("res::::::::::", res)
            return 
        else:
            return res

    
    
    
    

    
    def risposta(self, record, messages): 
        
        openai.api_key = self.env['ir.config_parameter'].sudo().get_param('chatgpt_api_key')
        response = openai.ChatCompletion.create(
            model= "gpt-3.5-turbo",
            # prompt=body,
            # temperature=0.7,
            # max_tokens=3000,
            # top_p=1,
            # frequency_penalty=0,
            # presence_penalty=0,
            # stop=[" Human:", " AI:"],
            messages=messages,
            )
        
        gpt = (response.choices[0].message.content)
        odoobot_id = self.env['ir.model.data']._xmlid_to_res_id("base.partner_root")
        mod_response = self.env['mail.channel'].with_context(chatgpt=True).browse(record.id).message_post(body=gpt, message_type='comment', subtype_xmlid='mail.mt_comment', author_id=odoobot_id)
        return mod_response