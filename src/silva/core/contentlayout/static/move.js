/*!
 * jQuery UI Mouse 1.8.18
 *
 * Copyright 2011, AUTHORS.txt (http://jqueryui.com/about)
 * Dual licensed under the MIT or GPL Version 2 licenses.
 * http://jquery.org/license
 *
 * http://docs.jquery.com/UI/Mouse
 *
 * Depends:
 *	jquery.ui.widget.js
 */
(function( $, undefined ) {

    var mouseHandled = false;

    var css_size = function(element, property) {
        return parseInt(element.css(property), 10) || 0;
    };

$.widget("infrae.blockable", {
    widgetEventPrefix: "block",
	ready: false,
	options: {
        mouseSource: $(document),
        mouseCapture: true,
		appendTo: "parent",
		axis: false,
		connectWith: false,
		containment: false,
		cursor: 'auto',
		cursorAt: false,
		dropOnEmpty: true,
		forcePlaceholderSize: false,
		forceHelperSize: false,
		grid: false,
		handle: false,
		helper: "original",
		items: '> *',
		opacity: false,
		placeholder: false,
		revert: false,
		scroll: true,
		scrollSensitivity: 20,
		scrollSpeed: 20,
		scope: "default",
		tolerance: "intersect",
		zIndex: 1000,
		cancel: ':input,option',
		distance: 1,
		delay: 0
	},
	_mouseInit: function() {
		var self = this;

        this.options.mouseSource.mouseup(function(event) {
	        mouseHandled = false;
        });

		this.element
			.bind('mousedown.' + this.widgetName, function(event) {
				return self._mouseDown(event);
			})
			.bind('click.' + this.widgetName, function(event) {
				if (true === $.data(event.target, self.widgetName + '.preventClickEvent')) {
				    $.removeData(event.target, self.widgetName + '.preventClickEvent');
					event.stopImmediatePropagation();
					return false;
				}
			});

		this.started = false;
	},

	// TODO: make sure destroying one instance of mouse doesn't mess with
	// other instances of mouse
	_mouseDestroy: function() {
		this.element.unbind('.' + this.widgetName);
	},

	_mouseDown: function(event) {
		// don't let more than one widget handle mouseStart
		if(mouseHandled) {
            return;
        };

		// we may have missed mouseup (out of window)
		(this._mouseStarted && this._mouseUp(event));

		this._mouseDownEvent = event;

		var btnIsLeft = (event.which == 1),
			// event.target.nodeName works around a bug in IE 8 with
			// disabled inputs (#7620)
			elIsCancel = (typeof this.options.cancel == "string" && event.target.nodeName ? $(event.target).closest(this.options.cancel).length : false);
		if (!btnIsLeft || elIsCancel || !this._mouseCapture(event)) {
			return true;
		}

        this._mouseStartMoving(event, event.target);

		event.preventDefault();

		return true;
	},

    _mouseStartMoving: function(event, element) {
        var self = this;

        if(mouseHandled) {
            return;
        };

        this._mouseDownEvent = event;

		this.mouseDelayMet = !this.options.delay;
		if (!this.mouseDelayMet) {
			this._mouseDelayTimer = setTimeout(function() {
				self.mouseDelayMet = true;
			}, this.options.delay);
		}

		if (this._mouseDistanceMet(event) && this._mouseDelayMet(event)) {
			this._mouseStarted = (this._mouseStart(event) !== false);
			if (!this._mouseStarted) {
                return;
			}
		}

		// Click event may never have fired (Gecko & Opera)
		if (true === $.data(element, this.widgetName + '.preventClickEvent')) {
			$.removeData(element, this.widgetName + '.preventClickEvent');
		}

		// these delegates are required to keep context
		this._mouseMoveDelegate = function(event) {
			return self._mouseMove(event);
		};
		this._mouseUpDelegate = function(event) {
			return self._mouseUp(event);
		};

		this.options.mouseSource
			.bind('mousemove.' + this.widgetName, this._mouseMoveDelegate)
			.bind('mouseup.' + this.widgetName, this._mouseUpDelegate);

		mouseHandled = true;
    },

	_mouseMove: function(event) {
		// IE mouseup check - mouseup happened when mouse was out of window
		if ($.browser.msie && !(document.documentMode >= 9) && !event.button) {
			return this._mouseUp(event);
		}

		if (this._mouseStarted) {
			this._mouseDrag(event);
			return event.preventDefault();
		}

		if (this._mouseDistanceMet(event) && this._mouseDelayMet(event)) {
			this._mouseStarted =
				(this._mouseStart(this._mouseDownEvent, event) !== false);
			(this._mouseStarted ? this._mouseDrag(event) : this._mouseUp(event));
		}

		return !this._mouseStarted;
	},

	_mouseUp: function(event) {
		this.options.mouseSource
			.unbind('mousemove.' + this.widgetName, this._mouseMoveDelegate)
			.unbind('mouseup.' + this.widgetName, this._mouseUpDelegate);

		if (this._mouseStarted) {
			this._mouseStarted = false;

			if (event.target == this._mouseDownEvent.target) {
			    $.data(event.target, this.widgetName + '.preventClickEvent', true);
			};

			this._mouseStop(event);
		};

		return false;
	},

	_mouseDistanceMet: function(event) {
		return (Math.max(
				Math.abs(this._mouseDownEvent.pageX - event.pageX),
				Math.abs(this._mouseDownEvent.pageY - event.pageY)
			) >= this.options.distance
		);
	},

	_mouseDelayMet: function(event) {
		return this.mouseDelayMet;
	},

	_create: function() {
		var o = this.options;
        this.currentItem = undefined;
        this.currentContainer = undefined;
		this.containerCache = {};
		this.element.addClass("ui-sortable");
        this.deferred = undefined;
        this.floating = this.options.axis === 'x';  // Define if matching should be horizontal or vertical.

		//Let's determine the parent's offset
		this.offset = this.element.offset();

		//Initialize mouse events for interaction
		this._mouseInit();

		//We're ready to go
		this.ready = true;

	},

	destroy: function() {
		$.Widget.prototype.destroy.call(this);
		this.element
			.removeClass("ui-sortable ui-sortable-disabled");
		this._mouseDestroy();
		return this;
	},

	_setOption: function(key, value){
		if ( key === "disabled" ) {
			this.options[ key ] = value;

			this.widget()
				[ value ? "addClass" : "removeClass"]( "ui-sortable-disabled" );
		} else {
			// Don't call widget base _setOption for disable as it adds ui-state-disabled class
			$.Widget.prototype._setOption.apply(this, arguments);
		}
	},

    capture: function(event, element) {
        // Alternate start point.
        // Find current items and other containers.
        this.findAll(event);
        this._setCurrentItem(element[0]);
        this._mouseStartMoving(event, element);
    },

	_mouseCapture: function(event, overrideHandle) {
		var that = this;

		if (this.options.disabled || this.options.type == 'static' || !this.options.mouseCapture) {
            return false;
        };

        // Find current items and other containers.
        this.findAll(event);

        // XXX This is broken, we have to update to use the :data hack here.
		//Find out if the clicked node (or one of its parents) is a actual item in this.items
		var currentItem = null, nodes = $(event.target).parents().each(function() {
			if($.data(this, that.widgetName + '-item') == that) {
				currentItem = $(this);
				return false;
			}
		});
		if($.data(event.target, that.widgetName + '-item') == that) {
            currentItem = event.target;
        }

		if(!currentItem) {
            return false;
        }
		if(this.options.handle && !overrideHandle) {
			var validHandle = false;

			$(this.options.handle, currentItem).find("*").andSelf().each(function() {
                if(this == event.target)
                    validHandle = true;
            });
			if(!validHandle)
                return false;
		}

        this._setCurrentItem(currentItem);
		return true;

	},

	_mouseStart: function(event, overrideHandle, noActivation) {
		var o = this.options, self = this;
		this.currentContainer = this;
        this.deferred = null;

		// We only need to refresh all blocks positions.
		this.refreshAllPositions(true);

		//Create and append the visible helper
		this.helper = this._createHelper(event);

		//Cache the helper size
		this._cacheHelperProportions();

		/*
		 * - Position generation -
		 * This block generates everything position related - it's the core of draggables.
		 */

		//Cache the margins of the original element
		this._cacheMargins();

		//Get the next scrolling parent
		this.scrollParent = this.helper.scrollParent();

		//The element's absolute position on the page minus margins
		this.offset = this.currentItem.offset();
		this.offset = {
			top: this.offset.top - this.margins.top,
			left: this.offset.left - this.margins.left
		};

		// Only after we got the offset, we can change the helper's position to absolute
		// TODO: Still need to figure out a way to make relative sorting possible
		this.helper.css("position", "absolute");
		this.cssPosition = this.helper.css("position");

		$.extend(this.offset, {
			click: { //Where the click happened, relative to the element
				left: event.pageX - this.offset.left,
				top: event.pageY - this.offset.top
			},
			parent: this._getParentOffset(),
			relative: this._getRelativeOffset() //This is a relative to absolute position minus the actual position calculation - only used for relative positioned helper
		});

		//Generate the original position
		this.originalPosition = this._generatePosition(event);
		this.originalPageX = event.pageX;
		this.originalPageY = event.pageY;

		//Adjust the mouse offset relative to the helper if 'cursorAt' is supplied
		(o.cursorAt && this._adjustOffsetFromHelper(o.cursorAt));

		//Cache the former DOM position
		this.domPosition = { prev: this.currentItem.prev()[0], parent: this.currentItem.parent()[0] };

		//If the helper is not the original, hide the original so it's not playing any role during the drag, won't cause anything bad this way
		if(this.helper[0] != this.currentItem[0]) {
			this.currentItem.hide();
		}

		//Create the placeholder
		this._createPlaceholder();

		//Set a containment if given in the options
		if(o.containment)
			this._setContainment();

		if(o.cursor) { // cursor option
			if ($('body').css("cursor")) this._storedCursor = $('body').css("cursor");
			$('body').css("cursor", o.cursor);
		}

		if(o.opacity) { // opacity option
			if (this.helper.css("opacity")) this._storedOpacity = this.helper.css("opacity");
			this.helper.css("opacity", o.opacity);
		}

		if(o.zIndex) { // zIndex option
			if (this.helper.css("zIndex")) this._storedZIndex = this.helper.css("zIndex");
			this.helper.css("zIndex", o.zIndex);
		}

		// Prepare scrolling
		if(this.scrollParent[0] != document && this.scrollParent[0].tagName != 'HTML')
			this.overflowOffset = this.scrollParent.offset();

		// Call callbacks
		this._trigger("start", event, this._eventInfo());

		// Recache the helper size
		if(!this._preserveHelperProportions)
			this._cacheHelperProportions();

		this.dragging = true;

		this.helper.addClass("ui-sortable-helper");
		this._mouseDrag(event); //Execute the drag once - this causes the helper not to be visible before getting its correct position
		return true;

	},

	_mouseDrag: function(event) {
		// Compute the helpers position
		this.position = this._generatePosition(event);
		this.positionAbs = this._convertPositionTo("absolute");

		if (!this.lastPositionAbs) {
			this.lastPositionAbs = this.positionAbs;
		}

		// Do scrolling
		if(this.options.scroll) {
			var o = this.options, scrolled = false;
			if(this.scrollParent[0] != document && this.scrollParent[0].tagName != 'HTML') {

				if((this.overflowOffset.top + this.scrollParent[0].offsetHeight) - event.pageY < o.scrollSensitivity)
					this.scrollParent[0].scrollTop = scrolled = this.scrollParent[0].scrollTop + o.scrollSpeed;
				else if(event.pageY - this.overflowOffset.top < o.scrollSensitivity)
					this.scrollParent[0].scrollTop = scrolled = this.scrollParent[0].scrollTop - o.scrollSpeed;

				if((this.overflowOffset.left + this.scrollParent[0].offsetWidth) - event.pageX < o.scrollSensitivity)
					this.scrollParent[0].scrollLeft = scrolled = this.scrollParent[0].scrollLeft + o.scrollSpeed;
				else if(event.pageX - this.overflowOffset.left < o.scrollSensitivity)
					this.scrollParent[0].scrollLeft = scrolled = this.scrollParent[0].scrollLeft - o.scrollSpeed;

			} else {

				if(event.pageY - $(document).scrollTop() < o.scrollSensitivity)
					scrolled = $(document).scrollTop($(document).scrollTop() - o.scrollSpeed);
				else if($(window).height() - (event.pageY - $(document).scrollTop()) < o.scrollSensitivity)
					scrolled = $(document).scrollTop($(document).scrollTop() + o.scrollSpeed);

				if(event.pageX - $(document).scrollLeft() < o.scrollSensitivity)
					scrolled = $(document).scrollLeft($(document).scrollLeft() - o.scrollSpeed);
				else if($(window).width() - (event.pageX - $(document).scrollLeft()) < o.scrollSensitivity)
					scrolled = $(document).scrollLeft($(document).scrollLeft() + o.scrollSpeed);

			}
		}

		// Regenerate the absolute position used for position checks
		this.positionAbs = this._convertPositionTo("absolute");

		// Set the helper position
		if(!this.options.axis || this.options.axis != "y")
            this.helper[0].style.left = this.position.left+'px';
		if(!this.options.axis || this.options.axis != "x")
            this.helper[0].style.top = this.position.top+'px';

		// Update the new order.
		this._updateItemOrder(event);

		this.lastPositionAbs = this.positionAbs;
		return false;

	},

	_mouseStop: function(event) {
		if(!event)
            return;
        var promise = this.deferred ? this.deferred : $.Deferred().resolve();
		var self = this;

        promise.pipe(function() {
            self._finish(event);
        }, function() {
            return {};
        }).done(function() {
           	self._clear(event);
        });
		return false;
	},

	cancel: function() {
		var self = this;

		if(this.dragging) {
			this._mouseUp({target: null});

			if(this.options.helper == "original")
				this.currentItem.css(this._storedCSS).removeClass("ui-sortable-helper");
			else
				this.currentItem.show();
		};

		if (this.placeholder) {
			if(this.placeholder[0].parentNode)
                this.placeholder[0].parentNode.removeChild(this.placeholder[0]);
			if(this.options.helper != "original" && this.helper && this.helper[0].parentNode)
                this.helper.remove();

			$.extend(this, {
				helper: null,
				dragging: false,
				reverting: false,
				_noFinalSort: null
			});

			if(this.domPosition.prev) {
				$(this.domPosition.prev).after(this.currentItem);
			} else {
				$(this.domPosition.parent).prepend(this.currentItem);
			}
		}

		return this;

	},

	/* Be careful with the following core functions */
	_intersectsWith: function(item) {

		var x1 = this.positionAbs.left,
			x2 = x1 + this.helperProportions.width,
			y1 = this.positionAbs.top,
			y2 = y1 + this.helperProportions.height;

		var l = item.left,
			r = l + item.width,
			t = item.top,
			b = t + item.height;

		var dyClick = this.offset.click.top,
			dxClick = this.offset.click.left;

		var isOverElement = (y1 + dyClick) > t && (y1 + dyClick) < b && (x1 + dxClick) > l && (x1 + dxClick) < r;

		if(	   this.options.tolerance == "pointer"
			|| this.options.forcePointerForContainers
			|| (this.options.tolerance != "pointer" && this.helperProportions[this.floating ? 'width' : 'height'] > item[this.floating ? 'width' : 'height'])
		) {
			return isOverElement;
		} else {

			return (l < x1 + (this.helperProportions.width / 2) // Right Half
				&& x2 - (this.helperProportions.width / 2) < r // Left Half
				&& t < y1 + (this.helperProportions.height / 2) // Bottom Half
				&& y2 - (this.helperProportions.height / 2) < b ); // Top Half

		}
	},

	_intersectsWithPointer: function(item) {
		var isOverElementHeight = $.ui.isOverAxis(this.positionAbs.top + this.offset.click.top, item.top, item.height),
			isOverElementWidth = $.ui.isOverAxis(this.positionAbs.left + this.offset.click.left, item.left, item.width),
			isOverElement = isOverElementHeight && isOverElementWidth,
			verticalDirection = this._getDragVerticalDirection(),
			horizontalDirection = this._getDragHorizontalDirection();

		if (!isOverElement)
			return false;

		return this.floating ?
			( ((horizontalDirection && horizontalDirection == "right") || verticalDirection == "down") ? 2 : 1 )
			: ( verticalDirection && (verticalDirection == "down" ? 2 : 1) );

	},

	_intersectsWithSides: function(item) {

		var isOverBottomHalf = $.ui.isOverAxis(this.positionAbs.top + this.offset.click.top, item.top + (item.height/2), item.height),
			isOverRightHalf = $.ui.isOverAxis(this.positionAbs.left + this.offset.click.left, item.left + (item.width/2), item.width),
			verticalDirection = this._getDragVerticalDirection(),
			horizontalDirection = this._getDragHorizontalDirection();

		if (this.floating && horizontalDirection) {
			return ((horizontalDirection == "right" && isOverRightHalf) || (horizontalDirection == "left" && !isOverRightHalf));
		} else {
			return verticalDirection && ((verticalDirection == "down" && isOverBottomHalf) || (verticalDirection == "up" && !isOverBottomHalf));
		}

	},

	_getDragVerticalDirection: function() {
		var delta = this.positionAbs.top - this.lastPositionAbs.top;
		return delta != 0 && (delta > 0 ? "down" : "up");
	},

	_getDragHorizontalDirection: function() {
		var delta = this.positionAbs.left - this.lastPositionAbs.left;
		return delta != 0 && (delta > 0 ? "right" : "left");
	},

    // find associated containers and items.

	findAll: function(event) {
		this.findItems(event);
        this.findContainers(event);
		return this;
	},

	findContainers: function(event) {
        this.containers = [this];

        if (this.ready) {
            var names = this.options.connectWith.constructor == String
                    ? [this.options.connectWith]
                    : this.options.connectWith;

            for (var i = names.length - 1; i >= 0; i--) {
			    var $element = $(names[i]);
			    for (var j = $element.length - 1; j >= 0; j--) {
				    var container = $.data($element[j], this.widgetName);
                    if (container !== this && !container.options.disabled) {
                        this.containers.push(container);
                    };
                };
            };
        };
	},

	findItems: function(event) {
        var raw_items = [];
		var items = this.items = [];

        if ($.isFunction(this.options.items)) {
            raw_items = this.options.items.call(this.element[0], event, {item: this.currentItem});
        } else {
            raw_items = $(this.options.items, this.element);
        };

        raw_items.each(function () {
            var $item = $(this);
            items.push({
				item: $item,
				width: 0,
                height: 0,
				left: 0,
                top: 0,
                is: function(other) {
                    if (other !== undefined) {
                        return $item == other;
                    };
                    return false;
                },
                is_contained: function(other) {
                    return $.ui.contains(other[0], $item[0]);
                }

			});
        });

        // Let's determine if the items are being displayed horizontally
		this.floating = this.items.length
            ? this.options.axis === 'x' || (/left|right/).test(this.items[0].item.css('float')) || (/inline|table-cell/).test(this.items[0].item.css('display'))
            : false;
	},

    refreshAllPositions: function(hard_refresh) {
		// This has to be redone because due to the item being moved
		// out/into the offsetParent, the offsetParent's position will
		// change
		if(this.offsetParent && this.helper) {
			this.offset.parent = this._getParentOffset();
		};
        for (var i=0; i < this.containers.length; i++) {
            if (hard_refresh && this != this.containers[i]) {
                this.containers[i].findItems();
            };
            this.containers[i].refreshPositions(hard_refresh);
        };
    },

	refreshPositions: function(hard_refresh) {
        for (var i = this.items.length - 1; i >= 0; i--){
			var item = this.items[i];

			// We ignore calculating positions of all connected containers when we're not over them
			if(item.is(this.currentItem)) {
                continue;
            }

            var t = this.options.toleranceElement ? $(this.options.toleranceElement, item.item) : item.item;
            var p = t.offset();

			item.left = p.left;
			item.top = p.top;
            if (hard_refresh) {
                item.width = t.outerWidth();
			    item.height = t.outerHeight();
            };
		};

		var p = this.element.offset();
		this.containerCache.left = p.left;
		this.containerCache.top = p.top;
		this.containerCache.width = this.element.outerWidth();
		this.containerCache.height = this.element.outerHeight();
		return this;
	},

    // Set current item remove the item from the list of available ones.
    _setCurrentItem: function(element) {
        this.currentItem = null;
		for (var i=0; i < this.items.length; i++) {
			if(this.items[i].item[0] == element) {
                this.currentItem = this.items[i].item;
                this.items.splice(i,1);
                break;
			};
		};
	},

    // End of refresh and find items/containers buisness.

	_createPlaceholder: function(that) {
		var self = that || this, o = self.options;

		if(!o.placeholder || o.placeholder.constructor == String) {
			var className = o.placeholder;
			o.placeholder = {
				element: function() {

					var el = $(document.createElement(self.currentItem[0].nodeName))
						.addClass(className || self.currentItem[0].className+" ui-sortable-placeholder")
						.removeClass("ui-sortable-helper")[0];

					if(!className)
						el.style.visibility = "hidden";

					return el;
				},
				update: function(container, p) {

					// 1. If a className is set as 'placeholder
					// option, we don't force sizes - the class is
					// responsible for that

					// 2. The option 'forcePlaceholderSize can be
					// enabled to force it even if a class name is
					// specified

					if(className && !o.forcePlaceholderSize)
                        return;
					// If the element doesn't have a actual height by
					// itself (without styles coming from a stylesheet),
					// it receives the inline height from the dragged
					// item

					if(!p.height()) {
                        p.height(self.currentItem.innerHeight() -
                                 parseInt(self.currentItem.css('paddingTop')||0, 10) -
                                 parseInt(self.currentItem.css('paddingBottom')||0, 10));
                    };
					if(!p.width()) {
                        p.width(self.currentItem.innerWidth() -
                                parseInt(self.currentItem.css('paddingLeft')||0, 10) -
                                parseInt(self.currentItem.css('paddingRight')||0, 10));
                    };
				}
			};
		}

		//Create the placeholder
		self.placeholder = $(o.placeholder.element.call(self.element, self.currentItem));

		//Append it after the actual current item
		self.currentItem.after(self.placeholder);

		//Update the size of the placeholder (TODO: Logic to fuzzy, see line 316/317)
		o.placeholder.update(self, self.placeholder);

	},

	_updateItemOrder: function(event) {
        // Step one, find the current container.
		var candidateContainer = null;

		for (var i = this.containers.length - 1; i >= 0; i--) {
			// Never consider a container that's located within the item itself
			if($.ui.contains(this.currentItem[0], this.containers[i].element[0]))
				continue;

			if(this._intersectsWith(this.containers[i].containerCache)) {
				// if we've already found a container and it's more
				// "inner" than this, then continue
				if(candidateContainer !== null &&
                   $.ui.contains(this.containers[i].element[0], candidateContainer.element[0]))
					continue;

				candidateContainer = this.containers[i];
			};
		};

        if(candidateContainer === null) {
            // If no current container are found we return.
            return;
        }

        // Step two, find a new order.
		for (var i = candidateContainer.items.length - 1; i >= 0; i--) {
			// Cache variables and intersection, continue if no intersection
			var item = candidateContainer.items[i];
            var intersection = this._intersectsWithPointer(item);

			if (!intersection)
                continue;

            var itemElement = item.item[0];
            if(itemElement != this.currentItem[0] //cannot intersect with itself
			   &&	this.placeholder[intersection == 1 ? "next" : "prev"]()[0] != itemElement //no useless actions that have been done before
				&&	!$.ui.contains(this.placeholder[0], itemElement) //no action if the item moved is the parent of the item checked
			) {
            //if ((!item.is(this.currentItem)) &&
            //    (!item.is_contained(this.placeholder)) &&
            //    (!item.is(this.placeholder[intersection == 1 ? "next" : "prev"]()))) {
                this._reorderItem(event, candidateContainer, item, intersection == 1 ? "down" : "up");
			};
            return;
		};

        // Step three, handle empty containers.
        if (this.currentContainer != candidateContainer && this.options.dropOnEmpty) {
            this._reorderItem(event, candidateContainer);
        };
	},

    _reorderItem: function(event, container, item, direction) {
        var refresh = [this.currentContainer];
        var hard_refresh = false;

        // Move the placeholder.
        if (item !== undefined) {
             item.item[0].parentNode.insertBefore(this.placeholder[0], (direction == "down" ? item.item[0] : item.item[0].nextSibling));
            // if (direction) {
            //     item.item.before(this.placeholder);
            // } else {
            //     item.item.after(this.placeholder);
            // };
        } else {
            container.element.append(this.placeholder);
        };
        // Update the container if required.
        if (container != this.currentContainer) {
            refresh.push(container);
            hard_refresh = true;
            this.currentContainer = container;
            this.options.placeholder.update(this.currentContainer, this.placeholder);
        };
        // Event
        this._trigger("reorder", event, this._eventOrderInfo(item, direction));

        // Refresh positions afterwards.
		// 1. we create a setTimeout, that calls refreshPositions
		// 2. on the instance, we have a counter variable, that get's higher after every append
		// 3. on the local scope, we copy the counter variable, and check in the timeout, if it's still the same
		// 4. this lets only the last addition to the timeout stack through
		this.counter = this.counter ? ++this.counter : 1;
		var self = this, counter = this.counter;

		window.setTimeout(function() {
			if(counter == self.counter) {
                while (refresh.length) {
                    refresh.pop().refreshPositions(hard_refresh);
                };
            };
		},0);

	},


	_createHelper: function(event) {
		var o = this.options;
		var helper = $.isFunction(o.helper) ? $(o.helper.apply(this.element[0], [event, this.currentItem])) : (o.helper == 'clone' ? this.currentItem.clone() : this.currentItem);

		if(!helper.parents('body').length) //Add the helper to the DOM if that didn't happen already
			$(o.appendTo != 'parent' ? o.appendTo : this.currentItem[0].parentNode)[0].appendChild(helper[0]);

		if(helper[0] == this.currentItem[0]) {
			this._storedCSS = {
                width: this.currentItem[0].style.width,
                height: this.currentItem[0].style.height,
                position: this.currentItem.css("position"),
                top: this.currentItem.css("top"),
                left: this.currentItem.css("left")
            };
        }
		if(helper[0].style.width == '' || o.forceHelperSize) {
            helper.width(this.currentItem.width());
        }
		if(helper[0].style.height == '' || o.forceHelperSize){
            helper.height(this.currentItem.height());
        }
		return helper;
	},

	_adjustOffsetFromHelper: function(obj) {
		if (typeof obj == 'string') {
			obj = obj.split(' ');
		}
		if ($.isArray(obj)) {
			obj = {left: +obj[0], top: +obj[1] || 0};
		}
		if ('left' in obj) {
			this.offset.click.left = obj.left + this.margins.left;
		}
		if ('right' in obj) {
			this.offset.click.left = this.helperProportions.width - obj.right + this.margins.left;
		}
		if ('top' in obj) {
			this.offset.click.top = obj.top + this.margins.top;
		}
		if ('bottom' in obj) {
			this.offset.click.top = this.helperProportions.height - obj.bottom + this.margins.top;
		}
	},

	_getParentOffset: function() {
		//Get the offsetParent and cache its position
		this.offsetParent = this.helper.offsetParent();
		var po = this.offsetParent.offset();

		// This is a special case where we need to modify a offset calculated on start, since the following happened:
		// 1. The position of the helper is absolute, so it's position is calculated based on the next positioned parent
		// 2. The actual offset parent is a child of the scroll parent, and the scroll parent isn't the document, which means that
		//    the scroll is included in the initial calculation of the offset of the parent, and never recalculated upon drag
		if(this.cssPosition == 'absolute' &&
           this.scrollParent[0] != document &&
           $.ui.contains(this.scrollParent[0], this.offsetParent[0])) {
			po.left += this.scrollParent.scrollLeft();
			po.top += this.scrollParent.scrollTop();
		}

        //This needs to be actually done for all browsers, since pageX/pageY includes this information
		if((this.offsetParent[0] == document.body)
		   || (this.offsetParent[0].tagName && this.offsetParent[0].tagName.toLowerCase() == 'html' && $.browser.msie)) //Ugly IE fix
			po = { top: 0, left: 0 };

		return {
			top: po.top + (parseInt(this.offsetParent.css("borderTopWidth"),10) || 0),
			left: po.left + (parseInt(this.offsetParent.css("borderLeftWidth"),10) || 0)
		};

	},

	_getRelativeOffset: function() {
		if(this.cssPosition == "relative") {
			var p = this.currentItem.position();
			return {
				top: p.top - (parseInt(this.helper.css("top"),10) || 0) + this.scrollParent.scrollTop(),
				left: p.left - (parseInt(this.helper.css("left"),10) || 0) + this.scrollParent.scrollLeft()
			};
		} else {
			return {top: 0, left: 0};
		}
	},

	_cacheMargins: function() {
		this.margins = {
			left: (parseInt(this.currentItem.css("marginLeft"),10) || 0),
			top: (parseInt(this.currentItem.css("marginTop"),10) || 0)
		};
	},

	_cacheHelperProportions: function() {
		this.helperProportions = {
			width: this.helper.outerWidth(),
			height: this.helper.outerHeight()
		};
	},

	_setContainment: function() {

		var o = this.options;
		if(o.containment == 'parent') o.containment = this.helper[0].parentNode;
		if(o.containment == 'document' || o.containment == 'window') this.containment = [
			0 - this.offset.relative.left - this.offset.parent.left,
			0 - this.offset.relative.top - this.offset.parent.top,
			$(o.containment == 'document' ? document : window).width() - this.helperProportions.width - this.margins.left,
			($(o.containment == 'document' ? document : window).height() || document.body.parentNode.scrollHeight) - this.helperProportions.height - this.margins.top
		];

		if(!(/^(document|window|parent)$/).test(o.containment)) {
			var ce = $(o.containment)[0];
			var co = $(o.containment).offset();
			var over = ($(ce).css("overflow") != 'hidden');

			this.containment = [
				co.left + (parseInt($(ce).css("borderLeftWidth"),10) || 0) + (parseInt($(ce).css("paddingLeft"),10) || 0) - this.margins.left,
				co.top + (parseInt($(ce).css("borderTopWidth"),10) || 0) + (parseInt($(ce).css("paddingTop"),10) || 0) - this.margins.top,
				co.left+(over ? Math.max(ce.scrollWidth,ce.offsetWidth) : ce.offsetWidth) - (parseInt($(ce).css("borderLeftWidth"),10) || 0) - (parseInt($(ce).css("paddingRight"),10) || 0) - this.helperProportions.width - this.margins.left,
				co.top+(over ? Math.max(ce.scrollHeight,ce.offsetHeight) : ce.offsetHeight) - (parseInt($(ce).css("borderTopWidth"),10) || 0) - (parseInt($(ce).css("paddingBottom"),10) || 0) - this.helperProportions.height - this.margins.top
			];
		}

	},

	_convertPositionTo: function(d, pos) {

		if(!pos) pos = this.position;
		var mod = d == "absolute" ? 1 : -1;
		var o = this.options, scroll = this.cssPosition == 'absolute' && !(this.scrollParent[0] != document && $.ui.contains(this.scrollParent[0], this.offsetParent[0])) ? this.offsetParent : this.scrollParent, scrollIsRootNode = (/(html|body)/i).test(scroll[0].tagName);

		return {
			top: (
				pos.top																	// The absolute mouse position
				+ this.offset.relative.top * mod										// Only for relative positioned nodes: Relative offset from element to offset parent
				+ this.offset.parent.top * mod											// The offsetParent's offset without borders (offset + border)
				- ($.browser.safari && this.cssPosition == 'fixed' ? 0 : ( this.cssPosition == 'fixed' ? -this.scrollParent.scrollTop() : ( scrollIsRootNode ? 0 : scroll.scrollTop() ) ) * mod)
			),
			left: (
				pos.left																// The absolute mouse position
				+ this.offset.relative.left * mod										// Only for relative positioned nodes: Relative offset from element to offset parent
				+ this.offset.parent.left * mod											// The offsetParent's offset without borders (offset + border)
				- ($.browser.safari && this.cssPosition == 'fixed' ? 0 : ( this.cssPosition == 'fixed' ? -this.scrollParent.scrollLeft() : scrollIsRootNode ? 0 : scroll.scrollLeft() ) * mod)
			)
		};

	},

	_generatePosition: function(event) {

		var o = this.options, scroll = this.cssPosition == 'absolute' && !(this.scrollParent[0] != document && $.ui.contains(this.scrollParent[0], this.offsetParent[0])) ? this.offsetParent : this.scrollParent, scrollIsRootNode = (/(html|body)/i).test(scroll[0].tagName);

		// This is another very weird special case that only happens for relative elements:
		// 1. If the css position is relative
		// 2. and the scroll parent is the document or similar to the offset parent
		// we have to refresh the relative offset during the scroll so there are no jumps
		if(this.cssPosition == 'relative' && !(this.scrollParent[0] != document && this.scrollParent[0] != this.offsetParent[0])) {
			this.offset.relative = this._getRelativeOffset();
		}

		var pageX = event.pageX;
		var pageY = event.pageY;

		/*
		 * - Position constraining -
		 * Constrain the position to a mix of grid, containment.
		 */

		if(this.originalPosition) { //If we are not dragging yet, we won't check for options

			if(this.containment) {
				if(event.pageX - this.offset.click.left < this.containment[0])
                    pageX = this.containment[0] + this.offset.click.left;
				if(event.pageY - this.offset.click.top < this.containment[1])
                    pageY = this.containment[1] + this.offset.click.top;
				if(event.pageX - this.offset.click.left > this.containment[2])
                    pageX = this.containment[2] + this.offset.click.left;
				if(event.pageY - this.offset.click.top > this.containment[3])
                    pageY = this.containment[3] + this.offset.click.top;
			}

			if(o.grid) {
				var top = this.originalPageY + Math.round((pageY - this.originalPageY) / o.grid[1]) * o.grid[1];
				pageY = this.containment ? (!(top - this.offset.click.top < this.containment[1] || top - this.offset.click.top > this.containment[3]) ? top : (!(top - this.offset.click.top < this.containment[1]) ? top - o.grid[1] : top + o.grid[1])) : top;

				var left = this.originalPageX + Math.round((pageX - this.originalPageX) / o.grid[0]) * o.grid[0];
				pageX = this.containment ? (!(left - this.offset.click.left < this.containment[0] || left - this.offset.click.left > this.containment[2]) ? left : (!(left - this.offset.click.left < this.containment[0]) ? left - o.grid[0] : left + o.grid[0])) : left;
			}

		}

		return {
			top: (
				pageY																// The absolute mouse position
				- this.offset.click.top													// Click offset (relative to the element)
				- this.offset.relative.top												// Only for relative positioned nodes: Relative offset from element to offset parent
				- this.offset.parent.top												// The offsetParent's offset without borders (offset + border)
				+ ($.browser.safari && this.cssPosition == 'fixed' ? 0 : ( this.cssPosition == 'fixed' ? -this.scrollParent.scrollTop() : ( scrollIsRootNode ? 0 : scroll.scrollTop() ) ))
			),
			left: (
				pageX																// The absolute mouse position
				- this.offset.click.left												// Click offset (relative to the element)
				- this.offset.relative.left												// Only for relative positioned nodes: Relative offset from element to offset parent
				- this.offset.parent.left												// The offsetParent's offset without borders (offset + border)
				+ ($.browser.safari && this.cssPosition == 'fixed' ? 0 : ( this.cssPosition == 'fixed' ? -this.scrollParent.scrollLeft() : scrollIsRootNode ? 0 : scroll.scrollLeft() ))
			)
		};

	},

    _finish: function(event) {
        this.placeholder.before(this.currentItem);
        this._trigger("order", event, this._eventOrderInfo());
    },

	_clear: function(event, noPropagation) {
		this.reverting = false;

		//Do what was originally in plugins
		if(this._storedCursor) {
            $('body').css("cursor", this._storedCursor);
        }

		this.dragging = false;
        this._trigger("beforeStop", event, this._eventInfo());

        // Revert CSS and remove helper.
        if(this.helper[0] == this.currentItem[0]) {
            // Restore opacity, zIndex and other CSS.
            if(this._storedOpacity) {
                this.currentItem.css("opacity", this._storedOpacity);
            };
		    if(this._storedZIndex) {
                this.currentItem.css("zIndex", this._storedZIndex == 'auto' ? '' : this._storedZIndex);
            };
			for(var i in this._storedCSS) {
				if(this._storedCSS[i] == 'auto' || this._storedCSS[i] == 'static')
                    this._storedCSS[i] = '';
			};
			this.currentItem.css(this._storedCSS).removeClass("ui-sortable-helper");
		} else {
            this.helper.remove();
			this.currentItem.show();
		};
        this.helper = null;

        // Remove placeholder
		this.placeholder[0].parentNode.removeChild(this.placeholder[0]);

		this._trigger("stop", event, this._eventInfo());
        this.currentItem = null;
        this.currentContainer = null;
		return true;

	},

    validate: function(deferred){
        this.deferred = deferred;
    },

	_trigger: function() {
		if ($.Widget.prototype._trigger.apply(this, arguments) === false) {
			this.cancel();
		}
	},

    _eventOrderInfo: function(item, direction) {
        var order = 0;
        if (item !== null) {
            var correctif = 0;
            var items = this.currentContainer.items;
            for (; order < items.length; order++) {
                if (items[order] == item) {
                    if (direction == 'up')
                        correctif += 1;
                    order += correctif;
                    break;
                };
            };
        } else {
            order = null;
        };

        return {
            validate: $.proxy(this.validate, this),
            placeholder: this.placeholder,
            item: this.currentItem,
            container: this.currentContainer.element,
            order: order,
            relative: item
        };
    },

	_eventInfo: function() {
		return {
            placeholder: this.placehoder,
            item: this.currentItem,
            container: this.currentContainer.element
		};
	}

});

})(jQuery);
