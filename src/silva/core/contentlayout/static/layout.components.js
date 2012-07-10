
(function($, infrae, jsontemplate) {

    var readZIndex = function($element) {
        // Copy and fix jquery.ui broken zIndex function.
		var position, value;
		while ($element.length && $element[0].ownerDocument !== null) {
			position = $element.css("position");
			if (position === "absolute" || position === "relative" || position === "fixed") {
				value = parseInt($element.css("zIndex"), 10);
				if (!isNaN(value) && value !== 0) {
					return value;
				};
			};
			$element = $element.parent();
		};
        return 0;
    };

    // Base object representing a block or a slot.
    var Element = function($element) {
        var $current = $element;
        var placeholding = null;
        var api = {
            zIndex: 0,
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
                this.zIndex = api.zIndex = readZIndex($current);
            }
        };
        return api;
    };

    // Object used to represent a block.
    var Block = function($block) {
        var api = {},
            element;

        if ($block === undefined) {
            $block = $('<div class="contentlayout-edit-block" />');
        };
        element = Element($block);

        $.extend(api, element, {
            id: $block.data('block-id'),
            editable: $block.data('block-editable') === true,
            $block: $block,
            set: function(data) {
                this.id = data.block_id,
                this.editable = data.block_editable;
                this.$block.attr('data-block-id', data.block_id);
                this.$block.html(data.block_data);
                if (data.block_editable) {
                    this.$block.attr('data-block-editable', 'true');
                } else {
                    this.$block.removeAttr('data-block-editable');
                }
            }
        });
        return api;
    };

    // Object used to represent a slot
    var Slot = function($slot, selector) {
        var api = {},
            blocks = [],
            element,
            zIndex = 0,
            editable = true;

        if ($slot !== undefined) {
            // Find contained blocks, check if the slot is empty.
            if (selector !== undefined) {
                $(selector, $slot).each(function () {
                    blocks.push(Block($(this)));
                });
            };
        } else {
            $slot = $('<div class="contentlayout-edit-slot"></div>');
            editable = false;
            zIndex = 99;
        };

        if (!blocks.length && editable) {
            $slot.addClass('contentlayout-empty-slot');
        };
        element = Element($slot);

        $.extend(api, element, {
            id: $slot.data('slot-id'),
            $slot: $slot,
            zIndex: zIndex,
            editable: editable,
            horizontal: false,
            update: function() {
                for (var i=0; i < blocks.length; i++) {
                    blocks[i].update();
                };
                element.update();
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
                var current_slot = element.over(event);
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
            set: function(data) {
                this.id = data.slot_id;
                this.$slot.attr('data-slot-id', data.slot_id);
            },
            get: function(index) {
                return blocks[index];
            },
            index: function(item) {
                return $.inArray(item, blocks);
            },
            size: function() {
                return blocks.length;
            },
            add: function(item, index) {
                if (!blocks.length) {
                    $slot.removeClass('contentlayout-empty-slot');
                };
                if (index !== undefined) {
                    blocks.splice(index, 0, item);
                } else {
                    blocks.push(item);
                };
            },
            remove: function(item) {
                var index = api.index(item);
                var removed = null;

                if (index > -1) {
                    removed = blocks.splice(index, 1)[0];
                };
                if (!blocks.length && this.editable) {
                    $slot.addClass('contentlayout-empty-slot');
                };
                return removed;
            }
        });
        api.update();
        return api;
    };

    $.extend(infrae.smi.layout, {
        components: {
            Element: Element,
            Block: Block,
            Slot: Slot
        }
    });

})(jQuery, infrae, jsontemplate);
