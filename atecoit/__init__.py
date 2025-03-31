# -*- coding: utf-8 -*-

from . import controllers
from . import models


def post_init_hook(env):
    """
    Post init hook for downloading ATECO categories.
    This hook will be executed after the module is installed.
    
    Args:
        env: Odoo environment
    """
    env['atecoit.category'].download_ateco_category()
