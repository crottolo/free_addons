from odoo import models, fields, api, _
from random import randint
import requests
import csv
from io import StringIO
import logging

_logger = logging.getLogger(__name__)

def _get_default_color(self):
    return randint(1, 11)


class AtecoitCategory(models.Model):
    _name = 'atecoit.category'
    _description = 'Ateco IT Category'
    _order = 'sequence'
    #_inherit = ['mail.thread', 'mail.activity.mixin']

    color = fields.Integer(string='Color', default=_get_default_color)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id.id)
    name = fields.Char(required=True)
    code = fields.Char(string="ATECO Code", required=True)
    sequence = fields.Integer(string="Sequence")
    update = fields.Text()
    parent_id = fields.Many2one(
        "atecoit.category", string="Parent Category", index=True)
    child_ids = fields.One2many(
        "atecoit.category", "parent_id", string="Child Categories"
    )
    partner_ids = fields.Many2many(
        "res.partner",
        "ateco_category_partner_rel",
        "ateco_id",
        "partner_id",
        string="Partners",
    )

    def name_get(self):
        res = []

        for record in self:
            name = record.name
            if record.code:
                name = record.code + " - " + name
            res.append((record.id, name))
        return res

    @api.model
    def download_ateco_category(self):
        url = "https://raw.githubusercontent.com/italia/daf-ontologie-vocabolari-controllati/master/VocabolariControllati/classifications-for-organizations/ateco-2007/ateco-2007.csv"
        
        try:
            _logger.info("Starting download of ATECO data from %s", url)
            response = requests.get(url)
            if response.status_code == 200:
                csv_data = response.content.decode('utf-8-sig')
                _logger.info("Download completed successfully. Starting data processing.")
                result = self._process_csv_data(csv_data)
                return {
                    'success': True,
                    'message': "Update completed.",
                    'created': result['created'],
                    'updated': result['updated'],
                    'deleted': result['deleted']
                }
            else:
                _logger.error("Error downloading ATECO data. Status code: %s", response.status_code)
                return {
                    'success': False,
                    'message': f"Error downloading ATECO data. Status code: {response.status_code}",
                }
        except Exception as e:
            _logger.error("Error during ATECO data download: %s", str(e))
            return {
                'success': False,
                'message': f"Error during ATECO data download: {str(e)}",
            }

    def _process_csv_data(self, csv_data):
        reader = csv.reader(StringIO(csv_data), delimiter=',')
        next(reader)  # Skip header

        existing_categories = {cat.code: cat for cat in self.search([])}
        processed_codes = set()
        created_count = 0
        updated_count = 0

        _logger.info("Starting CSV row processing")
        for index, row in enumerate(reader, start=1):
            code, name, update = row[0], row[1], row[2]
            result = self._update_or_create_category(code, name, update, index)
            if result == 'created':
                created_count += 1
            elif result == 'updated':
                updated_count += 1
            processed_codes.add(code)

        # Handle deleted records
        deleted_codes = set(existing_categories.keys()) - processed_codes
        deleted_count = 0
        if deleted_codes:
            deleted_records = self.browse([existing_categories[code].id for code in deleted_codes])
            deleted_count = len(deleted_records)
            deleted_records.unlink()
            _logger.info("Deleted %s records no longer present in the CSV", deleted_count)

        _logger.info("CSV processing completed. Created: %s, Updated: %s, Deleted: %s",
                     created_count, updated_count, deleted_count)
        
        return {
            'created': created_count,
            'updated': updated_count,
            'deleted': deleted_count,
        }

    def _update_or_create_category(self, code, name, update, sequence):
        existing_category = self.search([('code', '=', code)], limit=1)

        # Name handling: capitalize first letter and handle empty or false name
        processed_name = name.capitalize() if name else _("Unnamed Category")

        if existing_category:
            if existing_category.name != processed_name or existing_category.update != update or existing_category.sequence != sequence:
                existing_category.write({
                    'name': processed_name,
                    'update': update,
                    'sequence': sequence
                })
                _logger.debug("Updated ATECO category: %s - %s", code, processed_name)
                return 'updated'
        else:
            self.create({
                'code': code,
                'name': processed_name,
                'update': update,
                'sequence': sequence
            })
            _logger.debug("Created new ATECO category: %s - %s", code, processed_name)
            return 'created'
        return 'unchanged'

    @api.model
    def cron_update_ateco_categories(self):
        _logger.info("Starting scheduled update of ATECO categories")
        result = self.download_ateco_category()
        if result:
            _logger.info("Scheduled update of ATECO categories completed successfully")
        else:
            _logger.warning("Scheduled update of ATECO categories failed")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' in vals:
                vals['name'] = vals['name'].capitalize(
                ) if vals['name'] else _("Unnamed Category")
        return super(AtecoitCategory, self).create(vals_list)

    def write(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].capitalize() if vals['name'] else _("Unnamed Category")
        return super(AtecoitCategory, self).write(vals)