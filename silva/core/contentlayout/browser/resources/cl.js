(function() {
YAHOO.util.Event.throwErrors = true;
YAHOO.namespace("bethel.contentlayout");
}()); /* bootstrapping */

(function() { /* YAHOO.bethel.contentlayout.getData function */
    /**
    * Returns a JSON-compatible data structure representing the data 
    * currently contained in the form.
    * @method getData
    * @return {Object} A JSON object reprsenting the data of the 
    * current form.
    * (copied from yui Dialog source)

    * aaltepet: this function was copied from yui Dialog source
        so that it could be used in other circumstances, like the
        edit dialog (which is just a panel), and for tools in the
        infopanel.
    */
    var Selector = YAHOO.util.Selector,
        Dom = YAHOO.util.Dom;

    YAHOO.bethel.contentlayout.getData = function (searchDOM) {

    var oForm = Selector.query('form', searchDOM, true),
        aElements,
        nTotalElements,
        oData,
        sName,
        oElement,
        nElements,       
        sType,
        sTagName,
        aOptions,
        nOptions,
        aValues,
        oOption,
        oRadio,
        oCheckbox,
        valueAttr,
        i,
        n;    
    if (!oForm) {
        return {};
    }
    function isFormElement(p_oElement) {
        var sTag = p_oElement.tagName.toUpperCase();
        return ((sTag == "INPUT" || sTag == "TEXTAREA" || 
            sTag == "SELECT") && p_oElement.name == sName);
    }

    if (oForm) {
        aElements = oForm.elements;
        nTotalElements = aElements.length;
        oData = {};
    
        for (i = 0; i < nTotalElements; i++) {
            sName = aElements[i].name;
    
            /*
                Using "Dom.getElementsBy" to safeguard user from JS 
                errors that result from giving a form field (or set of 
                fields) the same name as a native method of a form 
                (like "submit") or a DOM collection (such as the "item"
                method). Originally tried accessing fields via the 
                "namedItem" method of the "element" collection, but 
                discovered that it won't return a collection of fields 
                in Gecko.
            */
        
            oElement = Dom.getElementsBy(isFormElement, "*", oForm);
            nElements = oElement.length;
        
            if (nElements > 0) {
                if (nElements == 1) {
                    oElement = oElement[0];
        
                    sType = oElement.type;
                    sTagName = oElement.tagName.toUpperCase();
        
                    switch (sTagName) {
                    case "INPUT":
                        if (sType == "checkbox" || sType == "radio") {
                            if (oElement.checked)
                              oData[sName] = oElement.value;
                        } else if (sType != "radio") {
                            oData[sName] = oElement.value;
                        }
                        break;
        
                    case "TEXTAREA":
                        oData[sName] = oElement.value;
                        break;
        
                    case "SELECT":
                        aOptions = oElement.options;
                        nOptions = aOptions.length;
                        aValues = [];
        
                        for (n = 0; n < nOptions; n++) {
                            oOption = aOptions[n];
                            if (oOption.selected) {
                                valueAttr = oOption.attributes.value;
                                aValues[aValues.length] = (valueAttr && valueAttr.specified) ? oOption.value : oOption.text;
                            }
                        }
                        oData[sName] = aValues;
                        break;
                    }
                } else {
                    sType = oElement[0].type;
                    switch (sType) {
                    case "radio":
                        for (n = 0; n < nElements; n++) {
                                oRadio = oElement[n];
                            if (oRadio.checked) {
                                oData[sName] = oRadio.value;
                                break;
                            }
                        }
                        break;
        
                    case "checkbox":
                        aValues = [];
                        for (n = 0; n < nElements; n++) {
                            oCheckbox = oElement[n];
                            if (oCheckbox.checked) {
                                aValues[aValues.length] =  oCheckbox.value;
                            }
                        }
                        oData[sName] = aValues;
                        break;
                    case "textarea":
                        aValues = [];
                        for (n = 0; n < nElements; n++) {
                            aValues[aValues.length] =  oElement[n].value;
                        }
                        oData[sName] = aValues;
                        break;
        
                    case "text":
                        aValues = [];
                        for (n = 0; n < nElements; n++) {
                            aValues[aValues.length] =  oElement[n].value;
                        }
                        oData[sName] = aValues;
                        break;
                    }
                }
            }
        }
    }

    return oData;
}

}()); /* end YAHOO.bethel.contentlayout.getData function */

(function() { /* YAHOO.bethel.contentlayout.InfoPanel */
    YAHOO.bethel.contentlayout.InfoPanel = function(el, userConfig, app) {
        /* this needs to be set _before_ the constructor call. */
        this.app = app;
        /* this holds the "extra" tools, like SNN properties */
        this.tools = {};
        // allow the state cookie to live for 1 year
        this.cookie_lifetime = 31536000000; //(365 * 24 * 60 * 60 * 1000);
        YAHOO.bethel.contentlayout.InfoPanel.superclass.constructor.call(this, el, userConfig);
    }      
    var Lang = YAHOO.lang,
         Module = YAHOO.widget.Module,
         InfoPanel = YAHOO.bethel.contentlayout.InfoPanel,
         Dom = YAHOO.util.Dom,
         Cookie = YAHOO.util.Cookie,
         Event = YAHOO.util.Event,
         Selector = YAHOO.util.Selector,
         Button = YAHOO.widget.Button,
         Menu = YAHOO.widget.Menu;    
        
    DEFAULT_CONFIG = {
    /* If true, makes the info panel have an open and closed
        state. If false, it is always open.*/        
        "CLOSEABLE": {
            key: "closeable",
            value: false
        }
    };

    Lang.extend(InfoPanel, Module, {
        /* methods overridden from YAHOO.widget.Module */
        init: function(el, userConfig) {            
            InfoPanel.superclass.init.call(this, el);
            if (userConfig) {
                this.cfg.applyConfig(userConfig, true);
            }
            this.initControlButton();            
            this.initPreviewButton();
            this.initTemplateSwitchButton();
            this.updateIFrameWidth();
            this.initIFrameResizeHandler();
        },
        
        initDefaultConfig: function() {    
            /* initialize the default configuration properties for this panel
                instance.  */
            InfoPanel.superclass.initDefaultConfig.call(this);        
            var cfg = this.cfg;
            /* `closeable`: when true, the panel is collapsible */
            cfg.addProperty("closeable", {
                handler: function(type, args, obj) {
                    this.cfg.setProperty("closeable", args[0], true);
                }
             });
         },
    
        registerTool: function(name, toolInstance) {
            /* SNN news/agenda items use this method to register
               their custom tools (e.g. the properties) */
            this.tools[name] = toolInstance;
            /* add this tool's element to the infopanel body */
            this.body.appendChild(toolInstance.element);
            /* make sure the tool has the necessary DOM 
                (if the tool wasn't already prepared with this, it will
                    be absent -- even after calling `render`) */
            var items = {'hd':'header','bd':'body','ft':'footer'};
            //prevent potential multiple redraws by establishing this new DOM 
            // in a document fragment
            df = toolInstance.element.ownerDocument.createDocumentFragment();
            for (var el in items) {
                if (!Selector.query('.'+el,toolInstance.element, true)) {
                    var attr = items[el];
                    var n = this.element.ownerDocument.createElement('div');
                    n.className = el;
                    /* since the module's init() has run already,
                       and render() will not pick them up, manually
                       set the structure attribs here*/
                    toolInstance[attr] = n;
                    df.appendChild(n)
                    toolInstance.element.appendChild(n)
                }
            }
            toolInstance.element.appendChild(df);
            toolInstance.installIntoPanel(this);
        },
        
        /* status functions and manipulators */
        isClosed: function() {
            /* returns True if the info panel is in a closed state */
            return Dom.hasClass(this.element, 'closed')
        },
    
        changeState: function() {
            /* changes the info panel state from closed to open (and vice versa) */
            if (this.isClosed()) {
                Dom.removeClass(this.element, 'closed');
                Dom.addClass(this.element, 'open');
                this.setOpenStateCookie('open');
                for (var k in this.tools) {
                    this.tools[k].panelOpened();
                }
            } else {
                Dom.removeClass(this.element, 'open');
                Dom.addClass(this.element, 'closed');
                this.setOpenStateCookie('closed');
                for (var k in this.tools) {
                    this.tools[k].panelClosed();
                }
            }
            // ensure the iframe's width is updated when the panel state changes */
            this.updateIFrameWidth();
        },
    
        updateIFrameWidth: function() {
            /* update the width attr of the iframe according to the width of the 
                info panel.  This should also be called whenever the width of the browser
                window chagnes */
            /* the iframe's width is originally 100% (same width as the parent container.
                This method update's the iframe width to be the width of the parent
                container - ( info panel width + 5px padding ) */
            var panelWidth = this.element.clientWidth + 5;
            var newWidth = this.app.iframe.parentNode.clientWidth - panelWidth;
            this.app.iframe.width = newWidth;
        },
    
        setOpenStateCookie: function(newstate) {
            /* set's the "open state" cookie so the ADDor will remember what state
                the infopanel was in.
                Acceptable values are 'open' and 'closed'*/
            var expires = new Date();
            expires.setTime(expires.getTime() + this.cookie_lifetime);
            if (location.hostname == 'localhost') {
                /* firefox does not accept cookies with a domain of 'localhost'
                (which we use during development).  So in this case do not set a domain
                (causing the browser to use the hostname. */
                Cookie.set('cl-open-state', newstate, { expires: expires,
                                                        path: '/' });
            } else {
                Cookie.set('cl-open-state', newstate, { expires: expires,
                                                        domain: location.hostname,
                                                        path: '/' });
            }
        },
    
        initIFrameResizeHandler: function() {
            /* initializes the window resize handler, so the iframe's width is corrected
                whenever the window size changes
                XXX does this even belong here?  This shouldn't be a function of the
                    info panel, as it seems like a side effect.  */
            Event.addListener(window, "resize", 
                function() { this.updateIFrameWidth(); },
                null, this); 
        },
    
        initControlButton: function() {
            /* create the control button, add onclick to change open state */            
            if(!this.cfg.getProperty("closeable")) {
                return;
            }
            this.controlButton = new Button(this.element.id + '-control',
                {onclick: {fn: function(event) { this.changeState(); },
                    scope: this }
                }  
            );
        },
        
        initPreviewButton: function() {
            this.previewModeButton = new Button('previewmode', {
                type: "checkbox",
                title: "Preview"
            });
            this.previewModeButton.addClass("infopanel-button");
            this.previewModeButton.addListener("checkedChange", function(event, context) {
                /* when this button is in a checked(true) state, the
                   CLE is in 'preview' mode.  When in an unchecked(false)
                   state, it's in edit mode */
                var infopanel = context[0],
                     app = context[1];
                if (event.newValue == true) {
                    /* switch to preview mode */
                    app.changeViewMode('preview');
                    this.set("title", "Switch to Edit");
                    this.set("label", "");
                } else {
                    app.changeViewMode('edit');
                    this.set("title", "Switch to Preview");
                    this.set("label", "");
                }
                /* notify state changed */
                infopanel.appStateChanged();
            }, [this, this.app]);
        }, /* end initPreviewButton */
        
        appStateChanged: function() {
            /* this function informs all registered tools that the
               state of the app has changed.
               (I suppose this could be a yui event, but this approach
               is slightly quicker)
            /* tools should call this when the state of the CLE/app has
               changed, e.g. from edit to move mode, from move to preview, etc.
               */
            for (var toolName in this.tools) {
                var tool = this.tools[toolName];
                if (tool.notifyAppStateChanged) tool.notifyAppStateChanged();
            }
        }, /* end appStateChanged */
        
        initTemplateSwitchButton: function() {
        
            /* Initialized the "switch template" button.
                The template switch button is a menubutton which provides a list of 
                the available content layout templates.*/
            /* Note: this button is only displayed/available if the meta_type
                has more than one supported template (configured in the content
                templates service */
            
            /* Creates the confirm window */
            var handleConfirmChange = function() {  
                var templateName,
                     ts_select = document.templateSelect.Select_Template;
                /* Finds the selected template from the Switch Template list by looping through them. */
                if (!ts_select.length) { /* in case there is only one radio button,
                                             this won't be a list */
                    ts_select = [ts_select];
                }
                for (var i=ts_select.length; i--;) { /* reverse loops are faster */
                    if (ts_select[i].checked) {
                        templateName = ts_select[i].value;
                        break;
                    }
                }
                /* Constructs the new request using the selected template. */
                var url = objurl + "/switchlayouttemplate";
                var params = "newTemplate="+templateName;
                /* Sends the request to change the template */
                Connect.asyncRequest('POST', url,
                    { success: function(resp) {
                        var newHref = window.location.href;
                        newHref = newHref.replace(/tab_edit.*?$/,"tab_edit");
                        window.location.replace(newHref);
                        },
                    failure: function(resp) { alert('template switch failure') } 
                    }, params);
                    this.submit();
            };
            
            /*Handle cancles on confirm window */
            var handleCancelChange = function() {            
                this.hide();
            }; 
        
            /*Create the confirm template switch window */
            this.confirmChange =  new YAHOO.widget.SimpleDialog("confirm-template-switch",  
                { 
                  width: "300px", 
                  hideaftersubmit: true,                  
                  modal: true,                  
                  fixedcenter: true, 
                  visible: false, 
                  draggable: false, 
                  close: true, 
                  text: "Are you sure you want to change templates?", 
                  constraintoviewport: true,
                  zindex: 200
                }
            );
            this.confirmChange.callback = {app:this};
            var confirmButtons = [ { text:"Change Template", handler:handleConfirmChange, isDefault:false }, 
                                 { text:"Cancel",  handler:handleCancelChange, setClass: 'canceler' } 
            ];        
            this.confirmChange.setHeader("Confirm Template Change");        
            this.confirmChange.cfg.queueProperty("buttons", confirmButtons);
            this.confirmChange.render();
            /*This prevents error when button doesn't exist.*/
            if (this.confirmChange.getButtons()){
		this.confirmChange.getButtons()[1]._button.className += 'canceler';
            }
            /* End confirm window */
            
            /*Handles Cancel being pressed in the Change Template window */        
            var handleCancel = function() {
                        this.cancel();
                    },
                /* Shows the confirm dialog */
                handleSubmit = function() {                                           
                    this.callback['app'].confirmChange.show();         
                }
                templateSelectButtons = [
                   { text: "Switch Template", handler: handleSubmit, isDefault: false},
                   { text: "Cancel", handler: handleCancel }
                ];
        
            /* Dialog to select new template window */
            this.templateSwitchDialog = new YAHOO.widget.Dialog('switch-template-select',
                {fixedcenter: "contained",
                modal: true,
                close: true,
                draggable: false,
                hideaftersubmit: true,
                height: "450px",            
                width: "350px",
                visible: false,
                constraintoviewport: true
                },
                this
            );
            this.templateSwitchDialog.callback = {app:this};
            
            this.templateSwitchDialog.setHeader("Switch Template");        
            this.templateSwitchDialog.cfg.queueProperty("buttons", templateSelectButtons);
            this.templateSwitchDialog.render();
            /*This prevents error when button doesn't exist.*/
            if (this.templateSwitchDialog.getButtons()){
		this.templateSwitchDialog.getButtons()[1]._button.className += 'canceler';
            }
            /*End select new template window */
            

            if (!Selector.query('#switch-template-cont', document, true)){
                return;
            }
            this.templateSwitch = new Button('switch-template-button',
                {type: "push",
                    title: "Switch Template"
                }
            );
            this.templateSwitch.subscribe('click', function(event, context) {
                context.templateSwitchDialog.show();
                }, this
            );
            this.templateSwitch.addClass("infopanel-button");
        } /* end initTemplateSwitchButton */
    
  }); /*end Lang.extend */
    
}()); /* YAHOO.bethel.contentlayout.InfoPanel */

(function() { /* YAHOO.bethel.contentlayout.PartMoveTool */
 /* the part move tool is a button in the info panel which activates
    the "move" mode of the CLE.  In "move" mode, each movable part is turned
    into a draggable object which can be dropped on any section(droppable)
    and reordered.
    */
    YAHOO.bethel.contentlayout.PartMoveTool = function(el, userConfig) {
        YAHOO.bethel.contentlayout.PartMoveTool.superclass.constructor.call(this, el, userConfig);
        this.infopanel = null;
    }
    
    var Lang = YAHOO.lang,
        Module = YAHOO.widget.Module,
        PartMoveTool = YAHOO.bethel.contentlayout.PartMoveTool,
        Dom = YAHOO.util.Dom,
        Event = YAHOO.util.Event,
        Selector = YAHOO.util.Selector,
        Button = YAHOO.widget.Button;
        
    Lang.extend(PartMoveTool, Module, {

        panelOpened: function() {
            /* called when the info panel is opened. */
            return
        },
    
        panelClosed: function() {
            /* called when info panel is closed */
            return;
        },
    
        notifyAppStateChanged: function() {
            if (this.infopanel.app._view_mode == 'preview') {
                /* always disable edit mode */
                this.toolButton.set("disabled", true);
                if (this.toolButton.get("checked")) {
                    this.toolButton.set("checked", false);
                }
            } else {
                this.toolButton.set("disabled", false);
            }
        
        }, /* end notifyAppStateChanged */
        
        installIntoPanel: function(panel) {
            /* this is called by the InfoPanel.  This method installs the
               tool into the infopanel.  This adds the part move button into
               the panel, and configures the event handlers */
               
            this.infopanel = panel;
            var toolButtonName = this.element.id + "button";
            this.render();
            this.toolButton = new Button({id: toolButtonName,
                                            type: "checkbox",
                                            title: "Move",
                                            container: this.body,
                                            value: "move"
                                            });
            this.toolButton.addClass("infopanel-button");
            this.toolButton.addListener("checkedChange", function(event, context) {
                var app = context[0];
                if (app._view_mode == 'preview') {
                     /* only allow move mode if it is possible (e.g. not
                        in preview mode) */
                    if (event.newValue == true) {
                        /* don't enable */
                        return false;
                    }
                } else {
                    if (event.newValue == true) {
                        app.changeViewMode('move');
                    } else {
                        app.changeViewMode('edit');
                    }
                }
            }, [this.infopanel.app]);
        }, /* end installIntoPanel */
        
        changeState: function() {

        } /* end changeState */
        
    }); /* end Lang.extend */

})(); /* end YAHOO.bethel.contentlayout.PartMoveTool */

(function() { /* YAHOO.bethel.contentlayout.DDPart */
    YAHOO.bethel.contentlayout.DDPart = function(part, sGroup, app, config, handleElId) {
        YAHOO.bethel.contentlayout.DDPart.superclass.constructor.call(this, part, sGroup, config);
        if (handleElId) {
            this.setOuterHandleElId(handleElId);
        }
        this.logger = this.logger || YAHOO;
        var el = this.getDragEl();
        Dom.setStyle(el, "opacity", 0.67);
        this.goingUp = false;
        this.lastY = 0;
        this.moved = false;
        this.app = app;
        this.addButton = Dom.getPreviousSibling(this.getEl());
    }

    var Lang = YAHOO.lang,
        DDProxy = YAHOO.util.DDProxy,
        Dom = YAHOO.util.Dom,
        Motion = YAHOO.util.Motion,
        DDM = YAHOO.util.DragDropMgr,
        Connect = YAHOO.util.Connect,
        DDPart = YAHOO.bethel.contentlayout.DDPart;

    Lang.extend(DDPart, DDProxy, {
        startDrag: function(x, y) {
            // make the proxy look like the source element
            var dragEl = this.getDragEl();
            var clickEl = this.getEl();
            Dom.setStyle(clickEl, "visibility", "hidden");
            Dom.setStyle(this.addButton, "visibility", "hidden");

            dragEl.innerHTML = clickEl.innerHTML;
            Dom.setStyle(dragEl, "color", Dom.getStyle(clickEl, "color"));
            Dom.setStyle(dragEl, "backgroundColor", Dom.getStyle(clickEl, "backgroundColor"));
            Dom.setStyle(dragEl, "border", "2px solid gray");
            var dragHD = Selector.query('div.hd',dragEl,true);
            Dom.setStyle(dragHD, 'visibility', 'hidden');
        
            /* hide the part controls (edit, remove, move) of the proxy element */
            var clickBD = YAHOO.util.Selector.query('.part-controls', dragEl, true);
            Dom.setStyle(clickBD, "display", "none");
        
            /* inform the app that a part move is in process.  This was initially
                put in place so that partControlOverlays will remain hidden during 
                the move */
            this.app.disable_part_overlays = true;
        }, /* end startDrag */

        endDrag: function(e) {
            var srcEl = this.getEl();
            var proxy = this.getDragEl();
    
            // Show the proxy element and animate it to the src element's location
            Dom.setStyle(proxy, "visibility", "");
            var a = new Motion(proxy, 
                { points: { to: Dom.getXY(srcEl) } },
                0.2,
                YAHOO.util.Easing.easeOut
            );
            // Hide the proxy and show the source element when finished with the animation
            var proxyid = proxy.id;
            var thisid = this.id;
            a.onComplete.subscribe(function(a,b,context) {
                Dom.setStyle(proxyid, "visibility", "hidden");
                Dom.setStyle(thisid, "visibility", "");
                Dom.setStyle(context.ddpart.addButton, "visibility", "");
            }, {ddpart:this});
            a.animate();
            if (this.moved) {
                var partId = srcEl.id;
                var partModule = this.app.parts[partId][0]; 
        
                var oldSlotModule = this.app.parts[partId][1];
                var oldSlotParts = this.app.slots[oldSlotModule.element.id][1];
                /* srcEl.parentNode = slotModule.getBody(), so the
                    parent's parent is the slot DOM */
                var newSlotId = srcEl.parentNode.parentNode.id;
                var newSlotModule = this.app.slots[newSlotId][0];
                var newSlotParts = this.app.slots[newSlotId][1];
            
                // remove the part from the old slotModule parts list
                delete oldSlotParts[partId]
                // point the partModule to the new slotModule
                this.app.parts[partId][1] = newSlotModule;
            
                // add the partModule to the new slotModule's parts list
                newSlotParts[partId] = partModule;
            
                /* the part has moved.  Inform Silva that the part has moved */
                var url = top.objurl + "/moveparttoslot";
                var params = "partkey=" + this.app._getPartInfoFromID(partId)[1] + "&slotname="+newSlotId
                var next = Dom.getNextSibling(partModule.element);
                while (next) {
                    if (next.nodeName.toLowerCase() == 'div' && Dom.hasClass(next, 'part')) {
                        break;
                    }
                    next = Dom.getNextSibling(next);
                }
                if (next) {
                    var beforepartkey = this.app._getPartInfoFromID(next.id)[1];
                    params += "&beforepartkey="+beforepartkey;
                }
                Connect.asyncRequest('POST',
                    url,
                    {failure: function(resp) { alert("error moving the part"); } },
                    params
                );
            }
            this.app.disable_part_overlays = false;
        }, /* end endDrag */

        onDragDrop: function(e, id) {
            // If there is one drop interaction, the part was dropped either on the 
            // a slot or it was dropped on the current location of the part element.     
            if (DDM.interactionInfo.drop.length ===1) {
                // The position of the cursor at the time of the drop (YAHOO.util.Point)
                var pt = DDM.interactionInfo.point;
                // The region occupied by the source element at the time of the drop
                var region = DDM.interactionInfo.sourceRegion;
                // Check to see if we are over the source element's location.  We will 
                // add to the body of the slot if the destEl is the slot.
                if (!region.intersect(pt)) {
                    var destEl = Dom.get(id);
                    if (destEl.tagName.toLowerCase() == 'div' && Dom.hasClass(destEl, 'slot')) {
                        var srcEl = this.getEl();
                        // do the move only if the slot (destEl) is different than
                        //   the slot the part is in
                        if (this.app.slots[destEl.id] &&
                            this.app.parts[srcEl.id][1] != this.app.slots[destEl.id][0]) {
                            var destDD = DDM.getDDById(id);
                            //this is a slot, append to the body of the slot, above
                            // the add button
                            var destBody = Selector.query('.bd',destEl)[0];
                            destBody.insertBefore(srcEl, Dom.getLastChild(destBody));
                            destBody.insertBefore(this.addButton, srcEl);
                            destDD.isEmpty = false;
                            DDM.refreshCache();
                            this.moved = true;
                            /* update the part/slot datastructures */
                            this.app.slots[destEl.id][1][srcEl.id] = this.app.parts[srcEl.id][0];
                            var oldslot = this.app.parts[srcEl.id][1];
                            this.app.parts[srcEl.id][1] = this.app.slots[destEl.id][0];
                            delete this.app.slots[oldslot.id][1][srcEl.id];
                        }
                    }
                }
            }
        }, /* end onDragDrop */
        
        onDrag: function(e) {
            //keep track of the drag direction for use during onDragOver
            var y = Event.getPageY(e);
            if (y < this.lastY) {
                this.goingUp = true;
            } else if (y > this.lastY) {
                this.goingUp = false;
            }
            this.lastY = y;
        },

        onDragOver: function(e, id) {
            /* when dragging over parts, change the order */
            var srcEl = this.getEl();
            var destEl = Dom.get(id);
            //only concerned with part and slot divs
            if (destEl && destEl.nodeName.toLowerCase() == "div") {
                if (Dom.hasClass(destEl, 'part')) {
                    var p = destEl.parentNode;
                    if (this.goingUp) {
                        p.insertBefore(srcEl, Dom.getPreviousSibling(destEl)); // insert above
                    } else {
                        p.insertBefore(srcEl, Dom.getNextSibling(destEl)); // below
                    }
                    p.insertBefore(this.addButton, srcEl)
                    this.moved = true;
                    DDM.refreshCache();
                } else if (Dom.hasClass(destEl, 'slot')) {
                    /* being dragged over a slot.  If the part(srcEl) isn't in the 
                        slot(destEl), then move it to the slot.
                        Make the part the first element of slot's body.  Subsequent
                        moves will rearrange it to the "correct" location. */
                    if (this.app.slots[destEl.id] &&
                        this.app.parts[srcEl.id][1] != this.app.slots[destEl.id][0]) {
                        var slotModule = this.app.slots[destEl.id][0];
                        slotModule.body.insertBefore(srcEl, Dom.getLastChild(slotModule.body));
                        slotModule.body.insertBefore(this.addButton, srcEl);
                        this.app.slots[destEl.id][1][srcEl.id] = this.app.parts[srcEl.id][0];
                        var oldslot = this.app.parts[srcEl.id][1];
                        this.app.parts[srcEl.id][1] = slotModule;
                        delete this.app.slots[oldslot.id][1][srcEl.id];
                        this.moved = true;
                    }
                }
            }
        } /* end onDragOver */

    });

}());  /* YAHOO.bethel.contentlayout.DDPart */

(function() { /* YAHOO.bethel.contentlayout.EditorPanel */
  /* for any "editing" - style panel in the CLE */

    YAHOO.bethel.contentlayout.EditorPanel= function(el, userConfig, app) {
        this.app = app;
        YAHOO.bethel.contentlayout.EditorPanel.superclass.constructor.call(this, el, userConfig);
    }
    
    var EditorPanel = YAHOO.bethel.contentlayout.EditorPanel,
        getData = YAHOO.bethel.contentlayout.getData,
        Panel = YAHOO.widget.Panel
        Lang = YAHOO.lang,
        Dom = YAHOO.util.Dom,
        Region = YAHOO.util.Region,
        CustomEvent = YAHOO.util.CustomEvent,
        Layout = YAHOO.widget.Layout,
        Module = YAHOO.widget.Module,
        Overlay = YAHOO.widget.Overlay,
        Button = YAHOO.widget.Button,
        Event = YAHOO.util.Event,
        Menu = YAHOO.widget.Menu,
        Connect = YAHOO.util.Connect,
        Selector = YAHOO.util.Selector,
        Resize = YAHOO.util.Resize;
        

    Lang.extend(EditorPanel, Panel, {

    init: function(el, userConfig) {
        EditorPanel.superclass.init.call(this, el);
        if (userConfig) {
            this.cfg.applyConfig(userConfig, true);
        }
            
        /* helper function to determine if two 
           objects/dictionaries are equal */
        function dataEquals(obj1, obj2) {
            //http://stackoverflow.com/questions/201183/how-do-you-determine-equality-for-two-javascript-objects/201265#201265
            for (var i in obj1) {
                if (obj1.hasOwnProperty(i)) {
                    if (!obj2.hasOwnProperty(i)) return false;
                    if (obj1[i] instanceof Array) {
                        /* if the value of obj1[i] is an array, use dataEquals to
                           see if obj1 and obj2's values are the same. */
                        if (!dataEquals(obj1[i], obj2[i])) return false;
                    } else {
                        /* not an array, use comparison */
                        if (obj1[i] != obj2[i]) return false;
                    }
                }
            }
            for (var i in obj2) {
                if (obj2.hasOwnProperty(i)) {
                    if (!obj1.hasOwnProperty(i)) return false;
                    if (obj1[i] instanceof Array) {
                        /* if the value of obj1[i] is an array, use dataEquals to
                           see if obj1 and obj2's values are the same. */
                        if (!dataEquals(obj1[i], obj2[i])) return false;
                    } else {
                        /* not an array, use comparison */
                        if (obj1[i] != obj2[i]) return false;
                    }
                }
            }
            return true;
        }
        
        /* create a new event -- to be called when the 'X' button and the
           cancel button are clicked */
        this.cancelEvent = new YAHOO.util.CustomEvent("cancel", this);
        //We must override _doClose so we can fire the cancel event when the "X" button is clicked
        this._doClose = function(e) {
            Event.preventDefault(e);
            this.cancelEvent.fire(this);
        }
        this.cancelEvent.subscribe(function(type, args, me) {
            this.cleanupTinyMCE(true);
            if (! dataEquals(this.originalData, getData(this.editorIFrame.document))) {
                if (confirm("Changes have been made, but have not yet been saved.\nAre you sure you want to continue without saving?")) {
                    me.hide();
                }
            } else {
                me.hide();
            }
        }, this);
            
        this.beforeRenderEvent.subscribe(function(type, args, me) {
            var panelid = this.id + 'panel-layout';
            this.setBody('<div id="'+panelid+'"></div>');
            this.setHeader(this.cfg.getProperty("defaultTitle"));
            Event.onAvailable(panelid, function(editorPanel) {
                /* `this` is the DOM Element with id=panelid (above)
                    editorPanel is the actual EditorPanel instance */
                    
                //define panelid within this context
                var panelid = this.id + 'panel-layout';
                var units = editorPanel.setupPanelLayoutUnits(panelid);
                editorPanel.layout = new Layout(this, {
                    height: editorPanel.body.offsetHeight-15,
                    width: editorPanel.element.offsetWidth-25,
                    units: units
                });
                /* subscribe to the 'render' event of the layout, so that
                   code can be run once the layout is rendered */
                editorPanel.layout.subscribe('render', 
                    function(type, args, me) {
                        this.onLayoutRender();
                    }, editorPanel, true);
                editorPanel.layout.render();

                // create the buttons for the center module, place them in
                // the footer of the center layout unit
                var center = editorPanel.layout.getUnitByPosition("center");
                editorPanel.editorIFrame = window.frames[panelid + '-center-iframe'];
                var iframeDOM = Selector.query('iframe', center.body, true);
                editorPanel.editorIFrameDOM = iframeDOM;
                /* set the height of the dom to eliminate screen flicker */
                iframeDOM.height = center.body.clientHeight;
            
                /* this NEEDS to be registered on iframeDOM (an HTMLElement)
                    and NOT editorPanel.editorIFrame (a Window) */
                Event.addListener(iframeDOM, 'load',
                    function(p_sType, p_aArgs) {
                        this.iframeDOMLoaded(p_sType, p_aArgs);
                    },
                    [],
                    editorPanel);
            
                editorPanel.buttons = [];
                editorPanel.buttons['submit'] = new Button({
                    id: panelid+"-submit-button",
                    type: "button",
                    label: editorPanel.cfg.getProperty('submitLabel'),
                    container: center.footer,
                    onclick: {fn: function(event, obj) {
                        this.submit(event, obj);
                    },
                    scope: editorPanel}
                });
                var parent = Dom.getAncestorByClassName(editorPanel.buttons['submit']._button,
                    'yui-button');
                Dom.addClass(parent,'manipulator');
                editorPanel.buttons['cancel'] = new Button({
                    id: panelid+"-cancel-button",
                    type: "button",
                    label: "Cancel",
                    container: center.footer,
                    onclick: {fn: function(event,obj) { this.cancelEvent.fire(this); },
                        scope: editorPanel}
                });
                parent = Dom.getAncestorByClassName(editorPanel.buttons['cancel']._button,
                    'yui-button');
                Dom.addClass(parent,'canceler');
            }, this);
        }, this);

        this.beforeShowEvent.subscribe(function() {
            this.setHeader(this.cfg.getProperty("defaultTitle"));
            var url = this.cfg.getProperty("dialogUrl");
            if (url) {
                this.editorIFrameDOM.src = url;
            }
        }, this);
        
        this.beforeHideEvent.subscribe(function() {
            /* reset the panel and app states */
            this.cleanupTinyMCE(true);
            this.app.disable_part_overlays = false;
            this.editorIFrame.location.href = 'about:blank';
        }, this);
        
    }, /* end init */
    
    onLayoutRender: function() {
        /* this is called after the panel's inner layout (a Layout)
           has rendered */
        //do nothing for std EditorPanels
    }, /* end onLayoutRender */
    
    storeOriginalData: function() {
        /* store the "original" data -- to be used for comparison if 
            the panel is closed without saving/adding */
        //We must run this first so the originalData on the next line is the
        //"cleaned" version that TinyMCE produces, so we can compare to the
        //possibly changed cleaned version later
        this.cleanupTinyMCE(true); 
        this.originalData = getData(this.editorIFrame.document);
    }, /* end storeOriginalData */
    
    initDefaultConfig: function() {
        DEFAULT_CONFIG = {
            "SUBMITLABEL": {
                key: "submitLabel",
                value: "Save"
            },
            "DEFAULTTITLE": {
                key: "defaultTitle",
                value: "Edit"
            },
            "DIALOGURL": {
                key: "dialogUrl"
            },
            "SUBMITCALLBACK": {
                key: "submitCallback"
            }
        };
        EditorPanel.superclass.initDefaultConfig.call(this);
        var cfg = this.cfg;
        cfg.addProperty(DEFAULT_CONFIG.SUBMITLABEL.key, {
            handler: function(type, args, obj) {
                this.cfg.setProperty("submitLabel", args[0], true);
            },
            value: DEFAULT_CONFIG.SUBMITLABEL.value
        });
        cfg.addProperty(DEFAULT_CONFIG.DEFAULTTITLE.key, {
            handler: function(type, args, obj) {
                this.cfg.setProperty("defaultTitle", args[0], true);
            },
            value: DEFAULT_CONFIG.DEFAULTTITLE.value
        });
        cfg.addProperty(DEFAULT_CONFIG.DIALOGURL.key, {
            handler: function(type, args, obj) {
                this.cfg.setProperty("dialogUrl", args[0], true);
            }
        });
        cfg.addProperty(DEFAULT_CONFIG.SUBMITCALLBACK.key, {
            handler: function(type, args, obj) {
                this.cfg.setProperty("submitCallback", args[0], true);
            }
        });
    }, /* end initDefaultConfig */
    
    setupPanelLayoutUnits: function(panelid) {
        /* return an array of layout units, used to set up
           the body of the panel using LayoutManager */
        return [{ position: 'center', body: '<div id="'+panelid+'-center"><iframe border="0" width="100%" name="'+panelid+'-center-iframe" src="about:blank"></iframe></div>', footer: '<div id="'+panelid+'-center-footer"></div>', gutter: '0 0 0 0' }];
    }, /* end setupPanelLayoutUnits */
    
    iframeDOMLoaded: function(p_sType, p_aArgs) {
        /* called when the iframe DOM has loaded */
        if (this.editorIFrame.location.href == 'about:blank') {
            /* this happens when the iframe is originally
               loaded (i.e. it has no src attribute) */
            return;
        } else {
            this.displayEditDialog();
        }
    }, /* end iframeDOMLoaded */
    
    cleanupTinyMCE: function(remove) {
        /* cause any active tinymces in the editor iframe to save their contents
            into their text areas */
        if (this.editorIFrame.cleanupTinyMCE) {
            this.editorIFrame.cleanupTinyMCE();
        };
    }, /* end cleanupTinyMCE */

    displayEditDialog: function() {
        /* called after the edit dialog iframe has finished loading */
        /* hide the page, so no artifacts are displayed before it is
            ready */
        Dom.setStyle(this.editorIFrame.document.body, 'visibility', 'hidden');
        /* fix the height of the form so scrollbars appear.  It seems 
            that center.foot is actually displayed above (on top of) 
            center.body.  Compute the visible height of center.body, and 
            set the height of oForm to that.
        */
        var oForm = Selector.query('form', this.editorIFrame.document, true),
            formReg = Region.getRegion(oForm),
            /* height of body will change, so get the height of the parent */
            center = this.layout.getUnitByPosition("center"),
            bodyReg = Region.getRegion(center.body.parentNode), 
            footReg = Region.getRegion(center.footer),
            centerBodyHeight = bodyReg.height - footReg.height;
        Dom.setStyle(center.body, 'height', centerBodyHeight + 'px');
        this.editorIFrameDOM.height = centerBodyHeight;
        Dom.setStyle(oForm, 'height', centerBodyHeight+ 'px');
        //Dom.setStyle(oForm, 'height', (centerBodyHeight + 1) + 'px');
        Dom.setStyle(this.editorIFrame.document.body, 'visibility', '');

        this.storeOriginalData();
        
        /*Set cursor to focus on the first text input field */
        var docform = this.editorIFrame.document.forms[0],
             formels = docform.elements;
        for( i = 0, max=docform.length; i < max; i++ ) {
            var el = formels[ i ];
            if (el.type != "hidden" &&
                 !el.disabled &&
                 !el.readOnly &&
                 !el.id.match(/^button/)){
                if (el.className == 'mceEditor') {
                    this.editorIFrame.setTimeout("window.tinyMCE.execCommand('mceFocus', false, '" + el.id + "')", 1);
                } else {
                    el.focus();
                    if (el.type == 'text' || el.nodeName == 'textarea') {
                        el.selectionStart = 0;
                        el.selectionEnd = 0;
                    }
                }
                break;
            }
        }
    }, /* end displayEditDialog */
    
    submit: function(event, obj) {
        /* user attempting to submit form.
           gather form elements */
        var cb = this.cfg.getProperty("submitCallback");
        if (cb) {
            cb.fn.call(cb.scope, event, obj);
        }
    }
    }); /* end Lang.extend */
    
}()); /* end YAHOO.bethel.contentlayout.EditorPanel */

(function() { /* YAHOO.bethel.contentlayout.PartEditorPanel */

    YAHOO.bethel.contentlayout.PartEditorPanel= function(el, userConfig, app) {
        YAHOO.bethel.contentlayout.PartEditorPanel.superclass.constructor.call(this, el, userConfig, app);
    }

    var EditorPanel = YAHOO.bethel.contentlayout.EditorPanel,
        PartEditorPanel = YAHOO.bethel.contentlayout.PartEditorPanel,
        getData = YAHOO.bethel.contentlayout.getData,
        Panel = YAHOO.widget.Panel
        Lang = YAHOO.lang,
        Dom = YAHOO.util.Dom,
        Region = YAHOO.util.Region,
        CustomEvent = YAHOO.util.CustomEvent,
        Layout = YAHOO.widget.Layout,
        Module = YAHOO.widget.Module,
        Overlay = YAHOO.widget.Overlay,
        Button = YAHOO.widget.Button,
        Event = YAHOO.util.Event,
        Menu = YAHOO.widget.Menu,
        Connect = YAHOO.util.Connect,
        Selector = YAHOO.util.Selector,
        Resize = YAHOO.util.Resize;

    Lang.extend(PartEditorPanel, EditorPanel, {

    init: function(el, userConfig) { 
        PartEditorPanel.superclass.init.call(this, el);
        if (userConfig) {
            this.cfg.applyConfig(userConfig, true);
        }

        this.beforeRenderEvent.subscribe(function(type, args, me) {
            if (this.cfg.getProperty("displayMode") == "edit") {
                this.setHeader("Edit");
            } else {
                this.setHeader("Add to Page");
            }
        }, this);
        
        this.beforeShowEvent.subscribe(function() {
            if (this.cfg.getProperty("displayMode") == "add") {
                this.addMenu.cfg.setProperty('visible', true);
                this.setHeader("Add to Page");
                this.loadAddablesScreen();
            } else {
                this.loadEditorPanel();
            }
        }, this);
    
        this.beforeHideEvent.subscribe(function() {
            // manually hide the menu
            if (this.cfg.getProperty("displayMode") == "add") {
                this.addMenu.cfg.setProperty('visible', false);
                this.setCheckedAddablesMenuItem();
                this.collapseLeftPanelAddablesMenu();
            }
            this.setClickContext(null);
        }, this);

    }, /* end init */

    initDefaultConfig: function() {
        PartEditorPanel.superclass.initDefaultConfig.call(this);

        DEFAULT_CONFIG = {
            /* this is the DOM element that is the add menu */
            "ADDMENU": {
                key: "addMenu"
            },
            /* displaymode is either 'add' or 'edit'.  If 'add', pass in
                the 'addMenu' (required) */
            "DISPLAYMODE": {
                key: "displayMode",
                value: "add"
            },
            /* currently two types of parts: 'es' (external source parts)
                and page-title (the title of the page) */
            "PARTTYPE": {
                key: "partType",
                value: "es"
            }
        };

        var cfg = this.cfg;
        cfg.addProperty(DEFAULT_CONFIG.ADDMENU.key, {
            handler: function(type, args, obj) {
                this.cfg.setProperty("addMenu", args[0], true);
            }
        });
        cfg.addProperty(DEFAULT_CONFIG.DISPLAYMODE.key, {
            handler: function(type, args, obj) {
                this.cfg.setProperty("displayMode", args[0], true);
            },
            value: DEFAULT_CONFIG.DISPLAYMODE.value
        });
        cfg.addProperty(DEFAULT_CONFIG.PARTTYPE.key, {
            handler: function(type, args, obj) {
                this.cfg.setProperty("partType", args[0], true);
            },
            value: DEFAULT_CONFIG.PARTTYPE.value
        });
    }, /* end initDefaultConfig */

    onLayoutRender: function() {
        /* fired when the panels' layoutmanager/layout has completed
            rendering */
        if (this.cfg.getProperty("displayMode") == "add") {
            /* now load a "nice" view of the "common" addables in the
                main panel */
            this.setupLeftPanelAddablesMenu();
        }
    }, /* end onLayoutRender */
    
    setupPanelLayoutUnits: function(panelid) {
        /* return an array of layout units, used to set up
           the body of the panel using LayoutManager */
        var units = PartEditorPanel.superclass.setupPanelLayoutUnits.call(this,panelid);
        if (this.cfg.getProperty('displayMode') == 'add') {
            units.push({ position: 'left', width: 175, resize: false, body: '', gutter: '0 0 0 0' });
        }
        return units;
    }, /* end setupPanelLayoutUnits */
    
    iframeDOMLoaded: function(p_sType, p_aArgs) {
        /* called when the iframe DOM has loaded */
        /* `this` is the editorPanel */
        var href = this.editorIFrame.location.href;
        if (this.editorIFrame.location.href == 'about:blank') {
            /* this happens when the iframe is originally
               loaded (i.e. it has no src attribute) */
            return;
        } else if (href.search(/addablesscreen/) > -1) {
            /* this is the addables screen.  Loop through table
               cells, making each clickable */
            var cells = Selector.query('div.option', this.editorIFrame.document);
            for (var i=cells.length; i--;) {
                var cell = cells[i];
                Event.addListener(cell, "click",
                    function(event, cell) {
                        var name = cell.getAttribute('name');
                        this.setCheckedAddablesMenuItem(name);
                        this.loadEditorPanel(name);
                        Event.preventDefault(event);
                        return false;
                }, cell, this);
            }
        } else {
            this.displayEditDialog();
        }
    }, /* end iframeDOMLoaded */
    
    loadEditorPanel: function(addESName) {
        /* loads the 'center' panel, where the part edit form is
            displayed.  This method is used both when the panel is
            in edit and add mode.  When in edit mode,  the external source 
            name is retrieved from the clickContext.  When in add mode,
            pass in the external source name as the `addESName` parameter
        */
        var partModule,
             slotModule,
             partType = this.cfg.getProperty('partType'),
             mode = this.cfg.getProperty("displayMode"),
             isAddMode = mode == "add",
             params = "parttype="+partType+"&mode="+mode;
        
        if (this.clickContextIsPartModule()) {
            partModule = this.clickContext;
            /* not all parts exist in slots, so if it is present in 
                this.app.parts_outside_slots, do not assign slotModule */
            if (!this.app.parts_outside_slots[partModule.element.id]) {
                slotModule = this.app.parts[partModule.element.id][1]
            }
        } else {
            slotModule = this.clickContext;
        }

        if (slotModule) { 
            /* this will be null if the partModule is the page title */
            params += "&slotname="+slotModule.element.id;
        }

        if (isAddMode) {
            params += "&esname="+addESName;
        } else { /* we're in edit mode */
            if (!this.app.parts_outside_slots[partModule.element.id]) {
                var partComponents = this.app._getPartInfoFromID(partModule.element.id);
                params += '&esname='+partComponents[0]+"&partkey="+partComponents[1];
            } else { 
                /* partModule is neither an ES, nor has a partkey.  The backend will
                    use the parttype to determine the proper presentation for the
                    editor */
            }
        }
        var url = objurl + "/editdialogiframe";
        this.editorIFrame.location.href = url + '?' + params;
    },

    displayEditDialog: function() {
        /* called after the edit dialog iframe has finished loading */

        /* hide the page, so no artifacts are displayed before it is
            ready */
        Dom.setStyle(this.editorIFrame.document.body, 'visibility', 'hidden');
        
        /* change the title of the panel.  The header is returned from the
            AJAX request, is inserted into the body as pat of the responseText, and
            then moved to the header */
        var header = Selector.query('.header-title', this.editorIFrame.document, true);
        if (header) {
            /* chrome requires that importNode be used, which creates a new node in
               the specified document.  when just setHeader is used (which ultimately
               calls appendNode, opera and firefox will update the node's ownerDocument,
               perhaps using importNode internally, and remove the node from the other
               document.  But this isn't universally supported */
            if (this.body.ownerDocument.importNode) {
                var newHeader = this.body.ownerDocument.importNode(header, true);
                header.parentNode.removeChild(header);
                header = newHeader;
            }
            /* Hack for IE... here's an interesting article:
               http://www.alistapart.com/articles/crossbrowserscripting/ */
            if (YAHOO.env.ua.ie) {
                var newHeader = parent.document.createElement("div");
                newHeader.innerHTML = header.outerHTML;
                header.parentNode.removeChild(header);
                header = newHeader.firstChild;
            }
            this.setHeader(header);
        }
        
        PartEditorPanel.superclass.displayEditDialog.call(this);
     },

    submit: function() {
        /* user attempting to submit form.
            first gather form elements and validate
            then add the part via ajax
            then add the part to the DOM */
        this.cleanupTinyMCE();
        var postData = getData(this.editorIFrame.document);
        if (!postData.parttype) {
            alert("you must first select an item to add");
            return;
        }
        var post = [];
        for (var name in postData) {
            var value = postData[name];
            if (!(value instanceof Array)) {
                value = [value];
            }
            for (var i=0, len=value.length; i < len; i++) {
                post.push(encodeURIComponent(name) + '=' + encodeURIComponent(value[i]));
            }
        }
        post = post.join("&");
        this.validateAndContinue(post, this.finalizeSubmit);
    },

    validateAndContinue: function(post, callAfterNextUrl) {
        var dialogCallback = { 
            success: function(resp) { 
                /* call the `continue` function, ensuring that the
                    `this` property of that function is the editor panel */
                var oForm = Selector.query('form', this.editorIFrame.document, true),
                    url = oForm.action;
                /* if the panel is in 'add' mode, determine the click context
                    if the context is a partModule, send it as 'beforepartkey'
                    */
                if (this.cfg.getProperty("displayMode")=='add' && 
                    this.clickContextIsPartModule()) {
                        var partComponents = this.app._getPartInfoFromID(this.clickContext.element.id);
                        post += "&beforepartkey="+partComponents[1];
                }
                Connect.asyncRequest('POST',
                    url,
                    {success: function(resp) {
                        /* call the continue function, ensuring that `this`
                            is correct.  This eliminates the need to pass context
                            in via a `contextVars` dictionary */
                        callAfterNextUrl.call(this, resp);
                    }, failure: function(resp) {
                        alert('failure in post validate: \n' + resp.responseText); 
                    }, argument: {callAfterNextUrl: callAfterNextUrl},
                    scope: this
                    },
                    post
                );
            },
            failure: function(resp) {
                if (resp.status == 400) {
                    alert('failure in validate: \n' + resp.responseText.replace(/&/g, "\n").replace(/=/g, ": ")); 
                }
                else {
                    alert('an internal error occured');
                }
            },
            argument: {callAfterNextUrl: callAfterNextUrl,
                post: post},
            scope: this
        };
        var url = objurl + "/validateeditdialog";
        Connect.asyncRequest('POST', 
            url, 
            dialogCallback, 
            post
        );
    },

    finalizeSubmit: function(resp) {
        /* after the ES form has been validated (via AJAX) and then
            the form has been submitted (via AJAX to form.action),
            the responseText is added into the page */
        var div = this.app.innerdoc.createElement('div');
        div.innerHTML = resp.responseText;

        var partModule, slotModule;
        if (this.clickContextIsPartModule()) {
            partModule = this.clickContext;
            /* part exists outside a slot, do not assign slotModule */
            if (!this.app.parts_outside_slots[partModule.element.id]) {
                slotModule = this.app.parts[partModule.element.id][1]
            }
        } else {
            slotModule = this.clickContext;
        }
        if (this.cfg.getProperty('displayMode')=='add') { 
            /* currently the only parttype where adds are allowed are ES parts.
                The format of the response is the complete html for the new part.*/
            var partDOM = Selector.query('div.part', div, true);
            if (!partModule) { /* add to end of slot */
                slotModule.appendToBody(partDOM);
            } else { /* add above the partModule */
                var parent = partModule.element.parentNode;
                parent.insertBefore(partDOM, partModule.element);
            }
            /* make sure to create an add button with this partmodule */
            this.app.createPartModule(partDOM, slotModule, true);
        } else {
            /* editing -- replace the part's body with the response */
            /* this can be any type of part (es, page-title), the format of the 
                response is the same */
            var partContent = Selector.query('div.part-content', partModule.body, true);
            while (partContent.hasChildNodes()) {
                partContent.removeChild(partContent.firstChild);
            }
            partContent.appendChild(div);
        }
        this.hide();
    },

    setClickContext: function(slotOrPart) {
        /* records what triggered the display of the editor panel.
            this should either be a slot or part module */
        this.clickContext = slotOrPart;
    },

    clickContextIsPartModule: function() {
        /* returns true if the click which triggered the display of this
            panel was inside a part (otherwise it was in a slot) */
        return Dom.hasClass(this.clickContext.element, 'part');
    },
    
    setCheckedAddablesMenuItem: function(newitem) {
        /* set the 'checked' property of the menu item with the same
           name (the id of the code source) as ``newitem``.
           If ``newitem`` is null, this effectively removes the currently
           checked menu item.
        */
        var items = this.addMenu.getItems();
        for (var i=0, len=items.length; i < len; i++) {
            var item = items[i];
            if (newitem) {
                var value = item.element.getElementsByTagName("a")[0].getAttribute("value");
                if (value == newitem) {
                    item.cfg.setProperty("checked", true);
                } else if (item.cfg.getProperty("checked")) {
                    item.cfg.setProperty("checked", false);
                }
            } else {
                if (item.cfg.getProperty("checked")) {
                    item.cfg.setProperty("checked", false);
                }
            }
        }
    },

    loadAddablesScreen: function() {
        /* The "Addables Screen" is a nicer rendering of the "common" addables, 
            placed in the editorIFrame.  The entire region for each common 
            addable is clickable */
        if (this.editorIFrame.location.href != url) { /* don't reload */
            var url = objurl + "/addablesscreen";
            this.editorIFrame.location.href = url;
        }
    },

    collapseLeftPanelAddablesMenu: function() {
        /* collapse all submenu groups which are currently expanded */
        /* only set up menu if in add mode */
        if (this.cfg.getProperty("displayMode") != "add") {
            return;
        }
        var groups = this.addMenu.getItemGroups();
        /* skip over the first two groups.  the first group is just
            "overview", the second group is "common" */
        for (var i=1; i < groups.length; i++) {
            var group = groups[i];
            var ul = group[0].element.parentNode;
            if (!Dom.hasClass(ul, 'collapsed')) {
                /* the previous sibling of the ul is the h6/group title */
                var h6 = Dom.getPreviousSibling(ul);
                Dom.addClass(h6, 'collapsed');
                Dom.addClass(ul, 'collapsed');
            }
        }
    },

    setupLeftPanelAddablesMenu: function() {
        /* only set up menu if in add mode */
        if (this.cfg.getProperty("displayMode") != "add") {
            return;
        }
        var leftUnit = this.layout.getUnitByPosition('left'),
            menu = this.cfg.getProperty('addMenu');
        this.addMenu = new Menu(menu,
            {visible: false,
            position: 'static',
            maxheight: 200}
        );
        this.addMenu.render(leftUnit.body);
        this.addMenu.hide();           
        this.addMenu.subscribe("click", function( p_sType, p_aArgs, contextItems) {
            var oEvent = p_aArgs[0],
                oMenuItem = p_aArgs[1],
                editorPanel = contextItems[0],
                app = editorPanel.app;
                /* only load the editorPanel for the clicked menuitem if that
                menu item is not already selected (and the editor panel loaded) */   
            if (oMenuItem && !oMenuItem.cfg.getProperty("checked")) {
                editorPanel.setCheckedAddablesMenuItem();
                var value = oMenuItem.element.getElementsByTagName("a")[0].getAttribute("value");
                if (value == "common") {
                    /* item clicked was the "common", to (re)display the addables
                        screen */
                    editorPanel.setHeader('Add to Page');
                    setCheckedAddablesMenuItem(null);
                }else{
                    /* item clicked was an external source */
                    oMenuItem.cfg.setProperty("checked", true);
                    /* remove any tinymce instances */
                    editorPanel.cleanupTinyMCE(true);
                    editorPanel.loadEditorPanel(value);
                }
            }
            var target = oEvent.target ? oEvent.target : oEvent.srcElement;
            if(target.tagName.toUpperCase() == 'H6') {
                /* the more items... title was clicked.  Expand the item 
                    if necessary */
                  
                    if (Dom.hasClass(target, 'moreItemsTitle')){                        
                        var group = this.getItemGroups()[1];
                        var ul = group[0].element.parentNode;
                        if (Dom.hasClass(target, 'collapsed')) {
                            Dom.removeClass(target, 'collapsed');
                            Dom.removeClass(ul, 'collapsed');
                        }else{
                            Dom.addClass(target, 'collapsed');
                            Dom.addClass(ul, 'collapsed');
                        }              
                    }
                    else if (Dom.hasClass(target, 'commonTitle')){ 
                         editorPanel.addMenu.cfg.setProperty('visible', true);
                        /* reset the header */
                         editorPanel.setHeader('Add to Page');
                        /* now load a "nice" view of the "common" addables in the
                         main panel */
                         editorPanel.loadAddablesScreen();
                         editorPanel.setCheckedAddablesMenuItem();
                    }   
                }
        }, [this] );
    } /* end setupLeftPanelAddablesMenu */

    });

}()); /* end YAHOO.bethel.contentlayout.PartEditor */

(function() { /* YAHOO.bethel.contentlayout.PartModule */

    YAHOO.bethel.contentlayout.PartModule = function(el, userConfig, app) {
        this.app = app;
        YAHOO.bethel.contentlayout.InfoPanel.superclass.constructor.call(this, el, userConfig);
    }

    var Lang = YAHOO.lang,
        Module = YAHOO.widget.Module,
        Dom = YAHOO.util.Dom,
        Event = YAHOO.util.Event,
        Region = YAHOO.util.Region,
        Point = YAHOO.util.Point,
        PartModule = YAHOO.bethel.contentlayout.PartModule,

    /**
    * Constant representing the Overlay's configuration properties
    */
    DEFAULT_CONFIG = {
        /* flag indicating whether to display the edit control */
        "EDIT": {
            key: "edit",
            validator: YAHOO.lang.isBoolean,
            value: true
        },
        /* the function to call when the edit control is clicked.  
            This is executed within the context of the content layout app,
            and has the signature: function(p_oEvent, context) where context
            is a one-item array containing this part module, e.g. [this] */
        "EDITCLICK": {
            key: "editClick"
        },
        /* flag indicating whether this part is movable.
            parts that are fixed on the page (e.g. the page title) 
            are not movable */
        "MOVABLE": {
            key: "movable",
            validator: YAHOO.lang.isBoolean,
            value: true
        },
        /* flag indicating whether to display the remove control
            parts that are fixed on the page (e.g. the page title) will not
            display this control */
        "REMOVE": {
            key: "remove",
            validator: YAHOO.lang.isBoolean,
            value: true
        },
        /* the function to call when the remove control is clicked.  
            This is executed within the context of the content layout app,
            and has the signature: function(p_oEvent, context) where context
            is a one-item array containing this part module, e.g. [this] */
        "REMOVECLICK": {
            key: "removeClick"
        },
        /* the text to add after the title of each control.  By default each
            control's html "title" attribute is the name of control, e.g. edit.
            Setting titlePostfix=" page title" will cause all controls to have
            a title of "[control name] page title", e.g. edit page title */
        "TITLEPOSTFIX": {
            key: "titlePostfix",
            validator: YAHOO.lang.isString,
            value: ""
        }
    };

    YAHOO.lang.extend(PartModule, Module, {

    init: function(el, userConfig) {
        /*
            Note that we don't pass the user config in here yet because we
            only want it executed once, at the lowest subclass level
        */
        YAHOO.bethel.contentlayout.PartModule.superclass.init.call(this, el/*, userConfig*/);
        if (userConfig) {
            this.cfg.applyConfig(userConfig, true);
        }

        /* dynamically create the control panel DOM */
        var ownerDoc = this.element.ownerDocument;
        var od = ownerDoc.createElement("div");
        od.id = this.element.id + "controls";
        od.className =  "part-controls";
        var hd = ownerDoc.createElement("div");
        hd.id = od.id + "hd";
        hd.className = "hd";
        od.appendChild(hd);
        var bd = ownerDoc.createElement("div");
        bd.id = od.id + "bd";
        bd.className = "bd";
        od.appendChild(bd);
        var fd = ownerDoc.createElement("div");
        fd.id = od.id + "ft";
        fd.className = "ft";
        od.appendChild(fd);
        /* add the controlpanel as the first child of the part's header */
        this.header.insertBefore(od, this.header.firstChild);
    
        this.partControlOverlay = new YAHOO.widget.Overlay(od, {visible: false});
    
        var postfix = this.cfg.getProperty("titlePostfix");
        if (postfix) {
            postfix = " " + postfix;
        }
    
        if (this.cfg.getProperty("edit")) {
            // add "edit" control
            var edit = ownerDoc.createElement("span");
            edit.title = "edit" + postfix;
            edit.appendChild(ownerDoc.createTextNode("edit"));
            edit.className="control manipulator";
            edit.id = od.id + "edit";
            this.partControlOverlay.body.appendChild(edit);
            /* XXX should this action be defined in the app, or in PartModule,
                with PartModule calling back to the app for cleanup duties */
            Event.addListener(edit, "click",
                this.cfg.getProperty("editClick"),
                [this],
                this.app);
            Event.addListener(edit, "click",
                function() { this.partControlOverlay.hide(); this.app.disable_part_overlays = true; },
                null,
                this);
        }
    
        if (this.cfg.getProperty("movable")) {
            this.app.editorframe.InnerLayoutApp.createDDPart(
                this.app,
                this.element,
                this.app.slotDDGroup
            );
        }
    
        if (this.cfg.getProperty("remove")) {
            // add "remove" control
            var remove = ownerDoc.createElement("span");
            remove.title = "remove" + postfix;
            remove.appendChild(ownerDoc.createTextNode("delete"));
            remove.className="control remover";
            remove.id = od.id + "remove";
            this.partControlOverlay.body.appendChild(remove);
            /* XXX should this action be defined in the app, or in PartModule,
                with PartModule calling back to the app for cleanup duties */
            Event.addListener(remove, "click",
                this.cfg.getProperty("removeClick"),
                [this],
                this.app);
            Event.addListener(remove, "click",
                function() { this.partControlOverlay.hide(); this.app.disable_part_overlays = true; },
                null,
                this);
        }
    
        this.partControlOverlay.cfg.setProperty("context", 
            [this.element, "tr", "tr", ["windowResize"] ]);
        this.partControlOverlay.render();
    
    
        Event.addListener(this.element, "mouseover",
            function(event, context) {
                if (!this.app.disable_part_overlays) {
                    /* ensure the placement of the overlay is always in the correct
                        location whenever it is displayed.  Relying on the application
                        to update the locations whenever it thinks they have changed
                        appears to be buggy and possibly dependent on the state of the
                        screen redraw when the sync happens (resulting in a misplaced
                        overlay */
                    this.syncPartControlOverlay();
                    this.partControlOverlay.show();
                }
            }, null, this);
        Event.addListener(this.element, "mouseout",
            function(event, context) {
                this.partControlOverlay.hide();
            }, null, this);
    },

    initDefaultConfig: function() {
        PartModule.superclass.initDefaultConfig.call(this);
        /* add the default configuration properties for PartModules */
        var cfg = this.cfg;
        cfg.addProperty(DEFAULT_CONFIG.EDIT.key, {
            handler: function (type, args, obj) {
                this.cfg.setProperty("edit", args[0], true);
            },
            validator: DEFAULT_CONFIG.EDIT.validator,
            value: DEFAULT_CONFIG.EDIT.value
        });
        cfg.addProperty(DEFAULT_CONFIG.EDITCLICK.key, {
            handler: function (type, args, obj) {
                this.cfg.setProperty("editClick", args[0], true);
            }
        });
        cfg.addProperty(DEFAULT_CONFIG.REMOVECLICK.key, {
            handler: function (type, args, obj) {
                this.cfg.setProperty("removeClick", args[0], true);
            }
        });
        cfg.addProperty(DEFAULT_CONFIG.MOVABLE.key, {
            handler: function (type, args, obj) {
                this.cfg.setProperty("movable", args[0], true);
            },
            validator: DEFAULT_CONFIG.MOVABLE.validator,
            value: DEFAULT_CONFIG.MOVABLE.value
        });
        cfg.addProperty(DEFAULT_CONFIG.REMOVE.key, {
            handler: function (type, args, obj) {
                this.cfg.setProperty("remove", args[0], true);
            },
            validator: DEFAULT_CONFIG.REMOVE.validator,
            value: DEFAULT_CONFIG.REMOVE.value
        });
        cfg.addProperty(DEFAULT_CONFIG.TITLEPOSTFIX.key, {
            handler: function (type, args, obj) {
                this.cfg.setProperty("titlePostfix", args[0], true);
            },
            validator: DEFAULT_CONFIG.TITLEPOSTFIX.validator,
            value: DEFAULT_CONFIG.TITLEPOSTFIX.value
        });
    },

    syncPartControlOverlay: function() {
        //to be used when the part has moved in the slots.  This will readjust
        // the position of the overlayCommon to the current top left corner of the
        // part.  Note that the moveTo method moves the top left corner of the
        // overlay to the specified coords
        var region = Dom.getRegion(this.element);
        var overlayRegion = Dom.getRegion(this.partControlOverlay.element);
        this.partControlOverlay.moveTo(region.right-overlayRegion.width,region.top);
    }

    });

}());/* end YAHOO.bethel.contentlayout.PartModule */

(function() { /* YAHOO.bethel.contentlayout.app */
    var Dom = YAHOO.util.Dom,
        Event = YAHOO.util.Event,
        Selector = YAHOO.util.Selector,
        Connect = YAHOO.util.Connect,
        Cookie = YAHOO.util.Cookie,
        Module = YAHOO.widget.Module,
        Dialog = YAHOO.widget.Dialog,
        SimpleDialog = YAHOO.widget.SimpleDialog,
        InfoPanel = YAHOO.bethel.contentlayout.InfoPanel,
        PartMoveTool = YAHOO.bethel.contentlayout.PartMoveTool,
        PartModule = YAHOO.bethel.contentlayout.PartModule,
        PartEditorPanel = YAHOO.bethel.contentlayout.PartEditorPanel;        

    YAHOO.bethel.contentlayout.app = function() {
        /* editorframe is a window object, not an HTMLElement (iframe) */
        this.editorframe = top.frames['editor-frame'];
        if (!this.editorframe) {
            /* the editor isn't present on this page, so stop loading it.
                this can happen if contentlayout is used for versionedcontent
                and there is no published version. */
            return;
        }

        /* this is the DOM HTMLElement/IFrame version of the editor iframe */
        this.iframe = Selector.query('#editor-frame', document, true);
    
        /* this is the layout container */
        this.layout = new Module("content-layout-template");
        this.layout.render();
    
        /* set to true to disable part overlays (e.g. the
            edit/move/remove/add controls.
            They should be disabled if a part is being moved
            via drag/drop, if the edit panel is visible */
        this.disable_part_overlays = false;
    
        this.partEditorPanel = new PartEditorPanel("part-editor-panel",
            {fixedcenter: "contained",
                draggable: false,
                width: '600px',
                height: '560px',
                modal: true,
                hideaftersubmit: true,
                constraintoviewport: true,
                visible: false,
                displayMode: "edit"
                },
                this
        );
        this.partEditorPanel.render();
    
        /* add panel is wider than edit panel, to accommodate for the
            add menu */
       
        this.partAddPanel = new PartEditorPanel("part-add-panel",
            {fixedcenter: "contained",
                draggable: false,
                width: '750px',
                height: '560px',
                modal: true,
                hideaftersubmit: true,
                constraintoviewport: true,
                visible: false,
                displayMode: "add",
                submitlabel: "Add",
                defaultTitle: "Add to Page",
                addMenu: Selector.query('#add-part-menu', document, true)
                },
                this
        );
        this.partAddPanel.render();
        
        /* this maybe should be run as soon as the content is ready.  
            which may improve screen flicker.  Currently it is
            run as soon as the DOM is loaded */
        this.infopanel = new InfoPanel("infopanel",{closable:true},this);
        this.infopanel.registerTool("movetool", new PartMoveTool("infopanel-movetool"));
    
        /* make sure the iframe height is within the bounds of the viewport
            also add a window resize listener to keep the height in sync */
        this.updateIFrameHeight();
        Event.addListener(window, "resize", 
            function() { this.updateIFrameHeight() },
            null, this);
    
        /* create the partRemove confirmation simple dialog */
        this.partRemoveConfirm = new SimpleDialog("confirm-part-delete", 
            {width: "20em",
                fixedcenter: true,
                draggable: false,
                modal: true,
                visible: true}
        );
        this.preparePartRemoveDialog();
    
        /* data structure containing references to the slot module (and the parts
            in that module, by the slot's id */
        this.slots = {};
        /* dictionary of partkey: [partModule, slotModule] */
        this.parts = {};
        /* dictionary for special parts located outside of slots, like
            the page title part */
        this.parts_outside_slots = {};
    
        /* the drag drop group for the part moving interations */
        this.slotDDGroup = "slot-dragdrop";
    };

    var ContentLayoutApp = YAHOO.bethel.contentlayout.app;

    ContentLayoutApp.prototype.changeViewMode = function(newmode) {
        if (this._view_mode != newmode) {
            if (newmode == 'preview') {
                // first only remove the layouteditor layer, rather than replacing with
                // the preview, in case it isn't the last path component
                var path = this.editorframe.location.pathname.replace(/\+\+layouteditor\+\+/,'');
                //if path ends in a slash, remove it
                path = path.replace(/\/$/, '');
                // add ++preview++ after a publication (it's only on publications,
                // buh.  Assume the first path component is a publication
                // (this is fragile, it's still possible to break it, but
                // the best we can do at this point)
                path = path.replace(/^(\/[^\/]*?\/)/, '$1++preview++/')
                this.editorframe.location.pathname = path;
                // clean out the contentlayout datastructures
                this.parts = {};
                this.slots = {};
                this.parts_outside_slots = {};
                this.editorframe.InnerLayoutApp.lockDD();
            } else if (newmode == 'edit') {
                if (this._view_mode == 'preview') {
                    // first only remove the layouteditor layer, rather than replacing with
                    // the preview, in case it isn't the last path component
                    var newurl = this.editorframe.location.href.replace(/preview_html/,'');
                    if (newurl.search(/\/$/)==-1) {
                        newurl += '/';
                    }
                    newurl += '/++layouteditor++/';
                    /* when the editorframe loads again, it should know to call
                        _editorFrameLoaded */
                    this.editorframe.location.href = newurl;

                    if (this.editorframe.InnerLayoutApp)
                        this.editorframe.InnerLayoutApp.lockDD();
                } else if (this._view_mode == 'move') {
                    /* disable move mode, return to edit mode */
                    Dom.addClass(this.innerskin, 'editmode');
                    Dom.removeClass(this.innerskin, 'movemode');
                    this.editorframe.InnerLayoutApp.lockDD();
                }
            } else if (this._view_mode != 'preview' && newmode == 'move') {
                /* move mode is only available when in "edit" mode */
                Dom.removeClass(this.innerskin, 'editmode');
                Dom.addClass(this.innerskin, 'movemode');
                this.editorframe.InnerLayoutApp.unlockDD();
            }
            
            this._view_mode = newmode;
        }
    };

    ContentLayoutApp.prototype._editorFrameLoaded = function(partID) {
        /*  This code needs to be run once the editor iframe has finished loading,
            since it requires the editor iframe's DOM to be fully loaded.

        onload events for iframe (windows) do not seem to work on opera (and possibly others)
        so instead, within the iframe window (which is loaded with the ++layouteditor++
        layer), this method should be called using onDOMReady.  The onDOMReady needs
        to be called within the iframe's window, so that YUI will inspect the
        iframe window for readyness.  There is no way within YUI2 to cause onDOMReady
        to look at a different window. */
        /* set up each slot in the template */
        this.innerdoc = this.editorframe.document;

        this.editorframe.InnerLayoutApp.lockDD();

        this.innerskin = Selector.query('.yui-skin-sam', this.innerdoc.body, true);
        Dom.addClass(this.innerskin, 'editmode');

        var pageTitlePart = Selector.query('#page-title-widget', this.innerdoc.body, true);
        if (pageTitlePart) { /* not all templates display a page title */
            this.createPageTitleModule(pageTitlePart);
        }
    
        var slotsDivs = Selector.query('.slot', this.innerdoc);
        for (var i=slotsDivs.length; i--;) {
            var slot = slotsDivs[i];
            var slotModule = new Module(slot);
            slotModule.render();
    
            this.slots[slot.id] = [slotModule, {}];
            this.editorframe.InnerLayoutApp.createDDTarget(slot, this.slotDDGroup);
            this.placeAddPartButton(slotModule, false);
        
            /* initialize each part in the slot */
            var partDivs = Selector.query('.part', slot);
            for (var j=partDivs.length; j--;) {
                var pm = this.createPartModule(partDivs[j], slotModule, true);
        
            }
        } // end slot loop

        var As = this.innerdoc.getElementsByTagName("a"),
            emptyFunc = function() { return false; };
        for (var i = As.length; i--;) {
            As[i].onclick = emptyFunc;
        }
    }

    ContentLayoutApp.prototype.placeAddPartButton = function(module, isPart) {
        var od = module.element.ownerDocument;
        var div = od.createElement('div');
        div.className = "add-container";
        var innerDiv = od.createElement('div');
        innerDiv.className = "add-button manipulator";
        //innerDiv.appendChild(od.createTextNode('add'));
        innerDiv.appendChild(od.createTextNode(''));
        innerDiv.setAttribute('title','add');
        div.appendChild(innerDiv);

        if (isPart) { 
            /* place it after the part */
            var el = module.element;
            el.parentNode.insertBefore(div, el.nextSibling);
        } else { //dom is a slot
            module.body.insertBefore(div, module.body.firstChild);
        }
    
        Event.addListener(div, 'click',
            function(event, app) {
                /* find the part immediately after this button */
                var part = Dom.getNextSibling(this);
                while (part && !Dom.hasClass(part, 'part')) {
                    part = Dom.getNextSibling(part);
                }
                var mod;
                if (!part) { /* last add button in the slot, add to bottom of slot */
                    mod = app.slots[this.parentNode.parentNode.id][0]
                } else {
                    mod = app.parts[part.id][0];
                }
                app.clickAddButton(null, [mod])
            },
            this
        );
    }

    ContentLayoutApp.prototype.updateIFrameHeight = function() {
        var ifheight = this.iframe.height,
            vpheight = Dom.getViewportHeight();
        var heightAboveIFrame = 100;
        //vpheight > ifheight - heightAboveIFrame -- grow
        //vpheight < ifheight - heightaboveiframe -- shrink
        /*do a resize, but make sure the height if the iframe doesn't
            shrink too small.  Don't re-set the height if unchanged */
        var newheight = vpheight - heightAboveIFrame;
        if (newheight < 480) {
            newheight = 480;
        }
        if (newheight != ifheight) {
            this.iframe.height = newheight;
            this.infopanel.element.style.height = this.iframe.height + 'px';
        }
        /* XXX need to adjust for scrollbars here, and 
            in infopanel.updateIFrameWidth */
    }

    ContentLayoutApp.prototype._getPartInfoFromID = function(partID) {
        /* the part id encodes the part name (es zope id) and the part key */
        var partComponents = partID.match(/([^.]*)\_([^_]*)$/);
        var partName = partComponents[1];
        var partKey = partComponents[2];
        return [partName,partKey]
    }

    ContentLayoutApp.prototype.createPageTitleModule  = function(titleDOM) {
        var pageTitleModule = new PartModule(
            titleDOM, 
            {edit: true,
                editClick: this.clickTitleEditButton,
                movable: false, 
                remove: false, 
                titlePostfix: "page title"},
            this);
        this.parts_outside_slots[pageTitleModule.element.id] = pageTitleModule;
    }
    
    ContentLayoutApp.prototype.createPartModule = function(partDOM, slotModule, placeAdd) {
        var partModule = new PartModule(
            partDOM, 
            {titlePostfix: "part", 
                editClick: this.clickPartEditButton, 
                removeClick: this.clickPartRemoveButton
            }, this);
        partModule.render();

        this.slots[slotModule.element.id][1][partModule.element.id] = partModule;
        this.parts[partModule.element.id] = [partModule, slotModule];
        if (placeAdd) {
            this.placeAddPartButton(partModule, true);
        }
        return partModule;
    }

    ContentLayoutApp.prototype.clickAddButton = function(p_oEvent, context) {
        /* context is an array whose first value is either the
            partModule immeditable below the add button
                -- adding a part above that module
                or the slot module 
                -- adding a part at the bottom of the module
        */
        this.partAddPanel.setClickContext(context[0]);
        this.partAddPanel.show();
    }
    
    ContentLayoutApp.prototype.clickTitleEditButton = function(p_oEvent,context) {
        /* launch the edit dialog for editing the page title part */
        this.partEditorPanel.setClickContext(context[0]);
        this.partEditorPanel.cfg.setProperty('partType', 'page-title');
        this.partEditorPanel.show();
    }

    ContentLayoutApp.prototype.clickPartEditButton = function(p_oEvent,context) {
        /* launch the PartEditorPanel for editing the part */
        /* set the click context to be partModule where the 'edit' click occurred */
        this.partEditorPanel.setClickContext(context[0]);
        this.partEditorPanel.cfg.setProperty('partType', 'es');
        this.partEditorPanel.show();
    }

    ContentLayoutApp.prototype.clickPartRemoveButton = function(p_oEvent,context) {
        /* handler called when the 'remove' button in a part is clicked.  This displays
            a confirmation dialog.  The callback is set up so contextual objects are 
            accessible within the dialog's event handlers.  The UI docs suggest the
            callback is to be used when handling AJAX responses, but it works here
            to pass objects through to the handlers as well. */
        var partModule = context[0];
        this.partRemoveConfirm.callback = {
            partModule: partModule,
            app: this
        };
        this.partRemoveConfirm.render();
        this.partRemoveConfirm.show();
    }

    ContentLayoutApp.prototype.getAnchorsInParts = function() {
        /* returns an array of all anchors in all parts in the layout.
            Used by TinyMCE's SilvaLink plugin to populate the "anchors"
            property with the complete list of anchors, not just the ones
            in the current tinymce instance */
            var nodes = YAHOO.util.Selector.query('div.part a[name]', this.editorframe.document);
            return nodes;
    }

    ContentLayoutApp.prototype.preparePartRemoveDialog = function() {
        /* configure the part remove dialog.  This is a SimpleDialog that prompts
            to confirm removal of a part.  If confirmed, an AJAX call is issued
            which removes the part in Silva, and then the callback from the AJAX
            call removes the part from the DOM */

        /* add a configevent handler for buttons, so that they can be given the
            appropriate CSS classes.  The buttons aren't actually generated (and
            added to the DOM) until the dialog is opened for the first time.  
        */
        this.partRemoveConfirm.cfg.subscribeToConfigEvent('buttons',
            function(key, value) {
                /* key should be "buttons", value is the list of buttons
                    i.e. the value of the config property "buttons".
                    `this` refers to the SimpleDialog instance */
                var buttons = value[0];
                var del = Selector.query('button', buttons[0]['htmlButton'], true);
                var cancel = Selector.query('button', buttons[1]['htmlButton'], true);
                Dom.addClass(del, 'remover');
                Dom.addClass(cancel, 'canceler');
            });
        var handleYes = function() {
            var partModule = this.callback['partModule'],
            app = this.callback['app'];
            var url = objurl + "/removepart";
            var params = "partkey="+app._getPartInfoFromID(partModule.element.id)[1];
            var trans = Connect.asyncRequest('POST', url,
                { success: function(resp) {
                    var el = partModule.element;
                    /* remove add button and partmodule */
                    var ps = Dom.getPreviousSibling(el);
                    el.parentNode.removeChild(ps);
                    el.parentNode.removeChild(el);
                    var slotModule = app.parts[partModule.element.id][1];
                    delete app.parts[partModule.element.id];
                    delete app.slots[slotModule.element.id][1][partModule.element.id];
                }, 
                failure: function(resp) { alert('failure handling removal response'); }
                }, params
            );
            this.hide();
        }, /* end handleYes */
           handleNo = function() { this.hide(); },
           myButtons = [ { text:"Delete", handler: handleYes},
            { text:"Cancel", handler:handleNo, isDefault: true }
        ];
        this.partRemoveConfirm.setHeader("Confirm Removal");
        this.partRemoveConfirm.setBody("Are you sure you want to delete this? This action cannot be undone.");
        this.partRemoveConfirm.cfg.queueProperty("buttons", myButtons);
        this.partRemoveConfirm.beforeHideEvent.subscribe(function() {
            /* re-enable part control overlays, do this before the dialog is
                actually hidden, so the overlays are available immediately. */
            this.disable_part_overlays = false;
        }, this, true);
    }

}()); /* end YAHOO.bethel.contentlayout.app */

(function() { /* YAHOO.bethel.contentlayout.InnerLayoutApp */
    YAHOO.bethel.contentlayout.InnerLayoutApp = function() {
        /* this is an object which contains helper functions to get certain features
            of the content layout editor to actually work when the layout is rendered
            within an iframe.  Some components (like the popup menus for the add buttons)
            will not work if they are generated from the iframe parent window, since
            that window's YUI uses the iframe parent as "document".  When created in
            the iframe's window, YUI uses the iframe document, which is the correct
            document. */
    }

    var DDPart = YAHOO.bethel.contentlayout.DDPart,
        ILA = YAHOO.bethel.contentlayout.InnerLayoutApp,
        DDTarget = YAHOO.util.DDTarget,
        Dom = YAHOO.util.Dom,
        DDM = YAHOO.util.DragDropMgr,
        Selector = YAHOO.util.Selector,
        Menu = YAHOO.widget.Menu,
        Button = YAHOO.widget.Button,
        Connect = YAHOO.util.Connect;

    ILA.prototype.lockDD = function() {
        if (!DDM.isLocked()) {
            DDM.lock();
        }
    }
        
    ILA.prototype.unlockDD = function() {
        if (DDM.isLocked()) {
            DDM.unlock();
        }
    }

    ILA.prototype.createDDPart = function(app, part, groupname, config, handleElId) {
        /* we're not currently using handle elements, but they're here in case */
        new DDPart(part, groupname, app, config, handleElId);
    }
    
    ILA.prototype.createDDTarget = function(slot, groupname) {
        new DDTarget(slot, groupname);
    }
}()); /* end YAHOO.bethel.contentlayout.InnerLayoutApp */
