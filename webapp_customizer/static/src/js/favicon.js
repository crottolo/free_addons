/** @odoo-module **/

import { WebClient } from "@web/webclient/webclient";
import { patch } from "@web/core/utils/patch";
import { useComponent } from "@odoo/owl";

patch(WebClient.prototype, {
    setup() {
        super.setup();
        const component = useComponent();
        const env = component.env;

        // Update favicon immediately on setup
        if (env.services.company?.currentCompany) {
            this._updateFavicon(env);
        }
    },

    _updateFavicon(env) {
        if (!env.services.company?.currentCompany) {
            return;
        }

        const companyId = env.services.company.currentCompany.id;
        const favicon = `/web/image/res.company/${companyId}/favicon`;

        // Update all favicon-related links (simplified logic from bb_web_company_favicon)
        const icons = document.querySelectorAll("link[rel*='icon']");
        const msIcon = document.querySelector("meta[name='msapplication-TileImage']");

        for (const icon of icons) {
            if (icon instanceof HTMLLinkElement) {
                icon.href = favicon;
            }
        }

        if (msIcon) {
            msIcon.setAttribute("content", favicon);
        }
    },
});
