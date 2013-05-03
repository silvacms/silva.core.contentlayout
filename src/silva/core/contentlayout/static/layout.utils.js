
(function($, infrae, jsontemplate) {

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

    var Transport = function(smi, urls, path) {
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
                }).then(
                    function(data) {
                        if (data.extra !== undefined) {
                            return data.extra;
                        };
                        return data;
                    }
                );
            },
            addable: function(state) {
                var slot_cache = validation_add[state.slot.id],
                    block_cache = undefined,
                    response = {
                        slot: state.slot,
                        block: state.block,
                        name: state.name,
                        index: state.index
                    };

                if (!state.slot.editable) {
                    return $.Deferred().resolve(
                        $.extend(response, {
                            failed: true,
                            success: false,
                            fatal: false
                        }));
                };

                if (slot_cache === undefined) {
                    slot_cache = validation_add[state.slot.id] = {};
                };
                block_cache = slot_cache[state.name];
                if (block_cache !== undefined && block_cache.state() == 'resolved') {
                    // Return cached success
                    return block_cache.then(function (data) {
                        return $.extend(response, {
                            success: data.success,
                            failed: data.failed,
                            fatal: false
                        });
                    });
                };
                return slot_cache[state.name] = smi.ajax.query(
                    urls.actions.addable.expand({
                        path: path,
                        slot_id: state.slot.id,
                        block_name: state.name
                    })
                ).then(function(data) {
                    return $.extend(response, {
                        success: data.success,
                        failed: !data.success,
                        fatal: false
                    });
                }, function(fatal) {
                    return $.Deferred().reject(
                        $.extend(response, {
                            failed: true,
                            success: false,
                            fatal: true
                        }));
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
                var block_cache = validation_move[state.current.id],
                    slot_cache = undefined,
                    response = {
                        slot: state.slot,
                        current: state.current,
                        index: state.index
                    };

                if (!state.slot.editable) {
                    return $.Deferred().resolve(
                        $.extend(response, {
                        failed: true,
                        success: false,
                        fatal: true
                        }));
                };
                if (block_cache === undefined) {
                    block_cache = validation_move[state.current.id] = {};
                };
                slot_cache = block_cache[state.slot.id];
                if (slot_cache !== undefined && slot_cache.state() == 'resolved') {
                    // Return cached success
                    return slot_cache.then(function (data) {
                        return $.extend(response, {
                            success: data.success,
                            failed: data.failed,
                            fatal: false
                        });
                    });
                };
                return block_cache[state.slot.id] = smi.ajax.query(
                    urls.actions.movable.expand({
                        path: path,
                        slot_id: state.slot.id,
                        block_id: state.current.id
                    })
                ).then(function(data) {
                    return $.extend(response, {
                        success: data.success,
                        failed: !data.success,
                        fatal: false
                    });
                }, function(request) {
                    return $.Deferred().reject(
                        $.extend(response, {
                        failed: true,
                        success: false,
                        fatal: true
                        }));
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
                ).then(function(data) {
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


    $.extend(infrae.smi.layout, {
        utils: {
            Mouse: Mouse,
            Transport: Transport
        }
    });

})(jQuery, infrae, jsontemplate);
