/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

console.log("list_controller.js");

patch(ListController.prototype, "bank_abicab", {
    setup() {
        this._super(...arguments);
        this.action = useService("action");
        this.orm = useService("orm");
    },

    async bankButtonDownload() {
        try {
            const result = await this.orm.call(
                "bank.abicab",
                "download_file_github",
                []
            );
            console.log("Risultato della chiamata:", result);
            if (result) {
                // Aggiorna la vista dopo il completamento dell'azione
                await this.model.load();
                this.render();
            }
        } catch (error) {
            console.error("Errore durante la chiamata:", error);
            // Qui puoi gestire eventuali errori, ad esempio mostrando una notifica all'utente
        }
    }
});