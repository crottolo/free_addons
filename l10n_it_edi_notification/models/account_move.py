import logging
import re

from markupsafe import Markup

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

# States to monitor for SDI issues
SDI_PROBLEM_STATES = (
    "requires_user_signature",
    "rejected",
    "rejected_by_pa_partner",
)


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_it_edi_notified = fields.Boolean(
        string="SDI Error Notified",
        default=False,
        copy=False,
        help="True if notification was already sent for this SDI error",
    )

    # -------------------------------------------------------------------------
    # CRON: Daily SDI Report
    # -------------------------------------------------------------------------

    @api.model
    def _cron_l10n_it_edi_daily_report(self):
        """Daily cron to send SDI issues summary.

        Only sends notification if there are problems.
        """
        # country_id is related field, filter in Python to avoid search issues
        all_companies = self.env["res.company"].search([])
        companies = all_companies.filtered(lambda c: c.country_id.code == "IT")

        for company in companies:
            problems = self._l10n_it_edi_get_all_problems(company)

            # Skip if no problems
            if not any(problems.values()):
                _logger.info(
                    "SDI Daily Report: No issues found for company %s",
                    company.name,
                )
                continue

            # Generate report
            self._l10n_it_edi_send_daily_report(company, problems)

    def _l10n_it_edi_get_all_problems(self, company):
        """Get all problematic invoices grouped by category."""
        return {
            "requires_signature": self._l10n_it_edi_get_requires_signature(company),
            "rejected": self._l10n_it_edi_get_rejected(company),
            "rejected_by_pa": self._l10n_it_edi_get_rejected_by_pa(company),
            "not_sent_self_invoices": self._l10n_it_edi_get_not_sent_self_invoices(
                company,
            ),
        }

    # -------------------------------------------------------------------------
    # Problem Detection Methods
    # -------------------------------------------------------------------------

    def _l10n_it_edi_get_requires_signature(self, company):
        """Get invoices that require user signature."""
        return self.search(
            [
                ("company_id", "=", company.id),
                ("state", "=", "posted"),
                ("l10n_it_edi_state", "=", "requires_user_signature"),
            ],
        )

    def _l10n_it_edi_get_rejected(self, company):
        """Get invoices rejected by SDI."""
        return self.search(
            [
                ("company_id", "=", company.id),
                ("state", "=", "posted"),
                ("l10n_it_edi_state", "=", "rejected"),
            ],
        )

    def _l10n_it_edi_get_rejected_by_pa(self, company):
        """Get invoices rejected by PA partner."""
        return self.search(
            [
                ("company_id", "=", company.id),
                ("state", "=", "posted"),
                ("l10n_it_edi_state", "=", "rejected_by_pa_partner"),
            ],
        )

    def _l10n_it_edi_get_not_sent_self_invoices(self, company):
        """Get self-invoices (autofatture) that are posted but not sent.

        Uses same logic as 'Send Tax Integration' button visibility:
        - state == 'posted'
        - l10n_it_edi_is_self_invoice == True (computed, filtered in Python)
        - is_move_sent == False
        - country_code == 'IT'
        """
        # Search base criteria (stored fields only)
        candidates = self.search(
            [
                ("company_id", "=", company.id),
                ("state", "=", "posted"),
                ("is_move_sent", "=", False),
                ("country_code", "=", "IT"),
            ],
        )
        # Filter by computed field in Python
        return candidates.filtered(lambda m: m.l10n_it_edi_is_self_invoice)

    # -------------------------------------------------------------------------
    # Report Generation & Sending
    # -------------------------------------------------------------------------

    def _l10n_it_edi_send_daily_report(self, company, problems):
        """Send the daily report to channel and fallback user."""
        # Use Italian language for report generation (Italian localization module)
        self_it = self.with_context(lang="it_IT")
        html_content = self_it._l10n_it_edi_generate_report_html(company, problems)

        # Get configuration
        params = self.env["ir.config_parameter"].sudo()
        channel_id = params.get_param(
            "l10n_it_edi_notification.notification_channel_id",
        )
        fallback_user_id = params.get_param("l10n_it_edi_notification.default_user_id")
        create_activity = (
            params.get_param("l10n_it_edi_notification.create_activity", "False")
            == "True"
        )

        # Post to channel
        channel = None
        if channel_id:
            channel = self.env["discuss.channel"].browse(int(channel_id)).exists()
        if not channel:
            # Fallback to default channel created by module
            channel = self.env.ref(
                "l10n_it_edi_notification.channel_sdi_notifications",
                raise_if_not_found=False,
            )

        if channel:
            channel.message_post(
                body=html_content,
                message_type="notification",
                subtype_xmlid="mail.mt_comment",
            )
            _logger.info("SDI Daily Report posted to channel %s", channel.name)

        # Send email to fallback user
        if fallback_user_id:
            fallback_user = self.env["res.users"].browse(int(fallback_user_id)).exists()
            if fallback_user and fallback_user.email:
                self._l10n_it_edi_send_report_email(
                    company,
                    fallback_user,
                    html_content,
                    problems,
                )

        # Create activities if enabled
        if create_activity:
            self._l10n_it_edi_create_activities(problems)

    def _l10n_it_edi_generate_report_html(self, company, problems):
        """Generate HTML report content using QWeb template."""
        from odoo.tools.misc import format_date, formatLang

        today = fields.Date.context_today(self)

        # Helper functions for template
        def format_monetary(amount, currency):
            return formatLang(self.env, amount, currency_obj=currency)

        def fmt_date(date):
            return format_date(self.env, date) if date else "-"

        # Italian labels for report (Italian localization module)
        # Using Italian directly as this is an IT-specific EDI notification module
        labels = {
            "title": "Riepilogo Giornaliero SDI",
            "company_label": "Azienda:",
            "requires_signature_title": "Richiede Firma",
            "requires_signature_desc": "Fatture che richiedono la firma utente prima dell'invio.",
            "rejected_title": "Rifiutate dallo SDI",
            "rejected_desc": "Fatture rifiutate dallo SDI - verificare errori nel chatter.",
            "rejected_pa_title": "Rifiutate dal Partner PA",
            "rejected_pa_desc": "Fatture rifiutate dal partner PA - contattare il cliente.",
            "self_invoices_title": "Autofatture Non Inviate",
            "self_invoices_desc": "Autofatture confermate (reverse charge) non ancora inviate allo SDI.",
        }

        return self.env["ir.qweb"]._render(
            "l10n_it_edi_notification.sdi_daily_report_template",
            {
                "company": company,
                "date": format_date(self.env, today),
                "problems": problems,
                "format_monetary": format_monetary,
                "format_date": fmt_date,
                "labels": labels,
            },
        )

    # -------------------------------------------------------------------------
    # Helper Methods for QWeb Template
    # -------------------------------------------------------------------------

    def _get_sdi_report_link(self):
        """Get direct link to invoice for SDI report."""
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")

        if self.move_type in ["out_invoice", "out_refund"]:
            action = "account.action_move_out_invoice_type"
        else:
            action = "account.action_move_in_invoice_type"

        return f"{base_url}/odoo/action-{action}/{self.id}"

    def _get_sdi_error_text(self):
        """Extract plain text error reason from l10n_it_edi_header.

        Returns full text without truncation.
        """
        self.ensure_one()
        header = self.l10n_it_edi_header or ""
        if not header:
            return ""

        # Strip HTML tags
        text = re.sub(r"<[^>]+>", " ", str(header))
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        # Decode HTML entities
        text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")

        return text

    def _l10n_it_edi_send_report_email(self, company, user, html_content, problems):
        """Send email report to fallback user."""
        # Count total problems
        total = sum(len(v) for v in problems.values())

        # Use mail.mail for direct sending
        mail_values = {
            "subject": _(
                "[%(company)s] SDI Summary - %(count)s issues",
                company=company.name,
                count=total,
            ),
            "body_html": html_content,
            "email_from": company.email_formatted or self.env.user.email_formatted,
            "email_to": user.email,
            "auto_delete": True,
        }

        mail = self.env["mail.mail"].sudo().create(mail_values)
        mail.send(raise_exception=False)
        _logger.info("SDI Daily Report email sent to %s", user.email)

    def _l10n_it_edi_create_activities(self, problems):
        """Create activities for problematic invoices."""
        activity_type = self.env.ref(
            "l10n_it_edi_notification.mail_activity_sdi_error",
            raise_if_not_found=False,
        )

        if not activity_type:
            return

        # Create activities for all problem categories
        all_moves = (
            problems["requires_signature"]
            | problems["rejected"]
            | problems["rejected_by_pa"]
            | problems["not_sent_self_invoices"]
        )

        for move in all_moves:
            # Skip if already notified
            if move.l10n_it_edi_notified:
                continue

            # Get user to assign activity to
            user = move._l10n_it_edi_get_notification_user()
            if not user:
                continue

            move.activity_schedule(
                activity_type_id=activity_type.id,
                summary=_("SDI Error: %s", move.name),
                note=move._l10n_it_edi_get_notification_message(),
                user_id=user.id,
            )

            # Mark as notified to avoid duplicate activities
            move.l10n_it_edi_notified = True

    def _l10n_it_edi_get_notification_user(self):
        """Get the user to notify for SDI errors.

        Priority: invoice_user_id > user_id > create_uid > configured default
        """
        self.ensure_one()

        # Priority 1: Invoice responsible
        if self.invoice_user_id:
            return self.invoice_user_id

        # Priority 2: Salesperson
        if self.user_id:
            return self.user_id

        # Priority 3: Creator
        if self.create_uid:
            return self.create_uid

        # Priority 4: Configured default user
        default_user_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_it_edi_notification.default_user_id")
        )
        if default_user_id:
            return self.env["res.users"].browse(int(default_user_id))

        return False

    def _l10n_it_edi_get_notification_message(self):
        """Build notification message based on SDI state or self-invoice status."""
        self.ensure_one()

        # Check if it's an unsent self-invoice first
        if self.l10n_it_edi_is_self_invoice and not self.is_move_sent:
            return Markup(
                _(
                    "Self-invoice <b>%(name)s</b> is confirmed but <b>NOT SENT</b> to SDI.<br/>"
                    "Click 'Send Tax Integration' to send it.",
                    name=self.name,
                ),
            )

        state_messages = {
            "requires_user_signature": Markup(
                _(
                    "Invoice <b>%(name)s</b> <b>REQUIRES SIGNATURE</b> before sending.<br/>"
                    "Access the invoice and complete the signature.",
                    name=self.name,
                ),
            ),
            "rejected": Markup(
                _(
                    "Invoice <b>%(name)s</b> was <b>REJECTED</b> by SDI.<br/>"
                    "Check the errors in the invoice chatter and fix them.",
                    name=self.name,
                ),
            ),
            "rejected_by_pa_partner": Markup(
                _(
                    "Invoice <b>%(name)s</b> was <b>REJECTED BY PA PARTNER</b>.<br/>"
                    "Contact the customer to verify the rejection reason.",
                    name=self.name,
                ),
            ),
        }

        return state_messages.get(self.l10n_it_edi_state, _("SDI Error"))

    @api.model
    def _l10n_it_edi_reset_notification_flag(self):
        """Reset notification flag when invoice is reset to draft.

        Called when invoice state changes allow re-sending after fix.
        """
        self.write({"l10n_it_edi_notified": False})
