# AGENTS.md - Free Addons ODOO (OCA/Community)

**Created**: 2026-06-06 | **Scale**: 242 files, ~5K LOC | **Modules**: 14

## OVERVIEW

OCA and community addons collection. Mostly third-party modules: FontAwesome, theme modifications, identity docs, bank codes, mail extensions, website tools, and misc integrations. Read-only — do not modify upstream OCA code.

## STRUCTURE

```
free_addons_odoo/
├── base_fontawesome/            # Up-to-date FontAwesome icons
├── enterprise_theme_mod/       # Enterprise theme customization
├── partner_identity_id/        # Identity document management
├── signup_address_fields_fl1/  # Signup address fields
├── atecoit/                    # Ateco code management
├── website_blog_backend_editor/ # Blog post backend editor
├── 3cxcrm/                     # 3CX CRM auto-identification
├── license_enterprise_reminder/ # Enterprise license reminder (30→60 days)
├── l10n_it_edi_notification/   # Italian e-invoice daily summary
├── mail_multicompany/          # Multi-company mail routing
├── bank_abicab/                # Italian bank ABI/CAB codes
├── webapp_customizer/          # Company favicons and PWA icons
├── server_info_monitor/        # REST API for Odoo instance monitoring
└── chatgpt4_bot/               # ChatGPT integration in Odoo chat
```

## NOTES

- These are **OCA/community modules** — do not modify unless forked.
- No custom code here; all modules are from external sources.
- Use as dependency modules only.