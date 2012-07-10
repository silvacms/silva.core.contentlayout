

(function($, infrae, jsontemplate) {

    var CoverFeature = function(view) {
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
                    this.$cover.height(view.$body.outerHeight());
                    this.$cover.width(view.$body.outerWidth());
                };
            },
            destroy: function() {
                this.$cover.remove();
                this.$cover = null;
            }
        };

        var cover = function(selected) {
            if (selected !== undefined) {
                if (selected.current) {
                    api.$cover.zIndex(selected.current.zIndex + 5);
                } else {
                    api.$cover.zIndex(selected.slot.zIndex + 5);
                };
            } else {
                api.$cover.zIndex(5);
            }
        };

        api.add();
        // Disable links and selection
        view.$body.delegate('a', 'click', function (event) {
            event.preventDefault();
        });
        view.$body.disableSelection();
        view.slots.events.onenter(function() {
            cover(this);
        });
        view.slots.events.onchange(function() {
            cover(this);
        });
        view.slots.events.onleave(function() {
            cover();
        });
        view.events.onresize(function() {
            api.update();
        });
        return api;
    };

    var EditorFeature = function(view, $layer, $components) {
        var selected = null;
        var $actions = $layer.find('.contentlayout-actions');
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
                    $layer.zIndex(other.current.zIndex + 10);
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
        var add = function(event){
            if (selected !== null) {
                api.disable();
            };
            view.slots.drag(event);
            view.mode(infrae.smi.layout.AddMode, $(this));
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
                view.mode(infrae.smi.layout.MoveMode, selected);
                api.disable();
            };
            event.stopPropagation();
            event.preventDefault();
        };
        var remove = function(event) {
            if (selected !== null && selected.current.$block !== undefined) {
                view.mode(infrae.smi.layout.RemoveMode, selected);
                api.disable();
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

    var LostFeature = function(view, template, data) {
        var $lost = null,
            $slots = null,
            slots = [];

        var add = function(slot) {
            // Add a new slot the to the $lost component.
            if ($lost === null) {
                $lost = $(template);
                $lost.find('#contentlayout-remove-all-blocks').bind('click', function(event) {
                    var selected = [];

                    infrae.utils.each(slots, function(slot) {
                        for (var index=slot.size(); index--;) {
                            selected.push({
                                slot: slot,
                                current: slot.get(index)});
                        };
                    });
                    view.mode(infrae.smi.layout.RemoveAllMode, selected);
                    event.preventDefault();
                    event.stopPropagation();
                });
                $slots = $lost.children('#contentlayout-lost-blocks');
                view.$body.append($lost);
                place();
            };
            $slots.append(slot.$slot);
            slot.update();
            slots.push(slot);
            view.slots.add(slot);
        };
        var place = function() {
            // Place the $lost component on the page.
            if ($lost !== null) {
                var available_width = view.$body.width();
                var current_width = $lost.width();
                var new_width = Math.min(500, available_width - 300);

                if (new_width != current_width) {
                    $lost.width(new_width);
                };
                $lost.offset({
                    top: 100,
                    left: (available_width - new_width) / 2});
            };
        };
        var clean = function() {
            // Clean if need the $lost component from the page.
            if ($lost !== null) {
                // We iterate in reverse to remove items when needed.
                var index = slots.length;

                while (index--) {
                    if (!slots[index].size()) {
                        slots[index].destroy();
                        slots.splice(index, 1);
                    };
                };
                if (!slots.length) {
                    $lost.remove();
                    $lost = null;
                    $slots = null;
                };
            };
        };

        for (var name in data) {
            var slot = infrae.smi.layout.components.Slot(),
                block,
                lost = data[name],
                index = 0;

            slot.set({slot_id: name});
            for (; index < lost.length; index++) {
                block = infrae.smi.layout.components.Block();
                block.set(lost[index]);
                slot.$slot.append(block.$block);
                slot.add(block);
            };
            if (index) {
                add(slot);
            };
        };
        view.events.onmodestart(function() {
            if ($lost !== null) {
                $lost.fadeOut();
                $lost.promise().done(function() {
                    view.slots.update();
                });
            };
        });
        view.events.onmodestop(function() {
            clean();
            if ($lost !== null) {
                $lost.fadeIn();
                $lost.promise().done(function() {
                    view.slots.update();
                });
            };
        });
        view.events.onresize(function() {
            place();
        });
    };

    $.extend(infrae.smi.layout, {
        EditorFeature: EditorFeature,
        CoverFeature: CoverFeature,
        LostFeature: LostFeature
    });



})(jQuery, infrae, jsontemplate);
