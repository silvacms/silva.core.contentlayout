

(function($, infrae, jsontemplate) {

    var AddMode = function($component) {
        var view = this;
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
             }).then(view.transport.add, function() {
                 return $.Deferred().reject();
             })
             : $.Deferred().reject().always(function() {
                 if ($helper !== null) {
                     $helper.remove();
                 };
             })
            ).then(function (data) {
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
                }).then(function(data) {
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
            type: 'add',
            cancel: cancel,
            save: save,
            promise: deferred.promise
        };
    };

    var RemoveMode = function(original) {
        var view = this;

        var deferred = infrae.ui.ConfirmationDialog({
            title: 'Remove component',
            message: 'Please confirm the permanent deletion of the component ?'
        }).then(function () {
            return view.transport.remove(original);
        }, function () {
            return $.Deferred().reject();
        });

        return {
            type: 'remove',
            cancel: function() {},
            save: function() {},
            promise: deferred.promise
        };
    };

    var RemoveAllMode = function(original) {
        var view = this;

        var deferred = infrae.ui.ConfirmationDialog({
            title: 'Remove all components',
            message: 'Please confirm the permanent deletion of all selected components ?'});

        infrae.utils.each(original, function(original) {
            deferred = deferred.then(function() {
                return view.transport.remove(original);
            }, function() {
                return $.Deferred().reject();
            });
        });

        return {
            type: 'remove',
            cancel: function() {},
            save: function() {},
            promise: deferred.promise
        };
    };

    var MoveMode = function(original) {
        var view = this;
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
             }).then(view.transport.move, function() {
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
            }).then(function(data) {
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
            type: 'move',
            cancel: cancel,
            save: save,
            promise: deferred.promise
        };
    };

    $.extend(infrae.smi.layout, {
        AddMode: AddMode,
        RemoveMode: RemoveMode,
        RemoveAllMode: RemoveAllMode,
        MoveMode: MoveMode
    });

})(jQuery, infrae, jsontemplate);
