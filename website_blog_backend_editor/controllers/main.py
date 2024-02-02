# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import json
from odoo import http, models
from odoo.http import request
# import markdown
import datetime
import re
_logger = logging.getLogger(__name__)


class BlogPost(http.Controller):
    @http.route('/blog_post/test_request', type='json', auth='public', methods=['POST'])
    def test_request(self, **post):
        """create test request to data"""
        # data = request.httprequest.data
        
        # print(data)
        
        data_str = request.httprequest.data
        decoded_str = data_str.decode('utf-8')
        
        # # Estrai il contenuto tra i delimitatori di blocchi di codice
        # match = re.search(r'```json\n(.*?)\n```', decoded_str, re.DOTALL)
        # if match:
        #     json_content_str = match.group(1)
        #     json_content = json.loads(json_content_str)
        #     print(json_content)
        # else:
        #     print("Content not found")
        # data_j = data.get('content')
        # cleaned_content = content.replace("```json", "").replace("```", "").strip()
        # print(cleaned_content)
        #  convert string to json
        
        # j = json.loads(cleaned_content)
        
        # title = j.get('title')
        # meta_description = j.get('meta_description')
        # meta_keywords = j.get('meta_keywords')
        # content = j.get('content')
        # html = markdown.markdown(content)
        
        # html = markdown.markdown(content)
        # search = request.env['blog.post'].sudo().with_user(2).search([('id_request', '=', data['id'])], limit=1)
        # search.update({'content': html, 'website_meta_title' : title, 'website_meta_description' : meta_description, 'website_meta_keywords' : meta_keywords})
        # body = f'<p>Updated content for request {data["id"]}</p> time: {datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")}'
        # search.message_post(body=body, subject='Updated content')
        # return {'status': 'ok'}