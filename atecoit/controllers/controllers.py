from odoo.http import request, Response
from odoo import http, _, tools
import requests
import json
import datetime
import logging
_logger = logging.getLogger(__name__)

# class NewOdoo(http.Controller):
#     _webhook_url = '/url'
    
    
#     @http.route(_webhook_url, type='http', methods=['GET'], auth='public', csrf=False)
#     def new_odoo_webhook_get(self, **kw):
#         _logger.info("url webhook verification")
#         return True
    
#     @http.route(_webhook_url, type='json', methods=['GET', 'POST'], auth='public', csrf=False)
#     def new_odoo_webhook_get_post(self, **kw):
#         _logger.info("url webhook verification")
#         return True
        
        
   