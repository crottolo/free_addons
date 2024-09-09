# -*- coding: utf-8 -*-

from . import controllers
from . import models


from odoo import api, SUPERUSER_ID
def init_ateco_categories(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['atecoit.category'].download_ateco_category()
