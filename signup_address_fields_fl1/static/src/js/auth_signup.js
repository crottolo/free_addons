// -*- coding: utf-8 -*-

odoo.define('signup_address_fields_fl1.auth_signup', function(require){
    'use strict';
    require('web.dom_ready');
    var publicWidget = require('web.public.widget');
    publicWidget.registry.authsignup = publicWidget.Widget.extend({
        selector: ".field-user-type,.field-mobile",
        events: {
            'change #mobile': 'mobile_change',
        },
        start: function () {
            var defult_selected = this.$el.find('.person').is(":checked")
            if (defult_selected == true) {
                
            }
        },

        mobile_change: function (e) {
            console.log('mobile_change', e)
        },
       
    });
});