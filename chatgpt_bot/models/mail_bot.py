from odoo import api, fields, models, _
from odoo.exceptions import UserError

import openai
import json
import aiohttp
import asyncio
import requests
from bs4 import BeautifulSoup as BS
import datetime

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
        messages = self.env['mail.message'].search([('id', 'in', get_last_message)], order='id desc', limit=10).mapped('body')
        
        old_conv = tuple()
        for msg in messages: 
            if msg:
                old_conv += tuple(BS(msg, 'html.parser').get_text().splitlines())
        # body = old_conv
       
        if body =="#enable":
            self.env.user.odoobot_state = 'chatgpt'
            return "ChatGpt enabled"
        if body =="#disable":
            self.env.user.odoobot_state = 'disabled'
            return "ChatGpt disabled"
        
        list = {'o_mail_notification', 'o_mail_redirect', 'o_channel_redirect'}
        msg_sys = [ele for ele in list if(ele in body)]
        
        
        contatti = self.env['res.partner'].search([])
        comp = len(contatti.filtered(lambda x: x.is_company == True))
        ct = len(contatti.filtered(lambda x: x.is_company == False))
        if odoobot_state == 'chatgpt' and not msg_sys:
            lang = self.env.user.lang 
            tz = self.env.user.tz
            lang = self.env['res.lang'].search([('code', '=', lang)]).name
            app = self.env['ir.module.module'].search([('state', '=', 'installed'), ('application', '=',True)]).mapped('name')
            pre = ( f"YOU ARE OdooBot.\n"
                    f"the system when type is ODOO 15+\n"
                    f"The company I work for is {self.env.company.name}.\n"
                    f"I'am is {self.env.user.name}.\n"
                    f"Now is {datetime.datetime.now()} and convert always to this timezone {tz}\n"
                    # f"preventivi a system: {10}.\n"
                    f"our have a {ct} contacts and {comp} are companies.\n"
                    f"The apps installed is {app}\n"
                    f"example of code must be put in the <pre></pre> tag,\n"
                    # f"the previous conversation is:[{old_conv}].\n\n\n"                    
                    )
            
            old_conv = tuple(reversed(old_conv))[:-1]
            latest = body#old_conv[-1]

            body =  f"Data training AI[<{pre}>]\n" \
                    f"Previous conversation[<{old_conv}>]\n" \
                    f"The answers must be in {lang} and HTML formatted.\n"\
                    f"The last question [{latest}]"
            
            print("body::::::::::\n", body)
            self.with_delay().risposta(record, body)
            # print("res::::::::::", res)
            return 
        else:
            return res

    
    
    
    

    
    def risposta(self, record, body): 
        
        openai.api_key = self.env['ir.config_parameter'].sudo().get_param('chatgpt_api_key')
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=body,
            temperature=0.7,
            max_tokens=3000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=[" Human:", " AI:"],
            echo = False,
            )
        gpt = (response['choices'][0]['text'])
        odoobot_id = self.env['ir.model.data']._xmlid_to_res_id("base.partner_root")
        mod_response = self.env['mail.channel'].with_context(chatgpt=True).browse(record.id).message_post(body=gpt, message_type='comment', subtype_xmlid='mail.mt_comment', author_id=odoobot_id)
        return mod_response