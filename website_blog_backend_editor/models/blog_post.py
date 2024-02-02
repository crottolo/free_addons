from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
import requests
import json


class BlogPost(models.Model):
    _inherit = 'blog.post'

    id_request = fields.Char(string="ID Request", readonly=True)
    text_to_search = fields.Char(string="Text to search", readonly=False)

    
    
    def test_request(self):
        """create test request to 127.0.0.1
        """
        if not self.text_to_search:
            raise UserError(_("Please insert text to search"))
        url = 'http://127.0.0.1:8000/queries/'
        callback = "https://0fbb-154-56-209-218.ngrok-free.app/blog_post/test_request"
        
        data = {
            'query': self.text_to_search,
            'callback': callback
            }
        req = requests.post(url, json=data)
        j = req.json()
        self.id_request = j['_id']
        print(req.text)
