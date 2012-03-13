

(function ($, infrae, jsontemplate) {
    infrae.interfaces.register('content-layout');

    var bind_effects = function($body) {
        // Mouse over make actions appears.
        $body.delegate('div.edit-slot', 'mouseenter', function() {
            var $slot = $(this);

            $slot.children('.slot-action').show();
        });
        $body.delegate('div.edit-slot', 'mouseleave', function() {
            var $slot = $(this);

            $slot.children('.slot-action').hide();
        });
        $body.delegate('div.edit-block', 'mouseenter', function() {
            $(this).children('.block-action').show();
        });
        $body.delegate('div.edit-block', 'mouseleave', function() {
            $(this).children('.block-action').hide();
        });
    };

    $(document).bind('load-smiplugins', function(event, smi) {
        var add_url_template = new jsontemplate.Template(
            smi.options.contentlayout.add_url, {});
        var edit_url_template = new jsontemplate.Template(
            smi.options.contentlayout.edit_url, {});
        var delete_url_template = new jsontemplate.Template(
            smi.options.contentlayout.delete_url, {});

        var AddDialog = function($slot) {
            $slot.SMIFormPopup({
                url: add_url_template.expand({path: smi.opened.path}),
                payload: [{name: 'slot_id', value: $slot.data('slot-id')}]
            }).pipe(
                function(data) {
                    if (data.extra !== undefined && data.extra.block_id) {
                        var $template = $slot.find('.edit-block-template');
                        var $result = $template.clone();

                        $result.removeClass('edit-block-template');
                        $result.attr('data-block-id', data.extra.block_id);
                        $result.children('.block-data').append(data.extra.html);
                        $result.insertBefore($template);
                    };
                    return data;
                }
            );
        };

        var EditDialog = function($block) {
            var $dialog = $('<div title="Edit"></div>');

            $dialog.bind('dialogclose', function() {
                $dialog.remove();
            });
            $dialog.dialog({autoOpen: false, modal:true});
            infrae.ui.ShowDialog($dialog);
        };


        infrae.views.view({
            iface: 'content-layout',
            name: 'content',
            factory: function($content, data, smi) {
                return {
                    data_template: true,
                    iframe: true,
                    nocache: true,
                    render: function($document) {
                        var $body = $document.find('body');

                        // Remove action
                        $body.delegate('div.edit-block a.remove-block', 'click', function() {
                            var $block = $(this).closest('div.edit-block');

                            $block.remove();
                        });
                        // Edit action
                        $body.delegate('div.edit-block a.edit-block', 'click', function() {
                            var $block = $(this).closest('div.edit-block');

                            EditDialog();
                            $block.find('span').text(prompt('text'));
                        });
                        // Add action
                        $body.delegate('div.edit-slot a.add-block', 'click', function() {
                            AddDialog($(this).closest('div.edit-slot'));
                        });
                        // Move action
                        $body.find('div.edit-blocks').sortable({
                            handle: 'a.move-block',
                            connectWith: 'div.edit-blocks',
                            containment: $body
                        });

                        bind_effects($body);
                    },
                    cleanup: function() {
                        $content.empty();
                    }
                };
            }
        });
    });
})(jQuery, infrae, jsontemplate);
