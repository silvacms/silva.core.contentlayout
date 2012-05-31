

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
            change: infrae.deferred.Callbacks()
        };
        var api = {
            events: {
                onchange: function(callback) {
                    events.change.add(callback);
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
                            events.change.invoke({
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
                            state.current.destroy();
                            events.change.invoke({
                                removed: true,
                                current: state.current,
                                slot: state.slot
                            });
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
            placeholder: {
                active: function() {
                    return false;
                },
                clear: function() {
                },
                revert: function() {
                }
            },
            placehold: function($placeholder, height, width, initial) {
                if (!this.placeholder.active()) {
                    this.placeholder = {
                        $container: $current.parent(),
                        $item: $current.prev(),
                        direction: "after",
                        $placeholder: $placeholder,
                        width: width || this.width,
                        height: height || this.height,
                        active: function() {
                            return this.$placeholder !== null;
                        },
                        resize: function(fill_in) {
                            if (this.$placeholder !== null) {
                                if (fill_in === false) {
                                    this.$placeholder.height(this.height);
                                    this.$placeholder.width('100%');
                                } else {
                                    this.$placeholder.width(this.width);
                                    this.$placeholder.height(this.height);
                                };
                            };
                        },
                        revert: function() {
                            if (this.$placeholder !== null) {
                                this.$placeholder.remove();
                                this.$placeholder = null;
                                $current = $element;
                                api.deplace(this);
                            };
                        },
                        clear: function() {
                            if (this.$placeholder !== null) {
                                $current.before($element);
                                $current.remove();
                                this.$placeholder.remove();
                                this.$placeholder = null;
                                $current = $element;
                            };
                        }
                    };
                    $current = $placeholder;
                    if (initial === undefined) {
                        $element.before($placeholder);
                        $element.detach();
                        this.placeholder.resize(undefined);
                    };
                    $placeholder.show();
                };
                return this.placeholder;
            },
            deplace: function(position, fill_in) {
                if (position.$item.length) {
                    position.$item[position.direction]($current);
                } else {
                    position.$container.prepend($current);
                };
                if (this.placeholder.active()) {
                    this.placeholder.resize(fill_in);
                };
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
        return api;
    };


    var AddMode = function(view, $component) {
        var $placeholder = $('<div class="contentlayout-component contentlayout-valid-placeholder"></div>');
        var $helper = null;
        var block = Block($('<div class="contentlayout-edit-block" />'));
        var slot = null;
        var validator = null;
        var deferred = $.Deferred();
        var finishing = false;

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
            if (finishing) {
                return $.Deferred();
            };
            finishing = true;
            view.shortcuts.remove('editor', 'adding');

            return (validator !== null && failed !== true
             ?  validator.done(function() {
                 $placeholder.attr('class', 'contentlayout-component contentlayout-placeholder');
             }).always(function() {
                 if ($helper !== null) {
                     $helper.remove();
                 };
             }).pipe(view.editor.add, function() {
                 return $.Deferred().reject();
             })
             : $.Deferred().reject().always(function() {
                 if ($helper !== null) {
                     $helper.remove();
                 };
             })
            ).pipe(function (data) {
                if (data.block_id) {
                    block.block_set(data);
                    return data;
                };
                return $.Deferred().reject();
            }, function() {
                return $.Deferred().reject();
            }).always(function() {
                block.placeholder.clear();
            }).fail(function() {
                if (slot !== null) {
                    slot.remove(block);
                };
                block.destroy();
            }).always(function() {
                if (slot !== null) {
                    slot.$slot.removeClass('contentlayout-over-slot');
                };
                view.slots.update();
                view.slots.events.restore(event);
                view.$body.css('cursor', 'inherit');
                $component.removeClass('selected');
                deferred.resolve();
            });
        };

        var reorder = function(info) {
            var index = 0;
            var position = {$container: info.slot.$slot, $item: []};
            var first = slot === null;

            if (info.current.$block !== undefined) {
                position.$item = info.current.$block;
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
                if (!first) {
                    slot.remove(block);
                    slot.$slot.removeClass('contentlayout-over-slot');
                };
                slot = info.slot;
                slot.add(block, index);
                if (first) {
                    $placeholder.html($component.children().clone());
                    block.placehold($placeholder, '1em', '8em', false);
                };
                block.deplace(position, slot.horizontal);
                view.slots.update();
                $placeholder.attr('class', 'contentlayout-component contentlayout-placeholder');
                slot.$slot.addClass('contentlayout-over-slot');
                validator = view.editor.addable({
                    slot: slot,
                    block: block,
                    name: $component.data('block-name'),
                    index: index
                }).pipe(function(data) {
                    var result = $.Deferred();

                    if (data.success) {
                        $placeholder.attr('class', 'contentlayout-component contentlayout-valid-placeholder');
                        result.resolve(data);
                    } else {
                        $placeholder.attr('class', 'contentlayout-component contentlayout-invalid-placeholder');
                        result.reject(data);
                    };
                    return result;
                }, function(data) {
                    finish(true);
                });

            };
        };

        var bootstrap = function() {
            $component.addClass('selected');
            view.$body.css('cursor', 'move');

            view.slots.events.snapshot();
            view.slots.events.onenter(function(event) {
               reorder(this);
            });
            view.slots.events.onmove(function(event) {
                if ($helper === null) {
                    $helper = $component.clone();
                    $helper.css('position', 'absolute');
                    $helper.css('opacity', '0.6');
                    $helper.zIndex('100000');
                    $helper.offset(this.mouse.offset);
                    view.$body.append($helper);
                } else {
                    $helper.offset(this.mouse.offset);
                };
                if (this.current !== null && this.mouse.changed !== false) {
                    reorder(this);
                };
            });
            view.slots.events.ondrop(save);
            view.slots.events.oncancel(cancel);
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
        var finishing = false;
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
            if (finishing) {
                return $.Deferred();
            };
            finishing = true;
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
                block.placeholder.clear();
            }).fail(function() {
                if (original.slot !== slot ||
                    original.index !== slot.index(block)) {
                    slot.remove(block);
                    original.slot.add(block, original.index);
                };
                block.placeholder.revert();
            }).always(function() {
                $helper.remove();
                slot.$slot.removeClass('contentlayout-over-slot');
                view.slots.update();
                view.slots.events.restore(event);
                view.$body.css('cursor', 'inherit');
                deferred.resolve();
            });
        };

        var reorder = function(info) {
            var index = 0;
            var position = {$container: info.slot.$slot, $item: []};

            if (info.current.$block !== undefined) {
                position.$item = info.current.$block;
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
                slot.$slot.removeClass('contentlayout-over-slot');
                info.slot.add(block, index);
                slot = info.slot;
                slot.$slot.addClass('contentlayout-over-slot');
                block.deplace(position, slot.horizontal);
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
            $helper.css('opacity', '0.6');
            $helper.zIndex('100000');
            $helper.offset(original.mouse);
            view.$body.append($helper);
            view.$body.css('cursor', 'move');
            block.placehold($placeholder);
            slot.$slot.addClass('contentlayout-over-slot');

            view.slots.events.snapshot();
            view.slots.events.onenter(function(event) {
               reorder(this);
            });
            view.slots.events.onmove(function(event) {
                $helper.offset(this.mouse.offset);
                if (this.current !== null && this.mouse.changed !== false) {
                    reorder(this);
                };
            });
            view.slots.events.ondrop(save);
            view.slots.events.oncancel(cancel);
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
        var $actions = $layer.find('#contentlayout-actions');
        var $edit = $actions.find('#contentlayout-edit-block');
        var $cover = $('<div id="contentlayout-cover-layer" />');

        var cover = function() {
            $cover.offset(view.$body.offset());
            $cover.height(view.$body.height());
            $cover.width(view.$body.width());
        };

        var api = {
            resize: function() {
                cover();
                api.update();
                view.slots.update();
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

                if ($block !== undefined){
                    $edit.toggle(other.current.editable);
                    if (selected === null) {
                        $layer.appendTo(view.$body);
                    };
                    selected = other;
                    api.update();
                };
            },
            disable: function() {
                if (selected !== null) {
                    $layer.detach();
                    selected = null;
                };
            }
        };
        // Block mouse move over the actions, that prevent to loose
        // the focus on small items
        $actions.bind('mousemove', function(event) {
            event.stopPropagation();
        });
        // Display and hide layer
        view.slots.events.onenter(function () {
            api.enable(this);
        });
        view.slots.events.onchange(function () {
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
        var delegate = function(mode) {
            if (delegated !== null) {
                delegated.cancel();
            };
            delegated = mode.apply(this, [].splice.call(arguments, 1, 2));
            delegated.promise().always(function() { delegated = null });
        };
        var add = function(event){
            if (selected !== null) {
                api.disable();
            };
            view.slots.drag(event);
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
                view.slots.drag(event);
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
        $components.delegate('div.contentlayout-component', 'mousedown', add);
        $layer.delegate('#contentlayout-edit-block', 'click', edit);
        view.shortcuts.bind('editor', null, ['ctrl+e'], edit);
        $layer.delegate('#contentlayout-move-block', 'mousedown', move);
        view.shortcuts.bind('editor', null, ['ctrl+m'], move);
        $layer.delegate('#contentlayout-remove-block', 'click', remove);
        view.shortcuts.bind('editor', null, ['ctrl+d'], remove);
        $cover.appendTo(view.$body);
        cover();
        return api;
    };

    var Block = function($block) {
        var api = {};
        var position = Element($block);
        $.extend(api, position, {
            id: $block.data('block-id'),
            editable: $block.data('block-editable') === true,
            $block: $block,
            block_set: function(data) {
                this.id = data.block_id,
                this.editable = data.block_editable;
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

        // Find contained blocks, check if the slot is empty.
        $(selector, $slot).each(function () {
            blocks.push(Block($(this)));
        });
        if (!blocks.length) {
            $slot.addClass('contentlayout-empty-slot');
        };

        $.extend(api, position, {
            id: $slot.data('slot-id'),
            $slot: $slot,
            vertical: false,
            update: function() {
                for (var i=0; i < blocks.length; i++) {
                    blocks[i].update();
                };
                position.update();
                api.horizontal = false;

                $.each(blocks, function() {
                    if (!this.placeholder.active()) {
                        api.horizontal = ((/left|right/).test(this.$block.css('float')) ||
                                          (/inline|table-cell/).test(this.$block.css('display')));
                        return false;
                    };
                });
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
                    return this;
                };
                return null;
            },
            get: function(index) {
                return blocks[index];
            },
            index: function(item) {
                return $.inArray(item, blocks);
            },
            add: function(item, index) {
                if (!blocks.length) {
                    $slot.removeClass('contentlayout-empty-slot');
                };
                blocks.splice(index, 0, item);
            },
            remove: function(item) {
                var index = api.index(item);
                var removed = null;

                if (index > -1) {
                    removed = blocks.splice(index, 1)[0];
                };
                if (!blocks.length) {
                    $slot.addClass('contentlayout-empty-slot');
                };
                return removed;
            }
        });
        api.update();
        return api;
    };

    var Mouse = function() {
        var api = {
            top: -1,
            left: -1,
            threshold: 10,
            changed: false,
            offset: {
                top: -1,
                left: -1
            },
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
                this.offset.left = event.pageX + this.threshold;
                this.offset.top = event.pageY + this.threshold;
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

    var Slots = function($document, $slots, selector, $target) {
        var slots = [];
        var dnd = {
            started: false,
            dragued: false,
            captured: false
        };
        var current = null;
        var slot = null;
        var timer = null;
        var mouse = Mouse();
        var events = {
            enter: infrae.deferred.Callbacks(),
            change: infrae.deferred.Callbacks(),
            leave: infrae.deferred.Callbacks(),
            move: infrae.deferred.Callbacks(),
            drop: infrae.deferred.Callbacks(),
            cancel: infrae.deferred.Callbacks()
        };
        var api = {
            events: {
                onenter: function(callback) {
                    events.enter.add(callback);
                },
                onchange: function(callback) {
                    events.change.add(callback);
                },
                onleave: function(callback) {
                    events.leave.add(callback);
                },
                onmove: function(callback) {
                    events.move.add(callback);
                },
                ondrop: function(callback) {
                    events.drop.add(callback);
                },
                oncancel: function(callback) {
                    events.cancel.add(callback);
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
                            events.enter.invoke(SlotEvent(), [event]);
                        };
                    };
                }
            },
            drag: function(event) {
                if (dnd.started) {
                    // We missed mouseup (might have happened outside of the window)
                    events.cancel.invoke(SlotEvent(), [event]);
                };
                mouse.update(event);
                dnd.started = true;
                dnd.dragued = true;
                dnd.captured = false;
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
                            events.enter.invoke(SlotEvent(), [event]);
                        } else {
                            events.change.invoke(SlotEvent(), [event]);
                        };
                        return true;
                    };
                    return false;
                };
            };
            if (current !== null) {
                events.leave.invoke(SlotEvent(), [event]);
                current = null;
                slot = null;
                return true;
            };
            return false;
        };

        $slots.each(function() {
            slots.push(Slot($(this), selector));
        });
        $target.bind('mousedown.contentlayout', function(event) {
            if (dnd.started && !dnd.dragued) {
                // This is a click
                events.drop.invoke(SlotEvent(), [event]);
                dnd.started = false;
                return;
            };
            api.drag(event);
        });
        $target.bind('mouseup.contentlayout', function(event) {
            if (dnd.started) {
                if (dnd.captured) {
                    // This was captured, it is a real DND
                    events.drop.invoke(SlotEvent(), [event]);
                    event.stopPropagation();
                    event.preventDefault();
                    dnd.started = false;
                } else {
                    // This was not captured, we will finish upon a click
                    dnd.dragued = false;
                };
            };
        });
        $target.bind('mousemove.contentlayout', function(event) {
            if (timer !== null) {
                clearTimeout(timer);
            };
            timer = setTimeout(function() {
                if (!mouse.update(event)) {
                    // The mouse didn't move
                    return;
                };
                if (dnd.started && dnd.dragued && !dnd.captured) {
                    // Capture to DND
                    dnd.captured = true;
                };
                if ($document.get(0) === event.delegateTarget && !lookup(event)) {
                    events.move.invoke(SlotEvent(), [event]);
                };
                mouse.finish(event);
                timer = null;
            }, 0);
        });
        return api;
    };

    $(document).bind('load-smiplugins', function(event, smi) {
        var urls = prepare_urls(smi.options.contentlayout);
        var settings = {minWidth: 250, minHeight: 250, position: [30, 'center']};

        infrae.views.view({
            iface: 'content-layout',
            name: 'toolbar',
            factory: function($content, data, smi, view) {
                return {
                    html: '<div class="actions layout-actions"><ol>' +
                        '<li class="last-action"><a class="ui-state-default component-action">' +
                        '<div class="action-icon"><ins class="ui-icon ui-icon-newwin"></ins></div>' +
                        '<span class="have-icon">Components</span></a></li></ol></div>',
                    render: function() {
                        var actions = data.menu.actions;
                        var $component = $content.find('.component-action');
                        var toggle = function(event) {
                            view.components.toggle();
                            event.preventDefault();
                            event.stopPropagation();
                        };

                        $component.bind('click', toggle);
                        view.shortcuts.bind('editor', null, ['ctrl+t'], toggle);
                        if (view.components.opened()) {
                            $component.addClass('active');
                        };
                        view.events.oncomponents(function() {
                            $component.toggleClass('active');
                        });

                        if (actions && actions.entries.length) {
                            var $menu = $('<div class="actions content-actions"><ol></ol></div>');
                            $menu.find('ol').render({data: actions});
                            $content.prepend($menu);
                        };
                        infrae.ui.selection.disable($content);
                    },
                    cleanup: function() {
                        $content.empty();
                        infrae.ui.selection.enable($content);
                    }
                };
            }
        });

        infrae.views.view({
            iface: 'content-layout',
            name: 'content',
            factory: function($content, data, smi) {
                var path = smi.opened.path + (data.identifier ? '/' + data.identifier : '');
                var opened = false;
                var $components = $(data.blocks.available);
                var $listing = $components.children('.contentlayout-components');
                var $layer = $(data.layer);
                var events = {
                    components: infrae.deferred.Callbacks(),
                    viewchange: infrae.deferred.Callbacks()
                };

                return {
                    html_url: urls.url.expand({path: path}),
                    iframe: true,
                    nocache: true,
                    editor: Editor(smi, urls, path),
                    shortcuts: smi.shortcuts,
                    events: {
                        oncomponents: function(callback) {
                            events.components.add(callback);
                        },
                        onviewchange: function(callback) {
                            events.viewchange.add(callback);
                        }
                    },
                    components: {
                        open: function() {
                            if (opened === false) {
                                infrae.ui.ShowDialog($components, settings);
                                opened = true;
                                events.components.invoke({active: true});
                            };
                        },
                        opened: function() {
                            return opened;
                        },
                        close: function() {
                            if (opened === true) {
                                $components.dialog('close');
                            };
                        },
                        toggle: function() {
                            if (opened === false) {
                                this.open();
                            } else {
                                this.close();
                            };
                        }
                    },
                    render: function($content) {
                        this.shortcuts.create('editor', $content, true);

                        this.ready.done(function(view) {
                            view.$body = view.$document.find('body');
                            view.slots = Slots(
                                view.$document,
                                view.$body.find('.contentlayout-edit-slot'),
                                '> .contentlayout-edit-block',
                                $(document).add(view.$document));

                            var mode = NormalMode(view, $layer, $components);
                            var timer = null;

                            // When the iframe is resize, positions need to be updated.
                            view.$window.bind('resize', function() {
                                if (timer !== null) {
                                    clearTimeout(timer);
                                };
                                timer = setTimeout(function() {
                                    mode.resize();
                                    timer = null;
                                }, 50);
                            });
                            // Disable links and selection
                            view.$body.delegate('a', 'click', function (event) {
                                event.preventDefault();
                            });
                            view.$body.disableSelection();
                        });

                        // The purpose of the cover is to prevent the
                        // iframe to catch the movements of the
                        // components dialog.
                        var $cover = $('<div id="smi-cover">');
                        $components.dialog({
                            closeOnEscape: false,
                            autoOpen: false,
                            width: 250,
                            height: 400,
                            open: function() {
                                $listing.accordion({fillSpace: true});
                            },
                            dragStart: function() {
                                $('body').append($cover);
                            },
                            resizeStart: function() {
                                $('body').append($cover);
                            },
                            dragStop: function() {
                                $cover.detach();
                                settings.position = $components.dialog('option', 'position');
                            },
                            resize: function() {
                                $listing.accordion('resize');
                            },
                            resizeStop: function() {
                                $cover.detach();
                            }
                        });
                        $components.bind('infrae-ui-dialog-resized', function() {
                            $listing.accordion('resize');
                        });
                        $components.bind('dialogclose', function() {
                            opened = false;
                            events.components.invoke({active: false});
                        });
                        infrae.ui.selection.disable($components);
                        this.components.open();
                    },
                    cleanup: function() {
                        this.components.close();
                        this.shortcuts.remove('editor');
                        $(document).unbind('.contentlayout');
                        $components.remove();
                        $content.empty();
                    }
                };
            }
        });
    });
})(jQuery, infrae, jsontemplate);


