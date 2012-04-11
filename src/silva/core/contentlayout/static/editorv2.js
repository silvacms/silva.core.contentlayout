

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

    var Editor = function(smi, urls, path) {
        var validation_cache = {};
        var events = {
            onchange: infrae.deferred.Callbacks()
        };
        var api = {
            events: {
                onchange: function(callback) {
                    events.onchange.add(callback);
                }
            },
            add: function(state) {
                return state.slot.$slot.SMIFormPopup({
                    url: urls.actions.add.expand({
                        path: path,
                        slot_id: state.slot.id
                    })
                }).pipe(
                    function(data) {
                        if (data.extra !== undefined && data.extra.block_id) {
                            var $result = $('<div class="edit-block" />');

                            $result.attr('data-block-id', data.extra.block_id);
                            if (data.extra.block_editable) {
                                $result.attr('data-block-editable', 'true');
                            };
                            $result.append(data.extra.block_data);
                            state.slot.$slot.append($result);
                            state.slot.append($result);
                            events.onchange.invoke();
                        };
                        return data;
                    }
                );
            },
            edit: function(state) {
                return state.current.$block.SMIFormPopup({
                    url: urls.actions.edit.expand({
                        path: path,
                        slot_id: state.slot.id,
                        block_id: state.current.id
                    })
                }).done(
                    function(data) {
                        if (data.extra !== undefined) {
                            state.current.$block.empty();
                            state.current.$block.append(data.extra.block_data);
                            events.onchange.invoke({
                                modified: true,
                                current: state.current,
                                slot: state.slot
                            });
                        };
                    }
                );
            },
            move_validate: function(state) {
                var block_cache = validation_cache[state.current.id];
                var slot_cache = undefined;

                if (block_cache === undefined) {
                    block_cache = validation_cache[state.current.id] = {};
                };
                slot_cache = block_cache[state.slot.id];
                if (slot_cache !== undefined && !slot_cache.isRejected()) {
                    return slot_cache.pipe(function (data) {
                        return {
                            success: data.success,
                            failed: data.failed,
                            slot: state.slot,
                            current: state.current,
                            index: state.index,
                            fatal: false
                        };
                    });
                };
                return block_cache[state.slot.id] = smi.ajax.query(
                    urls.actions.validate.expand({
                        path: path,
                        slot_id: state.slot.id,
                        block_id: state.current.id
                    })
                ).pipe(function(data) {
                    return {
                        success: data.success,
                        failed: !data.success,
                        slot: state.slot,
                        current: state.current,
                        index: state.index,
                        fatal: false
                    };
                }, function(request) {
                    return $.Deferred().reject({
                        failed: true,
                        success: false,
                        fatal: true
                    });
                });
            },
            move: function(state) {
                return smi.ajax.query(
                    urls.actions.move.expand({
                        path: path,
                        slot_id: state.slot.id,
                        block_id: state.current.id
                    }),
                    [{name: 'index', value: state.index}]
                ).pipe(function(data) {
                    return $.Deferred().resolve({
                        success: data.success,
                        failed: !data.success,
                        slot: state.slot,
                        current: state.current,
                        index: state.index,
                        fatal: false
                    });
                }, function(request) {
                    return $.Deferred().reject({
                        failed: true,
                        success: false,
                        fatal: true
                    });
                });
            },
            remove: function(state) {
                return smi.ajax.query(
                    urls.actions.remove.expand({
                        path: path,
                        slot_id: state.slot.id,
                        block_id: state.current.id
                    })
                ).done(
                    function(data) {
                        if (data.success) {
                            state.slot.remove(state.current);
                            events.onchange.invoke({
                                removed: true,
                                current: state.current,
                                slot: state.slot
                            });
                            state.current.destroy();
                        };
                    }
                );
            }
        };
        return api;
    };

    var Element = function($element) {
        var $current = $element;
        var placeholding = null;
        var api = {
            placeholder_set: function($placeholder, heigth, width) {
                if (placeholding === null) {
                    placeholding = {
                        container: $current.parent(),
                        item: $current.prev(),
                        direction: "after"
                        };
                    $placeholder.hide();
                    $current = $placeholder;
                    $element.before($placeholder);
                    $element.detach();
                    $placeholder.width(width || this.width);
                    $placeholder.height(heigth || this.height);
                    $placeholder.show();
                };
            },
            placeholder_clear: function() {
                if (placeholding !== null) {
                    $current.before($element);
                    $current.remove();
                    $current = $element;
                    placeholding = null;
                };
            },
            placeholder_revert: function() {
                if (placeholding !== null) {
                    $current.remove();
                    $current = $element;
                    this.deplace(placeholding);
                    placeholding = null;
                };
            },
            deplace: function(position) {
                if (position.item.length) {
                    position.item[position.direction]($current);
                } else {
                    position.container.prepend($current);
                }
            },
            destroy: function() {
                if (placeholding !== null) {
                    $current.remove();
                    placeholding = null;
                };
                $element.remove();
            },
            over: function(event) {
                var x = event.pageX, y = event.pageY;
                if (y < this.top || x < this.left || y > this.bottom || x > this.right) {
                    return null;
                };
                return this;
            },
            update: function() {
                var offset = $current.offset();
                this.top = offset.top;
                this.left = offset.left;
                this.height = $current.outerHeight();
                this.width = $current.outerWidth();
                // To simplify computation.
                this.bottom = this.top + this.height;
                this.right = this.left + this.width;
            }
        };
        api.update();
        return api;
    };


    var AddView = function($document, editor, shortcuts, containers, $component) {
        var $placeholder = $('<div class="contentlayout-block-valid-placeholder"></div>');
        var block = Block($('<div class="edit-block" />'));
        var slot = null;

        var save = function(event) {
            finish(false);
            event.stopPropagation();
            event.preventDefault();
        };

        var cancel = function(event) {
            finish(true);
            event.stopPropagation();
            event.preventDefault();
        };

        var finish = function(failed) {
            $document.unbind('click', save);
            shortcuts.remove('editor', 'adding');

            return $.Deferred().reject().always(function() {
                block.placeholder_clear();
            }).fail(function() {
                if (slot !== null) {
                    slot.remove(block);
                };
                block.destroy();
            }).always(function() {
                containers.update();
                containers.events.restore();
                $document.css('cursor', 'inherit');
            });
        };

        var reorder = function(info) {
            var index = 0;
            var position = {container: info.slot.$slot, item: []};

            if (info.current.$block !== undefined) {
                position.item = info.current.$block;
                index = info.slot.index(info.current);
                if ((!info.slot.horizontal && info.mouse.direction.bottom) ||
                    (info.slot.horizontal && info.mouse.direction.right)) {
                    index += 1;
                    position.direction = "after";
                } else {
                    position.direction = "before";
                };
                if (info.slot === slot) {
                    var current = slot.index(block);
                    if (current < index) {
                        index -= 1;
                    };
                };
            };
            if (info.slot.get(index) !== block) {
                if (slot !== null) {
                    slot.remove(block);
                };
                info.slot.add(block, index);
                slot = info.slot;
                block.deplace(position);
                containers.update();
            };
        };

        var bootstrap = function() {
            $placeholder.html($component.children().clone());
            block.placeholder_set($placeholder, '1em', '100%');
            $document.css('cursor', 'move');

            containers.events.snapshot(event);
            containers.events.onenter(function(event) {
               reorder(this);
            });
            containers.events.onmove(function(event) {
                if (this.current !== null && this.mouse.changed !== false) {
                    reorder(this);
                };
            });
            $document.bind('click', save);
            shortcuts.bind('editor', 'adding', ['ctrl+s'], save);
            shortcuts.bind('editor', 'adding', ['esc'], cancel);
        };

        bootstrap();
    };

    var MoveView = function($document, editor, shortcuts, containers, original) {
        var $placeholder = $('<div class="contentlayout-block-valid-placeholder"></div>');
        var $helper = null;
        var slot = original.slot;
        var block = original.current;
        var validator = null;
        // Save original index
        original.index = slot.index(block);

        var save = function(event) {
            finish(false);
            event.stopPropagation();
            event.preventDefault();
        };

        var cancel = function(event) {
            finish(true);
            event.stopPropagation();
            event.preventDefault();
        };

        var finish = function(failed) {
            $document.unbind('click', save);
            shortcuts.remove('editor', 'moving');
            return (validator !== null && failed !== true
             ?  validator.done(function() {
                 $placeholder.attr('class', 'contentlayout-block-placeholder');
             }).pipe(editor.move, function() {
                 return $.Deferred().reject();
             })
             : $.Deferred().reject({
                 success: true,
                 slot: slot,
                 current: block})
            ).done(function() {
                block.placeholder_clear();
            }).fail(function() {
                if (original.slot !== slot ||
                    original.index !== slot.index(block)) {
                    slot.remove(block);
                    original.slot.add(block, original.index);
                };
                block.placeholder_revert();
            }).always(function() {
                $helper.remove();
                containers.update();
                containers.events.restore();
                $document.css('cursor', 'inherit');
            });
        };

        var reorder = function(info) {
            var index = 0;
            var position = {container: info.slot.$slot, item: []};

            if (info.current.$block !== undefined) {
                position.item = info.current.$block;
                index = info.slot.index(info.current);
                if ((!info.slot.horizontal && info.mouse.direction.bottom) ||
                    (info.slot.horizontal && info.mouse.direction.right)) {
                    index += 1;
                    position.direction = "after";
                } else {
                    position.direction = "before";
                };
                if (info.slot === slot) {
                    var current = slot.index(block);
                    if (current < index) {
                        index -= 1;
                    };
                };
            };
            if (info.slot.get(index) !== block) {
                slot.remove(block);
                info.slot.add(block, index);
                slot = info.slot;
                block.deplace(position);
                containers.update();
                validator = editor.move_validate({
                    slot: slot,
                    current: block,
                    index: index
                }).pipe(function(data) {
                    var result = $.Deferred();

                    if (data.success) {
                        $placeholder.attr('class', 'contentlayout-block-valid-placeholder');
                        result.resolve(data);
                    } else {
                        $placeholder.attr('class', 'contentlayout-block-invalid-placeholder');
                        result.reject(data);
                    };
                    return result;
                }, function(data) {
                    finish(true);
                });
            };
        };

        var bootstrap = function() {
            $helper = block.$block.clone();
            $helper.css('position', 'absolute');
            $helper.css('opacity', '0.5');
            $helper.offset(original.mouse);
            $document.append($helper);
            $document.css('cursor', 'move');
            block.placeholder_set($placeholder);

            containers.events.snapshot();
            containers.events.onenter(function(event) {
               reorder(this);
            });
            containers.events.onmove(function(event) {
                $helper.offset(this.mouse);
                if (this.current !== null && this.mouse.changed !== false) {
                    reorder(this);
                };
            });
            $document.bind('click', save);
            shortcuts.bind('editor', 'moving', ['ctrl+s'], save);
            shortcuts.bind('editor', 'moving', ['esc'], cancel);
        };
        bootstrap();
    };


    var View = function($document, $layer, $components, editor, shortcuts, containers) {
        var selected = null;
        var api = {
            actions: {
                add: function($component) {
                    if (selected !== null) {
                        api.disable();
                    };
                    AddView($document, editor, shortcuts, containers, $component);
                },
                edit: function() {
                    if (selected !== null && selected.current.$block !== undefined) {
                        editor.edit(selected);
                    };
                },
                remove: function() {
                    if (selected !== null && selected.current.$block !== undefined) {
                        infrae.ui.ConfirmationDialog({
                            title: 'Remove block',
                            message: 'Please confirm the permanent deletion of the block'
                        }).done(function () {
                            editor.remove(selected);
                        });
                    };
                },
                move: function() {
                    if (selected !== null && selected.current.$block !== undefined) {
                        MoveView($document, editor, shortcuts, containers, selected);
                        api.disable();
                    };
                }
            },
            update: function() {
                if (selected !== null) {
                    $layer.offset(selected.current);
                    $layer.width(selected.current.width);
                    $layer.height(selected.current.height);
                };
            },
            enable: function(other) {
                var $block = other.current.$block;

                $layer.find('#contentlayout-actions').toggle($block !== undefined);
                if (selected === null) {
                    $layer.appendTo($document);
                };
                selected = other;
                api.update();
            },
            disable: function() {
                if (selected !== null) {
                    $layer.detach();
                    selected = null;
                };
            }
        };
        // Display / hide layer
        containers.events.onenter(function () {
            api.enable(this);
        });
        containers.events.onswitch(function () {
            api.enable(this);
        });
        containers.events.onleave(function () {
            api.disable();
        });
        editor.events.onchange(function() {
            containers.update();
            if (this.modified) {
                api.enable(this);
            } else if (this.removed) {
                api.disable();
            };
        });
        // Actions
        var add = function(event){
            api.actions.add($(this));
            event.stopPropagation();
            event.preventDefault();
        };
        var edit = function(event) {
            api.actions.edit();
            event.stopPropagation();
            event.preventDefault();
        };
        var move = function(event) {
            api.actions.move();
            event.stopPropagation();
            event.preventDefault();
        };
        var remove = function(event) {
            // We should add a confirmation here.
            api.actions.remove();
            event.stopPropagation();
            event.preventDefault();
        };
        $components.delegate('div.component', 'click', add);
        $layer.delegate('#contentlayout-edit-block', 'click', edit);
        shortcuts.bind('editor', null, ['ctrl+e'], edit);
        $layer.delegate('#contentlayout-move-block', 'click', move);
        shortcuts.bind('editor', null, ['ctrl+m'], move);
        $layer.delegate('#contentlayout-remove-block', 'click', remove);
        shortcuts.bind('editor', null, ['ctrl+d'], remove);
        return api;
    };

    var Block = function($block) {
        var api = {};
        var position = Element($block);
        $.extend(api, position, {
            id: $block.data('block-id'),
            $block: $block
        });
        return api;
    };

    var Slot = function($slot, selector) {
        var api = {};
        var position = Element($slot);
        var blocks = [];

        // Find contained blocks.
        $(selector, $slot).each(function () {
            blocks.push(Block($(this)));
        });

        $.extend(api, position, {
            id: $slot.data('slot-id'),
            $slot: $slot,
            vertical: false,
            update: function() {
                for (var i=0; i < blocks.length; i++) {
                    blocks[i].update();
                };
                position.update();
                api.horizontal = blocks.length ?
                    (/left|right/).test(blocks[0].$block.css('float')) ||
                    (/inline|table-cell/).test(blocks[0].$block.css('display'))
                    : false;
            },
            over: function(event) {
                var current_slot = position.over(event);
                var current_item = null;

                if (current_slot !== null) {
                    for (var i=0; i < blocks.length; i++) {
                        current_item = blocks[i].over(event);
                        if (current_item !== null) {
                            return current_item;
                        };
                    };
                };
                return current_slot;
            },
            get: function(index) {
                return blocks[index];
            },
            index: function(item) {
                return blocks.indexOf(item);
            },
            add: function(item, index) {
                blocks.splice(index, 0, item);
            },
            remove: function(item) {
                var index = api.index(item);
                var removed = null;

                if (index > -1) {
                    return blocks.splice(index, 1)[0];
                };
                return null;
            }
        });
        return api;
    };

    var Mouse = function() {
        var api = {
            top: -1,
            left: -1,
            threshold: 15,
            changed: false,
            direction: {
                right: null,
                bottom: null,
                changed: false
            },
            previous: {
                top: -1,
                left: -1,
                direction: {
                    right: null,
                    bottom: null
                }
            },
            update: function(event) {
                if (event.pageX == this.left && event.pageY == this.top) {
                    return false;
                };
                this.left = event.pageX;
                this.top = event.pageY;
                this.changed = Math.abs(this.left - this.previous.left) > this.threshold ||
                    Math.abs(this.top - this.previous.top) > this.threshold;
                if (this.changed) {
                    this.direction.right = this.left > this.previous.left;
                    this.direction.bottom = this.top > this.previous.top;
                    this.direction.changed =
                        this.direction.right != this.previous.direction.right ||
                        this.direction.bottom != this.previous.direction.bottom;
                }
                return true;
            },
            finish: function(event) {
                if (this.changed) {
                    this.previous.top = this.top;
                    this.previous.left = this.left;
                    this.previous.direction.right = this.direction.right;
                    this.previous.direction.bottom = this.direction.bottom;
                };
            }
        };
        return api;
    };

    var Slots = function($document, $slots, selector) {
        var slots = [];
        var current = null;
        var slot = null;
        var timer = null;
        var mouse = Mouse();
        var events = {
            onenter: infrae.deferred.Callbacks(),
            onswitch: infrae.deferred.Callbacks(),
            onleave: infrae.deferred.Callbacks(),
            onmove: infrae.deferred.Callbacks()
        };
        var api = {
            events: {
                onenter: function(callback) {
                    events.onenter.add(callback);
                },
                onswitch: function(callback) {
                    events.onswitch.add(callback);
                },
                onleave: function(callback) {
                    events.onleave.add(callback);
                },
                onmove: function(callback) {
                    events.onmove.add(callback);
                },
                snapshot: function(event) {
                    for (var name in events) {
                        events[name].push();
                    };
                },
                restore: function(event) {
                    for (var name in events) {
                        events[name].pop();
                    };
                    if (current !== null) {
                        events.onenter.invoke(SlotEvent(), [null]);
                    }
                }
            },
            update: function() {
                for (var i=0; i < slots.length; i++) {
                    slots[i].update();
                };
            }
        };

        var SlotEvent = function() {
            return {
                mouse: mouse,
                current: current,
                slot: slot
            };
        };

        var lookup = function(event) {
            var new_current = null;
            var previous_current = current;

            for (var i=0; i < slots.length; i++) {
                new_current = slots[i].over(event);
                if (new_current !== null) {
                    slot = slots[i];
                    if (new_current !== current) {
                        current = new_current;
                        if (previous_current === null) {
                            events.onenter.invoke(SlotEvent(), [event]);
                        } else {
                            events.onswitch.invoke(SlotEvent(), [event]);
                        };
                        return true;
                    };
                    return false;
                };
            };
            if (current !== null) {
                events.onleave.invoke(SlotEvent(), [event]);
                current = null;
                slot = null;
                return true;
            };
            return false;
        };

        var move = function(event) {
            if (!mouse.update(event)) {
                // The mouse didn't move
                return;
            };
            var new_current = null;
            var previous_current = current;

            for (var i=0; i < slots.length; i++) {
                new_current = slots[i].over(event);
                if (new_current !== null) {
                    slot = slots[i];
                    if (new_current !== current) {
                        current = new_current;
                        if (previous_current === null) {
                            events.onenter.invoke(SlotEvent(), [event]);
                        } else {
                            events.onswitch.invoke(SlotEvent(), [event]);
                        }
                    } else {
                        events.onmove.invoke(SlotEvent(), [event]);
                    };
                    mouse.finish(event);
                    return;
                };
            };
            if (current !== null) {
                events.onleave.invoke(SlotEvent(), [event]);
                current = null;
                slot = null;
            } else {
                events.onmove.invoke(SlotEvent(), [event]);
            };
            mouse.finish(event);
        };

        $slots.each(function() {
            slots.push(Slot($(this), selector));
        });

        $document.bind('mousemove', function(event) {
            if (timer !== null) {
                clearTimeout(timer);
            };
            timer = setTimeout(function() {
                move(event);
                timer = null;
            }, 0);
        });
        return api;
    };

    $(document).bind('load-smiplugins', function(event, smi) {
        var urls = prepare_urls(smi.options.contentlayout);
        var components_position = [30, 200];

        infrae.views.view({
            iface: 'content-layout',
            name: 'content',
            factory: function($content, data, smi) {
                var path = smi.opened.path + (data.identifier ? '/' + data.identifier : '');
                var editor = Editor(smi, urls, path);
                var $components = $(data.components);
                var $layer = $(data.layer);

                return {
                    html_url: urls.url.expand({path: path}),
                    iframe: true,
                    nocache: true,
                    render: function($content) {
                        var $body = this.$document.find('body');
                        var $slots = $body.find('div.edit-slot');
                        var timer = null;
                        smi.shortcuts.create('editor', $content, true);

                        var slots = Slots($body, $slots, '> div.edit-block');
                        var view = View($body, $layer, $components, editor, smi.shortcuts, slots);

                        // When the iframe is resize, positions need to be updated.
                        this.$window.bind('resize', function() {
                            if (timer !== null) {
                                clearTimeout(timer);
                            };
                            timer = setTimeout(function() {
                                slots.update();
                                view.update();
                                timer = null;
                            }, 50);
                        });

                        $components.dialog({position: components_position, closeOnEscape: false});
                        $components.accordion();
                        $components.bind('dialogclose', function() {
                            components_position = $components.dialog('option', 'position');
                            $components.remove();
                            $components = null;
                        });

                        // Disable links and selection
                        $body.delegate('a', 'click', function (event) {
                            event.preventDefault();
                        });
                        $body.disableSelection();

                    },
                    cleanup: function() {
                        if ($components !== null) {
                            $components.dialog('close');
                        };
                        smi.shortcuts.remove('editor');
                        $content.empty();
                    }
                };
            }
        });
    });
})(jQuery, infrae, jsontemplate);


