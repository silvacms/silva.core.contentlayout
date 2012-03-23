

(function ($, infrae, jsontemplate) {
    infrae.interfaces.register('content-layout');

    var prepare_urls = function(templates) {
        var prepared = {};
        for (var key in templates) {
            if (typeof(templates[key]) == "string") {
                prepared[key] = new jsontemplate.Template(templates[key], {});
            } else {
                prepared[key] = prepare_urls(templates[key]);
            };
        };
        return prepared;
    };

    var EditorController = function(smi, urls, path) {
        return {
            add: function($slot) {
                return $slot.SMIFormPopup({
                    url: urls.actions.add.expand({path: path}),
                    payload: [{name: 'slot_id', value: $slot.data('slot-id')}]
                }).pipe(
                    function(data) {
                        if (data.extra !== undefined && data.extra.block_id) {
                            var $result = $('<div class="edit-block" />');

                            $result.attr('data-block-id', data.extra.block_id);
                            $result.append(data.extra.block_data);

                            // Refresh the move
                            $slot.append($result);
                            //$slot.blockable('refresh');
                        };
                        return data;
                    }
                );
            },
            edit: function($block) {
                return $block.SMIFormPopup({
                    url: urls.actions.edit.expand({
                        path: path,
                        id: $block.data('block-id')
                    })
                }).pipe(
                    function(data) {
                        if (data.extra !== undefined) {
                            $block.empty();
                            $block.append(data.extra.block_data);
                        };
                    }
                );
            },
            remove: function($block) {
                return smi.ajax.query(
                    urls.actions.remove.expand({
                        path: path,
                        id: $block.data('block-id')
                    })
                ).pipe(
                    function(data) {
                        if (data.success) {
                            $block.remove();
                        };
                    }
                );
            }
        };
    };

    var LayerView = function($body, layer, api) {
        var $layer = $(layer);
        var $selected = $([]);
        var $candidate = $([]);
        var timer = null;

        var update = function() {
            var offset, width, height;
            if ($candidate.length) {
                offset = $candidate.offset();
                width = $candidate.width();
                height = $candidate.height();
                $layer.find('#contentlayout-block-actions').toggle($candidate.hasClass('edit-block'));
                if (!$selected.length) {
                    $layer.appendTo($body);
                };
                $layer.offset(offset);
                $layer.width(width);
                $layer.height(height);
            } else {
                $layer.detach();
            };
            $selected = $candidate;
            $candidate = $([]);
        };

        var schedule_update = function() {
            if (timer !== null) {
                clearTimeout(timer);
            };
            timer = setTimeout(update, 200);
        };
        var clear = function() {
            if (timer !== null) {
                clearTimeout(timer);
                timer = null;
            };
            $candidate = $([]);
            update();
        };

        $body.delegate('.edit-block, .edit-slot', 'mouseenter', function(event) {
            $candidate = $(this);
            schedule_update();
            event.stopPropagation();
        });
        $layer.bind('mouseleave', function(event) {
            if (!$candidate.length) {
                schedule_update();
            };
            event.stopPropagation();
        });
        $layer.delegate('#contentlayout-add-block', 'click', function() {
            var $slot = $selected.closest('div.edit-slot');
            if ($slot.length) {
                api.add($slot);
            };
        });
        $layer.delegate('#contentlayout-edit-block', 'click', function() {
            var $block = $selected.closest('div.edit-block');
            if ($block.length) {
                api.edit($block);
            };
        });
        $layer.delegate('#contentlayout-remove-block', 'click', function() {
            var $block = $selected.closest('div.edit-block');
            if ($block.length) {
                api.remove($block).pipe(function(data) {
                    clear();
                    return data;
                });
            };
        });
    };

    $(document).bind('load-smiplugins', function(event, smi) {
        var urls = prepare_urls(smi.options.contentlayout);

        $.ajax({
            url: smi.options.contentlayout.layer,
            async: false,
            dataType: 'html'
        }).pipe(function (layer) {
            infrae.views.view({
                iface: 'content-layout',
                name: 'content',
                factory: function($content, data, smi) {
                    var path = smi.opened.path + (data.path !== undefined ? '/' + data.path : '');
                    var api = EditorController(smi, urls, path);

                    return {
                        html_url: urls.url.expand({path: path}),
                        iframe: true,
                        nocache: true,
                        render: function($document) {
                            var $body = $document.find('body');
                            var $slots = $body.find('div.edit-slot');

                            $document.ready(function () {
                                LayerView($body, layer, api);
                            });

                            // Move action
                            // $slots.each(function () {
                            //     $(this).blockable({
                            //         handle: 'a.move-block',
                            //         placeholder: 'block-placeholder',
                            //         forcePlaceholderSize: true,
                            //         connectWith: $slots,
                            //         tolerance: "pointer",
                            //         base: $document,
                            //         helper: function(event, $element) {
                            //             return $element.clone().addClass('block-moving').appendTo($body);
                            //         }

                            //     });
                            // });

                            // Disable links and selection
                            $body.delegate('a', 'click', function (event) {
                                event.preventDefault();
                            });
                            $body.disableSelection();
                        },
                        cleanup: function() {
                            $content.empty();
                        }
                    };
                }

            });

        });
    });
})(jQuery, infrae, jsontemplate);
