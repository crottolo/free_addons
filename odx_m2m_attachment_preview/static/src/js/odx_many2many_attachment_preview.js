odoo.define('odx_m2m_attachment_preview.many2many_attachment_preview_widget', function (require) {
    "use strict";

var AbstractField = require('web.AbstractField');
var core = require('web.core');
var registry = require('web.field_registry');
var DocumentViewer = require('odx_m2m_attachment_preview.legacy.DocumentViewer');


var _t = core._t;
var _lt = core._lt;
var qweb = core.qweb;

/**
 * Widget to upload or delete one or more files at the same time.
 */
var FieldMany2ManyAttachmentPreview = AbstractField.extend({
    template: "FieldBinaryFileUploader",
    template_files: "FieldAttachmentFileUploader.files",
    supportedFieldTypes: ['many2many'],
    fieldsToFetch: {
        name: {type: 'char'},
        mimetype: {type: 'char'},
    },
    events: {
        'click .o_attach': '_onAttach',
        'click .o_attachment_delete': '_onDelete',
        'change .o_input_file': '_onFileChanged',
        'click .o_attachment_wrap': '_previewAttachment',
    },
    /**
     * @constructor
     */
    init: function () {
        this._super.apply(this, arguments);

        if (this.field.type !== 'many2many' || this.field.relation !== 'ir.attachment') {
            var msg = _t("The type of the field '%s' must be a many2many field with a relation to 'ir.attachment' model.");
            throw _.str.sprintf(msg, this.field.string);
        }

        this.uploadedFiles = {};
        this.uploadingFiles = [];
        this.fileupload_id = _.uniqueId('oe_fileupload_temp');
        this.accepted_file_extensions = (this.nodeOptions && this.nodeOptions.accepted_file_extensions) || this.accepted_file_extensions || '*';
        $(window).on(this.fileupload_id, this._onFileLoaded.bind(this));

        this.metadata = {};
    },

    destroy: function () {
        this._super();
        $(window).off(this.fileupload_id);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Compute the URL of an attachment.
     *
     * @private
     * @param {Object} attachment
     * @returns {string} URL of the attachment
     */
    _getFileUrl: function (attachment) {
        // return '/web/content/' + attachment.id + '?download=true';
        return '/web/content/' + attachment.id;
    },
    /**
     * Process the field data to add some information (url, etc.).
     *
     * @private
     */
    _generatedMetadata: function () {
        var self = this;
        _.each(this.value.data, function (record) {
            // tagging `allowUnlink` ascertains if the attachment was user
            // uploaded or was an existing or system generated attachment
            self.metadata[record.id] = {
                allowUnlink: self.uploadedFiles[record.data.id] || false,
                url: self._getFileUrl(record.data),
            };
        });
    },
    /**
     * @private
     * @override
     */
    _render: function () {
        // render the attachments ; as the attachments will changes after each
        // _setValue, we put the rendering here to ensure they will be updated

        this._generatedMetadata();
        this.$('.oe_placeholder_files, .o_attachments')
            .replaceWith($(qweb.render(this.template_files, {
                widget: this,
            })));
        this.$('.oe_fileupload').show();

        this.$('.o_image[data-mimetype^="image"]').each(function () {
            var $img = $(this);
            if (/gif|jpe|jpg|png/.test($img.data('mimetype')) && $img.data('src')) {
                $img.css('background-image', "url('" + $img.data('src') + "')");
            }
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _onAttach: function () {
        // This widget uses a hidden form to upload files. Clicking on 'Attach'
        // will simulate a click on the related input.
        this.$('.o_input_file').click();
    },
    /**
     * @private
     * @param {MouseEvent} ev
     */
    _onDelete: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();

        var fileID = $(ev.currentTarget).data('id');
        var record = _.findWhere(this.value.data, {res_id: fileID});
        if (record) {
            this._setValue({
                operation: 'FORGET',
                ids: [record.id],
            });
            var metadata = this.metadata[record.id];
            if (!metadata || metadata.allowUnlink) {
                this._rpc({
                    model: 'ir.attachment',
                    method: 'unlink',
                    args: [record.res_id],
                });
            }
        }
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onFileChanged: function (ev) {
        var self = this;
        ev.stopPropagation();

        var files = ev.target.files;
        var attachment_ids = this.value.res_ids;

        // Don't create an attachment if the upload window is cancelled.
        if(files.length === 0)
            return;

        _.each(files, function (file) {
            var record = _.find(self.value.data, function (attachment) {
                return attachment.data.name === file.name;
            });
            if (record) {
                var metadata = self.metadata[record.id];
                if (!metadata || metadata.allowUnlink) {
                    // there is a existing attachment with the same name so we
                    // replace it
                    attachment_ids = _.without(attachment_ids, record.res_id);
                    self._rpc({
                        model: 'ir.attachment',
                        method: 'unlink',
                        args: [record.res_id],
                    });
                }
            }
            self.uploadingFiles.push(file);
        });

        this._setValue({
            operation: 'REPLACE_WITH',
            ids: attachment_ids,
        });

        this.$('form.o_form_binary_form').submit();
        this.$('.oe_fileupload').hide();
        ev.target.value = "";
    },
    /**
     * @private
     */
    _onFileLoaded: function () {
        var self = this;
        // the first argument isn't a file but the jQuery.Event
        var files = Array.prototype.slice.call(arguments, 1);
        // files has been uploaded, clear uploading
        this.uploadingFiles = [];

        var attachment_ids = this.value.res_ids;
        _.each(files, function (file) {
            if (file.error) {
                self.displayNotification({ title: _t('Uploading Error'), message: file.error, type: 'danger' });
            } else {
                attachment_ids.push(file.id);
                self.uploadedFiles[file.id] = true;
            }
        });

        this._setValue({
            operation: 'REPLACE_WITH',
            ids: attachment_ids,
        });
    },

    _previewAttachment: function(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        var self = this;
        var activeAttachmentID = $(ev.currentTarget).data('id');
        this._rpc({
            model: 'ir.attachment',
            method: 'read_as_sudo',
            kwargs: {
                domain: [['id', 'in', this.value.res_ids]],
                fields: ['id', 'mimetype', 'index_content'],
            },
        }).then(result => {
            this.attachments = result.map(r => {
                return {
                    id: r.id,
                    mimetype: r.mimetype,
                    fileType: r.index_content
                }
            });
            var attachmentViewer = new DocumentViewer(this, this.attachments, activeAttachmentID);
            attachmentViewer.appendTo($('body'));
        })
    }
});

registry.add("many2many_attachment_preview", FieldMany2ManyAttachmentPreview);

})