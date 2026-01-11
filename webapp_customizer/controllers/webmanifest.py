# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import io

from odoo import http
from odoo.http import request

from odoo.addons.web.controllers import webmanifest

try:
    from PIL import Image
except ImportError:
    Image = None


class WebManifest(webmanifest.WebManifest):
    """Inherit Odoo's WebManifest controller to add PWA icon customization"""

    def _get_webmanifest(self):
        """Override to add custom PWA icon if configured"""
        manifest = super()._get_webmanifest()

        # Check if PWA icon is configured (stored as attachment)
        pwa_attachment = (
            request.env["ir.attachment"]
            .sudo()
            .search(
                [
                    ("name", "=", "pwa_icon"),
                    ("res_model", "=", "ir.config_parameter"),
                    ("res_id", "=", 0),
                ],
                limit=1,
            )
        )

        if pwa_attachment:
            manifest["icons"] = [
                {
                    "src": "/web/pwa_icon/192",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any maskable",
                },
                {
                    "src": "/web/pwa_icon/512",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any maskable",
                },
            ]

        return manifest

    @http.route(["/web/pwa_icon/<int:size>"], type="http", auth="public", readonly=True)
    def pwa_icon(self, size):
        """Serve PWA icon in requested size"""
        # Get PWA icon from attachment
        pwa_attachment = (
            request.env["ir.attachment"]
            .sudo()
            .search(
                [
                    ("name", "=", "pwa_icon"),
                    ("res_model", "=", "ir.config_parameter"),
                    ("res_id", "=", 0),
                ],
                limit=1,
            )
        )

        if not pwa_attachment or not Image:
            return request.not_found()

        try:
            # Decode base64 image
            image_data = base64.b64decode(pwa_attachment.datas)
            image = Image.open(io.BytesIO(image_data))

            # Resize to requested size
            image = image.resize((size, size), Image.Resampling.LANCZOS)

            # Convert to PNG
            output = io.BytesIO()
            image.save(output, format="PNG")
            output.seek(0)

            return request.make_response(
                output.getvalue(),
                headers=[
                    ("Content-Type", "image/png"),
                    ("Cache-Control", "public, max-age=3600"),
                ],
            )
        except Exception:
            return request.not_found()


class FaviconCustomizer(http.Controller):
    """Company-specific favicon controller (separate from PWA)"""

    @http.route("/favicon.ico", type="http", auth="public", readonly=True)
    def favicon(self):
        """Serve company-specific favicon"""
        try:
            company = request.env.company
        except Exception:
            company = None

        # If company has favicon, serve it
        if company and company.favicon:
            return request.redirect(f"/web/image/res.company/{company.id}/favicon")

        # Fallback to default favicon
        return request.redirect("/web/static/img/favicon.ico")
