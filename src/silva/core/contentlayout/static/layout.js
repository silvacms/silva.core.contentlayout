

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

    var Slots = function($document, $slots, selector, $target) {
        var current = null,
            slot = null,
            slots = [],
            timer = null,
            mouse = infrae.smi.layout.utils.Mouse();
        var dnd = {
            started: false,
            dragued: false,
            captured: false
        };
        var events = {
            enter: infrae.deferred.Callbacks(),
            change: infrae.deferred.Callbacks(),
            leave: infrae.deferred.Callbacks(),
            move: infrae.deferred.Callbacks(),
            drop: infrae.deferred.Callbacks(),
            cancel: infrae.deferred.Callbacks()
        };
        var sort = function() {
          slots.sort(function (a, b) {
              return b.zIndex - a.zIndex;
          });
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
            add: function(slot) {
                slots.push(slot);
                sort();
            },
            size: function() {
                return slots.length;
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
            },
            remove: function(slot) {
                var index = $.inArray(slot, slots);
                var removed = null;

                if (index > -1) {
                    removed = slots.splice(index, 1)[0];
                };
                return removed;
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
            slots.push(infrae.smi.layout.components.Slot($(this), selector));
        });
        sort();
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
                            $content.append($menu);
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
                var $components = $(data.templates.components);
                var $listing = $components.children('.contentlayout-components');
                var $layer = $(data.templates.layer);
                var active = null,
                    stopping = false;
                var events = {
                    resize: infrae.deferred.Callbacks(),
                    components: infrae.deferred.Callbacks(),
                    modestart: infrae.deferred.Callbacks(),
                    modestop: infrae.deferred.Callbacks()
                };

                return {
                    html_url: urls.url.expand({path: path}),
                    iframe: true,
                    template_nocache: true,
                    transport: infrae.smi.layout.utils.Transport(smi, urls, path),
                    shortcuts: smi.shortcuts,
                    events: {
                        oncomponents: function(callback) {
                            events.components.add(callback);
                        },
                        onresize: function(callback) {
                            events.resize.add(callback);
                        },
                        onmodestart: function(callback) {
                            events.modestart.add(callback);
                        },
                        onmodestop: function(callback) {
                            events.modestop.add(callback);
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
                    mode: function(mode) {
                        if (!stopping) {
                            var context = this,
                                options = [].splice.call(arguments, 1, 2);

                            var start = function() {
                                active = mode.apply(context, options);
                                active.promise().always(function() {
                                    events.modestop.invoke(active);
                                    active = null;
                                    stopping = false;
                                });
                                events.modestart.invoke(active);
                            };

                            if (active !== null) {
                                stopping = true;
                                active.cancel();
                                active.promise().always(start);
                            } else {
                                start();
                            };
                        };
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

                            // The order in which the features are initialized is imported
                            // (because of the order in which the resize event is called).
                            infrae.smi.layout.CoverFeature(view);
                            infrae.smi.layout.EditorFeature(view, $layer, $components);
                            view.events.onresize(function () {
                                view.slots.update();
                            });
                            infrae.smi.layout.LostFeature(view, data.templates.missing, data.missing);

                            // When the iframe is resize, positions need to be updated.
                            var timer = null;
                            view.$window.bind('resize', function() {
                                if (timer !== null) {
                                    clearTimeout(timer);
                                };
                                timer = setTimeout(function() {
                                    events.resize.invoke(view);
                                    timer = null;
                                }, 50);
                            });

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

    infrae.smi.layout = {};

})(jQuery, infrae, jsontemplate);


