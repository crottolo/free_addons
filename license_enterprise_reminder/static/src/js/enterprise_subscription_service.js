/** @odoo-module **/

import { SubscriptionManager } from "@web_enterprise/webclient/home_menu/enterprise_subscription_service";
import { patch } from "@web/core/utils/patch";
import { browser } from "@web/core/browser/browser";
import { session } from "@web/session";
import { deserializeDateTime } from "@web/core/l10n/dates";
const { DateTime } = luxon;

const debugMode = browser.location.search.includes('debug');

if (debugMode) {
    console.log("Loading License Enterprise Reminder patch");
}

/**
 * Calcola i giorni rimanenti anticipando di 30 giorni la scadenza
 * @param {DateTime} datetime - Data di scadenza
 * @returns {number} - Giorni rimanenti meno 30 giorni
 */
function daysUntil30(datetime) {
    const duration = datetime.diff(DateTime.utc(), 'days');
    const daysLeft = Math.round(duration.values.days);
    if (debugMode) {
        console.log('Original days left:', daysLeft);
        console.log('Adjusted days left:', daysLeft - 30);
    }
    return daysLeft - 30;
}



patch(SubscriptionManager.prototype, 'license_enterprise_reminder.SubscriptionManager', {
  /**
   * @override
   * Override del getter daysLeft per anticipare di 30 giorni la scadenza
   */
  get daysLeft() {
    return daysUntil30(this.expirationDate);
  }
  
});

if (debugMode) {
    console.log("License Enterprise Reminder patch applied successfully");
}

