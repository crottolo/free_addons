import json
import logging

from werkzeug.exceptions import BadRequest

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class Odoo3cxCrm(http.Controller):
    @http.route(
        "/api/3cx/crm",
        auth="public",
        csrf=False,
        type="json",
        methods=["POST"],
    )
    def odoo_3cx_query(self, **kw):
        token = request.env.ref("3cxcrm.token_3cx_crm").sudo().value
        data = json.loads(request.httprequest.data)
        apikey = request.httprequest.headers.get("apikey")

        number = str(data.get("number"))
        if apikey:
            if apikey != token:
                return BadRequest("Wrong APIKEY")

            res_partners = (
                request.env["res.partner"]
                .with_user(1)
                .search([("phone_mobile_search", "ilike", number)], limit=10)
            )
            crm_leads = (
                request.env["crm.lead"]
                .with_user(1)
                .search([("phone_mobile_search", "ilike", number)], limit=10)
            )

            partner_action_id = request.env.ref("contacts.action_contacts")
            crm_action_id = request.env.ref("crm.crm_lead_all_leads")

            if res_partners:
                b = res_partners[0]
                count = len(res_partners)
                firstname, lastname, company = self._get_partner_name_parts(b)
                if count > 1:
                    suffix = f" !! ({count})"
                    if lastname:
                        lastname += suffix
                    elif firstname:
                        firstname += suffix
                    else:
                        company += suffix
                url_root = request.httprequest.url_root.rstrip("/")
                data = {
                    "partner_id": f"{b.id}",
                    "type": b.type,
                    "firstname": firstname,
                    "lastname": lastname,
                    "mobile": b.mobile if b.mobile else "",
                    "phone": b.phone if b.phone else "",
                    "email": b.email if b.email else "",
                    "web_url": f"{url_root}/odoo/contacts/{b.id}",
                    "company_type": b.company_type
                    if b.company_type == "company"
                    else "",
                    "name": company,
                }
                return data
            if crm_leads:
                _logger.info("crm_lead %s", crm_leads[0])
                b = crm_leads[0]
                count = len(crm_leads)
                name = b.contact_name if b.contact_name else b.name
                if count > 1:
                    name = f"{name} !! ({count})"
                url_root = request.httprequest.url_root.rstrip("/")
                link = f"web#id={b.id}&model=crm.lead&view_type=form&action={crm_action_id.id}"
                data = {
                    "partner_id": f"L{b.id}",
                    "type": b.type,
                    "name": name,
                    "contact_name": b.name if b.name else "",
                    "mobile": b.mobile if b.mobile else "",
                    "phone": b.phone if b.phone else "",
                    "web_url": f"{url_root}/{link}",
                    "link_end": "link_end",
                }
                return data
            data = {"new_number": True}
            return data

        return BadRequest("ApiKey not set")

    @staticmethod
    def _get_partner_name_parts(partner):
        """Extract firstname, lastname and company from partner.

        Works with or without partner_firstname module installed.
        For individuals (is_company=False): splits name into first/last.
        For companies: returns empty first/last and name as company.
        """
        has_firstname_module = "firstname" in partner._fields
        company = partner.name if partner.is_company else ""

        if partner.is_company:
            return "", "", company

        if has_firstname_module:
            firstname = partner.firstname or ""
            lastname = partner.lastname or ""
        else:
            name_parts = (partner.name or "").split(" ", 1)
            firstname = name_parts[0] if name_parts else ""
            lastname = name_parts[1] if len(name_parts) > 1 else ""

        return firstname, lastname, company
