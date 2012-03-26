

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
                            $slot.blockable('refresh');
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

    var Layer = function($origin) {
        var layer = {
            contained: $([]),
            init: function($origin) {
                var offset = $origin.offset();

                this.top = offset.top;
                this.left = offset.left;
                this.height = $origin.outerHeight();
                this.width = $origin.outerWidth();
                this.update();
                return this;
            },
            update: function() {
                this.bottom = this.top + this.height;
                this.right = this.left + this.width;
            },
            add: function($other) {
                var min_height = $other.outerHeight();
                var min_width = $other.outerWidth();

                if (this.height < min_height) {
                    this.height = min_height;
                };
                if (this.width < min_width) {
                    this.width = min_width;
                };
                this.contained = $other;
                this.update();
            },
            move: function(event) {
                var x = event.pageX, y = event.pageY;

                if (y < this.top || x < this.left || y > this.bottom || x > this.right) {
                    return;
                };
                var height = this.contained.outerHeight();
                var width = this.contained.outerWidth();
                var top = y, left = x;
                if (this.bottom - top < height) {
                    top = this.bottom - height;
                };
                if (this.right - left < width) {
                    left = this.right - width;
                };
                this.contained.offset({top: top, left:left});
            },
            cover: function($other) {
                // Conver $origin with $other, being sure contained are here too.
                $other.offset(this);
                $other.width(this.width);
                $other.height(this.height);
                this.contained.offset(this);
            }
        };
        return layer.init($origin);
    };

    var LayerView = function($body, layer, api) {
        var $layer = $(layer);
        var position = null;
        var $actions = $layer.find('#contentlayout-actions');
        var $selected = $([]);
        var $candidate = $([]);
        var timer = null;
        var disabled = false;

        var update_layer = function() {
            if ($candidate.length) {
                position = Layer($candidate);
                $layer.find('#contentlayout-block-actions').toggle(
                    $candidate.hasClass('edit-block'));
                if (!$selected.length) {
                    $layer.appendTo($body);
                };
                position.add($actions);
                position.cover($layer);
            } else {
                $layer.detach();
                position = null;
            };
            $selected = $candidate;
            $candidate = $([]);
        };

        var select_layer = function($element) {
            if (!disabled) {
                $candidate = $element;
                if (timer !== null) {
                    clearTimeout(timer);
                };
                timer = setTimeout(update_layer, 200);
            };
        };

        var clear_layer = function(disable) {
            if (!disabled) {
                if (timer !== null) {
                    clearTimeout(timer);
                    timer = null;
                };
                if ($selected.length) {
                    $candidate = $([]);
                    update_layer();
                };
            };
            if (disable !== undefined) {
                disabled = disable;
            }
        };

        $body.delegate('.edit-block, .edit-slot', 'mouseenter', function(event) {
            select_layer($(this));
            event.stopPropagation();
        });
        $layer.bind('mouseleave', function(event) {
            if (!$candidate.length) {
                clear_layer();
            };
            event.stopPropagation();
        });
        $layer.delegate('#contentlayout-add-block', 'click', function(event) {
            var $slot = $selected.closest('div.edit-slot');
            if ($slot.length) {
                api.add($slot);
            };
            event.stopPropagation();
            event.preventDefault();
        });
        $layer.delegate('#contentlayout-edit-block', 'click', function(event) {
            var $block = $selected.closest('div.edit-block');
            if ($block.length) {
                api.edit($block);
            };
            event.stopPropagation();
            event.preventDefault();
        });
        $layer.delegate('#contentlayout-move-block', 'click', function(event) {
            var $block = $selected.closest('div.edit-block');
            var $slot = $selected.closest('div.edit-slot');
            if ($block.length) {
                $slot.blockable('capture', event, $block);
            };
            event.stopPropagation();
            event.preventDefault();
        });
        $body.bind('blockstart', function(event) {
            clear_layer(true);
        });
        $body.bind('blockstop', function(event) {
            clear_layer(false);
        });
        $layer.delegate('#contentlayout-remove-block', 'click', function(event) {
            var $block = $selected.closest('div.edit-block');
            if ($block.length) {
                api.remove($block).pipe(function(data) {
                    clear_layer();
                    return data;
                });
            };
            event.stopPropagation();
            event.preventDefault();
        });
        $layer.bind('click', function(event) {
            if (position !== null) {
                position.move(event);
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
                            $slots.each(function () {
                                $(this).blockable({
                                    placeholder: 'contentlayout-block-placeholder',
                                    forcePlaceholderSize: true,
                                    connectWith: $slots,
                                    tolerance: "pointer",
                                    mouseSource: $document,
                                    mouseCapture: false,
                                    helper: function(event, $element) {
                                        return $element.clone().addClass('block-moving').appendTo($body);
                                    }

                                });
                            });

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
