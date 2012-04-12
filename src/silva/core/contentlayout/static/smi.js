

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
        var validation_move = {};
        var validation_add = {};
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
                        slot_id: state.slot.id,
                        block_name: state.name
                    }),
                    payload: [{name: 'index', value: state.index}]
                }).pipe(
                    function(data) {
                        if (data.extra !== undefined) {
                            return data.extra;
                        };
                        return data;
                    }
                );
            },
            addable: function(state) {
                var slot_cache = validation_add[state.slot.id];
                var block_cache = undefined;

                if (slot_cache === undefined) {
                    slot_cache = validation_add[state.slot.id] = {};
                };
                block_cache = slot_cache[state.name];
                if (block_cache !== undefined && !block_cache.isRejected()) {
                    return block_cache.pipe(function (data) {
                        return {
                            success: data.success,
                            failed: data.failed,
                            slot: state.slot,
                            block: state.block,
                            name: state.name,
                            index: state.index,
                            fatal: false
                        };
                    });
                };
                return slot_cache[state.name] = smi.ajax.query(
                    urls.actions.addable.expand({
                        path: path,
                        slot_id: state.slot.id,
                        block_name: state.name
                    })
                ).pipe(function(data) {
                    return {
                        success: data.success,
                        failed: !data.success,
                        slot: state.slot,
                        block: state.block,
                        name: state.name,
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
            movable: function(state) {
                var block_cache = validation_move[state.current.id];
                var slot_cache = undefined;

                if (block_cache === undefined) {
                    block_cache = validation_move[state.current.id] = {};
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
                    urls.actions.movable.expand({
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


    var AddMode = function(view, $component) {
        var $placeholder = $('<div class="contentlayout-add contentlayout-valid-placeholder"></div>');
        var block = Block($('<div class="edit-block" />'));
        var slot = null;
        var validator = null;
        var deferred = $.Deferred();

        var save = function(event) {
            finish(event, false);
            if (event !== undefined) {
                event.stopPropagation();
                event.preventDefault();
            };
        };

        var cancel = function(event) {
            finish(event, true);
            if (event !== undefined) {
                event.stopPropagation();
                event.preventDefault();
            };
        };

        var finish = function(event, failed) {
            view.$body.unbind('click', save);
            view.shortcuts.remove('editor', 'adding');

            return (validator !== null && failed !== true
             ?  validator.done(function() {
                 $placeholder.attr('class', 'contentlayout-add contentlayout-placeholder');
             }).pipe(view.editor.add, function() {
                 return $.Deferred().reject();
             })
             : $.Deferred().reject({
                 success: true,
                 slot: slot,
                 current: block})
            ).always(function() {
                block.placeholder_clear();
            }).done(function(data) {
                block.block_set(data);
            }).fail(function() {
                if (slot !== null) {
                    slot.remove(block);
                };
                block.destroy();
            }).always(function() {
                view.slots.update();
                view.slots.events.restore(event);
                view.$body.css('cursor', 'inherit');
                $component.removeClass('selected');
                deferred.resolve();
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
                view.slots.update();
                $placeholder.attr('class', 'contentlayout-add contentlayout-placeholder');
                validator = view.editor.addable({
                    slot: slot,
                    block: block,
                    name: $component.data('block-name'),
                    index: index
                }).pipe(function(data) {
                    var result = $.Deferred();

                    if (data.success) {
                        $placeholder.attr('class', 'contentlayout-add contentlayout-valid-placeholder');
                        result.resolve(data);
                    } else {
                        $placeholder.attr('class', 'contentlayout-add contentlayout-invalid-placeholder');
                        result.reject(data);
                    };
                    return result;
                }, function(data) {
                    finish(true);
                });

            };
        };

        var bootstrap = function() {
            $placeholder.html($component.children().clone());
            $component.addClass('selected');
            block.placeholder_set($placeholder, '1em', '100%');
            view.$body.css('cursor', 'move');

            view.slots.events.snapshot();
            view.slots.events.onenter(function(event) {
               reorder(this);
            });
            view.slots.events.onmove(function(event) {
                if (this.current !== null && this.mouse.changed !== false) {
                    reorder(this);
                };
            });
            view.$body.bind('click', save);
            view.shortcuts.bind('editor', 'adding', ['ctrl+s'], save);
            view.shortcuts.bind('editor', 'adding', ['esc'], cancel);
        };

        bootstrap();
        return {
            cancel: cancel,
            save: save,
            promise: deferred.promise
        };
    };

    var MoveMode = function(view, original) {
        var $placeholder = $('<div class="contentlayout-valid-placeholder"></div>');
        var $helper = null;
        var slot = original.slot;
        var block = original.current;
        var validator = null;
        var deferred = $.Deferred();
        // Save original index
        original.index = slot.index(block);

        var save = function(event) {
            finish(event, false);
            if (event !== undefined) {
                event.stopPropagation();
                event.preventDefault();
            };
        };

        var cancel = function(event) {
            finish(event, true);
            if (event !== undefined) {
                event.stopPropagation();
                event.preventDefault();
            };
        };

        var finish = function(event, failed) {
            view.$body.unbind('click', save);
            view.shortcuts.remove('editor', 'moving');

            return (validator !== null && failed !== true
             ?  validator.done(function() {
                 $placeholder.attr('class', 'contentlayout-placeholder');
             }).pipe(view.editor.move, function() {
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
                view.slots.update();
                view.slots.events.restore(event);
                view.$body.css('cursor', 'inherit');
                deferred.resolve();
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
                view.slots.update();
                $placeholder.attr('class', 'contentlayout-placeholder');
                validator = view.editor.movable({
                    slot: slot,
                    current: block,
                    index: index
                }).pipe(function(data) {
                    var result = $.Deferred();

                    if (data.success) {
                        $placeholder.attr('class', 'contentlayout-valid-placeholder');
                        result.resolve(data);
                    } else {
                        $placeholder.attr('class', 'contentlayout-invalid-placeholder');
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
            view.$body.append($helper);
            view.$body.css('cursor', 'move');
            block.placeholder_set($placeholder);

            view.slots.events.snapshot();
            view.slots.events.onenter(function(event) {
               reorder(this);
            });
            view.slots.events.onmove(function(event) {
                $helper.offset(this.mouse);
                if (this.current !== null && this.mouse.changed !== false) {
                    reorder(this);
                };
            });
            view.$body.bind('click', save);
            view.shortcuts.bind('editor', 'moving', ['ctrl+s'], save);
            view.shortcuts.bind('editor', 'moving', ['esc'], cancel);
        };

        bootstrap();
        return {
            cancel: cancel,
            save: save,
            promise: deferred.promise
        };
    };


    var NormalMode = function(view, $layer, $components) {
        var selected = null;
        var delegated = null;
        var api = {
            update: function() {
                if (selected !== null) {
                    $layer.offset(selected.current);
                    $layer.width(selected.current.width);
                    $layer.height(selected.current.height);
                };
                view.slots.update();
            },
            enable: function(other) {
                var $block = other.current.$block;

                $layer.find('#contentlayout-actions').toggle($block !== undefined);
                if (selected === null) {
                    $layer.appendTo(view.$body);
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
        view.slots.events.onenter(function () {
            api.enable(this);
        });
        view.slots.events.onswitch(function () {
            api.enable(this);
        });
        view.slots.events.onleave(function () {
            api.disable();
        });
        view.editor.events.onchange(function() {
            view.slots.update();
            if (this.modified) {
                api.enable(this);
            } else if (this.removed) {
                api.disable();
            };
        });
        // Actions
        var delegate = function(view) {
            if (delegated !== null) {
                delegated.cancel();
            };
            delegated = view.apply(this, [].splice.call(arguments, 1));
            delegated.promise().always(function() { delegated = null });
        };
        var add = function(event){
            if (selected !== null) {
                api.disable();
            };
            delegate(AddMode, view, $(this));
            event.stopPropagation();
            event.preventDefault();
        };
        var edit = function(event) {
            if (selected !== null && selected.current.$block !== undefined) {
                view.editor.edit(selected);
            };
            event.stopPropagation();
            event.preventDefault();
        };
        var move = function(event) {
            if (selected !== null && selected.current.$block !== undefined) {
                delegate(MoveMode, view, selected);
                api.disable();
            };
            event.stopPropagation();
            event.preventDefault();
        };
        var remove = function(event) {
            if (selected !== null && selected.current.$block !== undefined) {
                infrae.ui.ConfirmationDialog({
                    title: 'Remove block',
                    message: 'Please confirm the permanent deletion of the block'
                }).done(function () {
                    view.editor.remove(selected);
                });
            };
            event.stopPropagation();
            event.preventDefault();
        };
        $components.delegate('div.component', 'click', add);
        $layer.delegate('#contentlayout-edit-block', 'click', edit);
        view.shortcuts.bind('editor', null, ['ctrl+e'], edit);
        $layer.delegate('#contentlayout-move-block', 'click', move);
        view.shortcuts.bind('editor', null, ['ctrl+m'], move);
        $layer.delegate('#contentlayout-remove-block', 'click', remove);
        view.shortcuts.bind('editor', null, ['ctrl+d'], remove);
        return api;
    };

    var Block = function($block) {
        var api = {};
        var position = Element($block);
        $.extend(api, position, {
            id: $block.data('block-id'),
            $block: $block,
            block_set: function(data) {
                this.id = data.block_id,
                this.$block.attr('data-block-id', data.block_id);
                this.$block.html(data.block_data);
                if (data.block_editable) {
                    this.$block.attr('data-block-editable', 'true');
                };
            }
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
                snapshot: function() {
                    for (var name in events) {
                        events[name].push();
                    };
                },
                restore: function(event) {
                    for (var name in events) {
                        events[name].pop();
                    };
                    if (event !== undefined) {
                        if (!lookup(event) && current !== null) {
                            events.onenter.invoke(SlotEvent(), [event]);
                        };
                    };
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

        $slots.each(function() {
            slots.push(Slot($(this), selector));
        });

        $document.bind('mousemove', function(event) {
            if (timer !== null) {
                clearTimeout(timer);
            };
            timer = setTimeout(function() {
                if (!mouse.update(event)) {
                    // The mouse didn't move
                    return;
                };

                if (!lookup(event)) {
                    events.onmove.invoke(SlotEvent(), [event]);
                };
                mouse.finish(event);
                timer = null;
            }, 0);
        });
        return api;
    };

    $(document).bind('load-smiplugins', function(event, smi) {
        var urls = prepare_urls(smi.options.contentlayout);
        var position = [30, 200];

        infrae.views.view({
            iface: 'content-layout',
            name: 'content',
            factory: function($content, data, smi) {
                var path = smi.opened.path + (data.identifier ? '/' + data.identifier : '');
                var $components = $(data.components);
                var $layer = $(data.layer);

                return {
                    html_url: urls.url.expand({path: path}),
                    iframe: true,
                    nocache: true,
                    editor: Editor(smi, urls, path),
                    shortcuts: smi.shortcuts,
                    render: function($content) {
                        var timer = null;

                        this.$body = this.$document.find('body');
                        this.shortcuts.create('editor', $content, true);
                        this.slots = Slots(this.$body, this.$body.find('div.edit-slot'), '> div.edit-block');

                        var mode = NormalMode(this, $layer, $components);

                        // When the iframe is resize, positions need to be updated.
                        this.$window.bind('resize', function() {
                            if (timer !== null) {
                                clearTimeout(timer);
                            };
                            timer = setTimeout(function() {
                                mode.update();
                                timer = null;
                            }, 50);
                        });

                        $components.dialog({position: position, closeOnEscape: false});
                        $components.accordion();
                        $components.bind('dialogclose', function() {
                            position = $components.dialog('option', 'position');
                            $components.remove();
                            $components = null;
                        });

                        // Disable links and selection
                        this.$body.delegate('a', 'click', function (event) {
                            event.preventDefault();
                        });
                        this.$body.disableSelection();

                    },
                    cleanup: function() {
                        if ($components !== null) {
                            $components.dialog('close');
                        };
                        this.shortcuts.remove('editor');
                        $content.empty();
                    }
                };
            }
        });
    });
})(jQuery, infrae, jsontemplate);


