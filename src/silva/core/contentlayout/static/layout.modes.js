

(function($, infrae, jsontemplate) {

    var AddMode = function(view, $component) {
        var $placeholder = $('<div class="contentlayout-component contentlayout-valid-placeholder"></div>');
        var $helper = null;
        var block = infrae.smi.layout.components.Block();
        var slot = null;
        var validator = null;
        var deferred = $.Deferred();
        var finishing = false;
        var $body = $('body');

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
            $body.css('cursor', 'inherit');

            return (validator !== null && failed !== true
             ?  validator.done(function() {
                 $placeholder.attr('class', 'contentlayout-component contentlayout-placeholder');
             }).always(function() {
                 if ($helper !== null) {
                     $helper.remove();
                 };
             }).pipe(view.transport.add, function() {
                 return $.Deferred().reject();
             })
             : $.Deferred().reject().always(function() {
                 if ($helper !== null) {
                     $helper.remove();
                 };
             })
            ).pipe(function (data) {
                if (data.block_id) {
                    block.set(data);
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
                validator = view.transport.addable({
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
            $body.css('cursor', 'move');
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
        var $placeholder = $('<div class="contentlayout-placeholder"></div>');
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
             }).pipe(view.transport.move, function() {
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

        var validate = function(index) {
            $placeholder.attr('class', 'contentlayout-placeholder');
            validator = view.transport.movable({
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
                validate(index);
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
            validate(0);

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

    var CoverMode = function(view) {
        var api =  {
            $cover: null,
            add: function() {
                this.$cover = $('<div id="contentlayout-cover-layer" />');
                this.$cover.appendTo(view.$body);
                this.update();
            },
            update: function() {
                if (this.$cover !== null) {
                    this.$cover.offset(view.$body.offset());
                    this.$cover.height(view.$body.height());
                    this.$cover.width(view.$body.width());
                };
            },
            destroy: function() {
                this.$cover.remove();
                this.$cover = null;
            }
        };

        api.add();
        // Disable links and selection
        view.$body.delegate('a', 'click', function (event) {
            event.preventDefault();
        });
        view.$body.disableSelection();
        view.events.onresize(function() {
            api.update();
        });
        return api;
    };


    var NormalMode = function(view, $layer, $components) {
        var selected = null,
            delegated = null;
        var $actions = $layer.find('#contentlayout-actions');
        var $edit = $actions.find('#contentlayout-edit-block');

        var api = {
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
                    $edit.toggle(other.slot.editable && other.current.editable);
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
        view.transport.events.onchange(function() {
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
                view.transport.edit(selected);
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
                    title: 'Remove component',
                    message: 'Please confirm the permanent deletion of the component ?'
                }).done(function () {
                    view.transport.remove(selected);
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
        view.events.onresize(function() {
            api.update();
        });
        return api;
    };

    $.extend(infrae.smi.layout, {
        AddMode: AddMode,
        MoveMode: MoveMode,
        NormalMode: NormalMode,
        CoverMode: CoverMode
    });

})(jQuery, infrae, jsontemplate);
