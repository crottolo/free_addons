from odoo import api, fields, models, _
from odoo.exceptions import UserError

import openai
import pytz
from bs4 import BeautifulSoup as BS
import datetime
import json
import html
import re
import markdown
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
        msgs= self.env['mail.message'].search([('id', 'in', get_last_message)], order='id desc', limit=20)
        # messages = msgs.mapped('body')
        bot = self.env.ref("base.partner_root")
        messages_old = []
        for m in msgs:
            norm = BS(m.body, 'html.parser').get_text()
            author = m.author_id.name
            if m.author_id.id == bot.id:
                messages_old.append({"role": "assistant", "content": norm})
            else:
                messages_old.append({"role": "user", "content": norm})
        
        if body =="#enable":
            self.env.user.odoobot_state = 'chatgpt'
            return "ChatGpt enabled"
        if body =="#disable":
            self.env.user.odoobot_state = 'disabled'
            return "ChatGpt disabled"
        if body =="#clear":
            self.env['mail.message'].search([('id', 'in', get_last_message[1:])], order='id desc').unlink()
            
            return #"cleared last 10 messages"

        exclusion = {'o_mail_notification', 'o_mail_redirect', 'o_channel_redirect'}
        msg_sys = [ele for ele in exclusion if(ele in body)]
        ### parse message ###
        revert = list(reversed(messages_old))

        #create message
        contatti = self.env['res.partner'].search([])
        comp = len(contatti.filtered(lambda x: x.is_company == True))
        ct = len(contatti.filtered(lambda x: x.is_company == False))
        if odoobot_state == 'chatgpt' and not msg_sys:
            lang = self.env.user.lang 
            tz = self.env.user.tz
            local = pytz.timezone(tz)
            now = datetime.datetime.strftime(pytz.utc.localize(datetime.datetime.utcnow()).astimezone(local), "%Y-%m-%d %H:%M:%S")
            lang = self.env['res.lang'].search([('code', '=', lang)]).name
            app = self.env['ir.module.module'].search([('state', '=', 'installed'), ('application', '=',True)]).mapped('name')

            message_new = [
                {'role': 'system', 'content': 'You are a veterinary assistant and work for this company with name '+self.env.company.name}, 
                {'role': 'system', 'content': 'Answer same a veterinary assistant'}, 
                {'role': 'system', 'content': 'qualified in veterinary medicine and surgery'}, 
                # {'role': 'system', 'content': 'Email:'+self.env.user.email},
                {'role': 'system', 'content': 'the date and time now is '+ now + ' with timezone '+ tz}, 
                {'role': 'system', 'content': 'Active Contacts:'+str(ct)}, 
                {'role': 'system', 'content': 'Active Companies'+str(comp)}, 
                {'role': 'system', 'content': 'Apps installed:'+str(app)}, 
                {'role': 'system', 'content': 'answer in:'+lang}, 
                {"role": "system", "content": 'At the beginning of the conversation, include the person\'s name '+ self.env.user.name }, 
                {"role": "system", "content": 'Answer Format: html'}, #and replace ```json {\} ``` with <pre> and </pre>'},
                {"role": "system", "content": 'consulto: https://ciaovet.com/consulto'},
                {"role": "system", "content": 'prenotazione: https://ciaovet.com/consulto'},
                {"role": "system", "content": 'appuntamento: https://ciaovet.com/consulto'},
                # {"role": "system", "content": 'Replace ```python {\} ``` with <pre> and </pre>'},

                

                
                {"role": "user", "content": 'Mi chiamo '+ self.env.user.name},
                {"role": "assistant", "content": 'Ciao'+self.env.user.name+' Roberto! Come posso esserti utile?'},
                {"role": "user", "content": 'ho un problema con il mio cane'},
                {"role": "assistant", "content": 'puoi descrivermi il problema?'},
                {"role": "user", "content": 'ha dei problemi'},
                {"role": "assistant", "content": 'puoi fissare un consulto direttamente qui: https://ciaovet.com/consulto'},

    # {"role": "system", "content": "You are OdooBot"},
    # {"role": "system", "content": "Roberto has 14 practices with our company"},
    # {"role": "system", "content": "3 practices are in progress"},
    # {"role": "system", "content": "2 practices closed and the revenue is 1.578€"},
    # {"role": "system", "content": "5 practices are in the first phase"},
    # {"role": "system", "content": "4 practices are draft"},
    # {"role": "system", "content": "provide an intent for each question from this list: saluto, stato_pratica, info_generiche, altro"},
    # {"role": "system", "content": "insert a response in json format: {'risposta': 'testo della risposta', 'intento': 'intenzione'}"},
            ]

            for item in revert:
                message_new.append(item)
            
            # print(json.dumps(message_new, indent=4))
            message_new.append({"role": "user", "content": body})            
            self.with_delay().risposta(record, message_new)
            
            return 
        else:
            return res

    


    def risposta(self, record, messages):
        openai.api_key = self.env['ir.config_parameter'].sudo().get_param('chatgpt_api_key')
        response = openai.ChatCompletion.create(
            model= "gpt-3.5-turbo",
            messages=messages,
            temperature=0.3,
        )
        gpt = response.choices[0].message.content
        parts = re.split(r'```.*\n', gpt) # separazione del codice markdown
        for i, part in enumerate(parts):
            if i % 2 == 0:
                parts[i] = html.escape(parts[i])
                parts[i] = markdown.markdown(parts[i])  # conversione in HTML del testo (ad eccezione del codice markdown)
            else:
                parts[i] = '<pre><code>' + parts[i] + '</code></pre>'
        gpt = ''.join(parts)
        gpt = html.unescape(gpt)
        odoobot_id = self.env.ref("base.partner_root")
        mod_response = self.env['mail.channel'].with_context(chatgpt=True).browse(record.id).message_post(
            body=gpt,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
            author_id=odoobot_id.id
        )
        return mod_response