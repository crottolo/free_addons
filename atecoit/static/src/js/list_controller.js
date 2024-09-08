/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { _t, _lt } from '@web/core/l10n/translation';


patch(ListController.prototype, "atecoit_category", {
    setup() {
        this._super(...arguments);
        this.action = useService("action");
        this.orm = useService("orm");
        this.notification = useService("notification");
    },

    async downloadAtecoCategory() {
        try {
            const result = await this.orm.call(
                'atecoit.category', 
                'download_ateco_category',
                []
            );
            console.log("Call result:", result);
            if (result.success) {
                const message = _lt(`${result.message} Created: ${result.created}, Updated: ${result.updated}, Deleted: ${result.deleted}`);
                this.notification.add(message, {
                    type: 'success',
                });
                // Update the view after action completion
                await this.model.load();
                this.render();
            } else {
                this.notification.add(result.message, {
                    type: 'warning',
                });
            }
        } catch (error) {
            console.error("Error during the call:", error);
            this.notification.add(_lt("An error occurred while updating ATECO categories."), {
                type: 'danger',
            });
        }
    }
});